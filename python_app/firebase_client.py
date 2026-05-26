import os
from datetime import datetime, date
import firebase_config
from firebase_admin import firestore, auth

# Initialize firebase client
firebase_config.get_firebase_app()
db = firestore.client()

# Firestore's modern Python client expects a FieldFilter object for keyword
# filters. Passing a list of tuples raises ValueError on newer releases.
def _where_eq(query, field: str, value):
    return query.where(filter=firestore.FieldFilter(field, "==", value))

# Helper to serialize values for Firestore
def serialize_val(val):
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, dict):
        return {k: serialize_val(v) for k, v in val.items()}
    if isinstance(val, list):
        return [serialize_val(v) for v in val]
    return val

# ----------------------------------------------------
# Audit Log Helper
# ----------------------------------------------------
def write_audit_log(action_type: str, performed_by: str, target_doc: str, old_value, new_value) -> None:
    """Writes a log record of the action performed to Firestore audit_log collection."""
    try:
        log_ref = db.collection("audit_log").document()
        log_ref.set({
            "action_type": action_type,
            "performed_by_uid": "admin",
            "performed_by_name": performed_by,
            "target_document": target_doc,
            "old_value": serialize_val(old_value),
            "new_value": serialize_val(new_value),
            "timestamp": firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        print(f"Error writing audit log: {e}")

# ----------------------------------------------------
# Consumer Functions
# ----------------------------------------------------
def get_consumer(cin_no: str) -> dict | None:
    """Fetches a consumer document by its unique cin_no."""
    doc_ref = db.collection("consumers").document(cin_no)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        data["cin_no"] = doc.id
        return data
    return None

def get_consumer_by_meter_serial(meter_serial_no: str) -> dict | None:
    """Fetches a consumer document by its meter serial number."""
    query = _where_eq(db.collection("consumers"), "meter_serial_no", meter_serial_no).limit(1).get()
    for doc in query:
        data = doc.to_dict()
        data["cin_no"] = doc.id
        return data
    return None

def create_consumer(data: dict, admin_name: str) -> str:
    """Creates a new consumer document. Writes an audit log entry."""
    cin_no = data.get("cin_no")
    if not cin_no:
        raise ValueError("CIN No is required for consumer creation")
    
    # Check if consumer already exists
    if get_consumer(cin_no) is not None:
        raise ValueError(f"Consumer with CIN {cin_no} already exists.")
        
    doc_ref = db.collection("consumers").document(cin_no)
    
    doc_data = {
        "name": data.get("name"),
        "zone": int(data.get("zone", 0)),
        "contact_number": data.get("contact_number"),
        "category": data.get("category"),
        "meter_size": data.get("meter_size"),
        "meter_serial_no": data.get("meter_serial_no"),
        "initial_meter_reading": float(data.get("initial_meter_reading", 0.0)),
        "last_reading": float(data.get("initial_meter_reading", 0.0)),
        "address_longitude": float(data.get("address_longitude", 0.0)) if data.get("address_longitude") is not None else None,
        "address_latitude": float(data.get("address_latitude", 0.0)) if data.get("address_latitude") is not None else None,
        "address_pin_code": int(data.get("address_pin_code", 0)) if data.get("address_pin_code") is not None else None,
        "address_area_location": data.get("address_area_location"),
        "address_landmark": data.get("address_landmark"),
        "aadhaar_phed_no": data.get("aadhaar_phed_no"),
        "apl_bpl": data.get("apl_bpl"),
        "custom_attributes": data.get("custom_attributes", {}),
        "consumer_status": data.get("consumer_status", "Active"),
        "credit_balance": float(data.get("credit_balance", 0.0)),
        "outstanding_balance": float(data.get("outstanding_balance", 0.0)),
        "is_active": data.get("is_active", True),
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP
    }
    
    doc_ref.set(doc_data)
    write_audit_log("CREATE_CONSUMER", admin_name, f"consumers/{cin_no}", None, doc_data)
    return cin_no

def update_consumer(cin_no: str, updates: dict, admin_name: str) -> None:
    """Updates selected fields on a consumer document. Writes an audit log entry."""
    doc_ref = db.collection("consumers").document(cin_no)
    old_doc = doc_ref.get()
    if not old_doc.exists:
        raise FileNotFoundError(f"Consumer {cin_no} not found.")
        
    old_data = old_doc.to_dict()
    updates["updated_at"] = firestore.SERVER_TIMESTAMP
    
    # Cast fields as needed
    if "zone" in updates:
        updates["zone"] = int(updates["zone"])
    if "initial_meter_reading" in updates:
        updates["initial_meter_reading"] = float(updates["initial_meter_reading"])
    if "last_reading" in updates:
        updates["last_reading"] = float(updates["last_reading"])
    if "outstanding_balance" in updates:
        updates["outstanding_balance"] = float(updates["outstanding_balance"])
    if "credit_balance" in updates:
        updates["credit_balance"] = float(updates["credit_balance"])
    if "address_pin_code" in updates and updates["address_pin_code"] is not None:
        updates["address_pin_code"] = int(updates["address_pin_code"])
    if "address_latitude" in updates and updates["address_latitude"] is not None:
        updates["address_latitude"] = float(updates["address_latitude"])
    if "address_longitude" in updates and updates["address_longitude"] is not None:
        updates["address_longitude"] = float(updates["address_longitude"])

    doc_ref.update(updates)
    write_audit_log("UPDATE_CONSUMER", admin_name, f"consumers/{cin_no}", old_data, updates)

def deactivate_consumer(cin_no: str, admin_name: str) -> None:
    """Sets is_active to False and updates status to Inactive on a consumer document."""
    update_consumer(cin_no, {"is_active": False, "consumer_status": "Inactive"}, admin_name)

def reactivate_consumer(cin_no: str, admin_name: str) -> None:
    """Sets is_active to True and updates status to Active on a consumer document."""
    update_consumer(cin_no, {"is_active": True, "consumer_status": "Active"}, admin_name)

def bulk_create_consumers(data_list: list, admin_name: str) -> dict:
    """Creates multiple consumer documents in batches. Returns counts of success and error rows."""
    success_count = 0
    errors = []
    
    for row_idx, data in enumerate(data_list):
        try:
            create_consumer(data, admin_name)
            success_count += 1
        except Exception as e:
            errors.append({"row": row_idx + 2, "error": str(e)}) # Offset by 2 (header row + 1-indexed)
            
    return {"success": success_count, "errors": errors}

def list_consumers(filters: dict = None) -> list:
    """Lists consumers from Firestore with optional filtering by zone, status, or is_active."""
    query = db.collection("consumers")
    
    if filters:
        if "zone" in filters and filters["zone"] is not None:
            query = _where_eq(query, "zone", int(filters["zone"]))
        if "status" in filters and filters["status"] is not None:
            query = _where_eq(query, "consumer_status", filters["status"])
        if "is_active" in filters and filters["is_active"] is not None:
            query = _where_eq(query, "is_active", bool(filters["is_active"]))
            
    docs = query.get()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["cin_no"] = doc.id
        results.append(data)
    return results

# ----------------------------------------------------
# Billing Cycle Functions
# ----------------------------------------------------
def create_billing_cycle(data: dict, admin_name: str) -> str:
    """Initiates a new billing cycle. Generates a unique cycle ID based on zones and dates."""
    # Check that none of the requested zones are already in an open cycle
    zones = [int(z) for z in data.get("zones", [])]
    open_cycles = get_open_cycles()
    active_zones = set()
    for cycle in open_cycles:
        active_zones.update(cycle.get("zones", []))
        
    conflicted_zones = [z for z in zones if z in active_zones]
    if conflicted_zones:
        raise ValueError(f"Zones {conflicted_zones} are already included in open billing cycles.")
        
    cycle_id = f"BC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    doc_ref = db.collection("billing_cycles").document(cycle_id)
    
    # Count consumers per zone
    consumer_count_per_zone = {}
    for zone in zones:
        zone_count = len(list_consumers({"zone": zone, "is_active": True}))
        consumer_count_per_zone[str(zone)] = zone_count
        
    doc_data = {
        "zones": zones,
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "last_payment_date": data.get("last_payment_date"),
        "grace_period_months": int(data.get("grace_period_months", 1)),
        "status": "open",
        "initiated_by": admin_name,
        "initiated_at": firestore.SERVER_TIMESTAMP,
        "closed_at": None,
        "consumer_count_per_zone": consumer_count_per_zone
    }
    
    doc_ref.set(doc_data)
    write_audit_log("CREATE_BILLING_CYCLE", admin_name, f"billing_cycles/{cycle_id}", None, doc_data)
    return cycle_id

def get_billing_cycle(cycle_id: str) -> dict | None:
    """Fetches details of a specific billing cycle."""
    doc_ref = db.collection("billing_cycles").document(cycle_id)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        data["cycle_id"] = doc.id
        return data
    return None

def get_open_cycles() -> list:
    """Fetches all open billing cycles."""
    query = _where_eq(db.collection("billing_cycles"), "status", "open").get()
    results = []
    for doc in query:
        data = doc.to_dict()
        data["cycle_id"] = doc.id
        results.append(data)
    return results

def get_open_cycle_zones() -> list:
    """Retrieves flat list of all zone integers currently in open cycles."""
    zones = []
    for cycle in get_open_cycles():
        zones.extend(cycle.get("zones", []))
    return sorted(list(set(zones)))

def close_billing_cycle(cycle_id: str, admin_name: str) -> None:
    """Closes an active billing cycle. Locks updates and frees zones."""
    doc_ref = db.collection("billing_cycles").document(cycle_id)
    cycle = doc_ref.get()
    if not cycle.exists:
        raise FileNotFoundError(f"Billing cycle {cycle_id} not found.")
    
    old_data = cycle.to_dict()
    if old_data.get("status") == "closed":
        return
        
    updates = {
        "status": "closed",
        "closed_at": firestore.SERVER_TIMESTAMP
    }
    doc_ref.update(updates)
    write_audit_log("CLOSE_BILLING_CYCLE", admin_name, f"billing_cycles/{cycle_id}", old_data, updates)

def list_billing_cycles(status: str = None) -> list:
    """Lists all billing cycles, optionally filtering by status (open/closed)."""
    query = db.collection("billing_cycles")
    if status:
        query = _where_eq(query, "status", status)
    
    docs = query.get()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["cycle_id"] = doc.id
        results.append(data)
    # Sort by initiated_at desc
    results.sort(key=lambda x: x.get("initiated_at") or 0, reverse=True)
    return results

# ----------------------------------------------------
# Reading Functions
# ----------------------------------------------------
def get_reading(reading_id: str) -> dict | None:
    """Fetches details of a reading document."""
    doc = db.collection("readings").document(reading_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["reading_id"] = doc.id
        return data
    return None

def get_readings_for_cycle(cycle_id: str, cin_no: str = None) -> list:
    """Retrieves readings submitted under a specific cycle."""
    query = _where_eq(db.collection("readings"), "cycle_id", cycle_id)
    if cin_no:
        query = _where_eq(query, "cin_no", cin_no)
    
    docs = query.get()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["reading_id"] = doc.id
        results.append(data)
    return results

def admin_update_reading(reading_id: str, updates: dict, admin_name: str) -> None:
    """Updates a reading and recalculates the consumer's outstanding balance atomically."""
    import billing_engine
    from utils import parse_date
    
    reading_ref = db.collection("readings").document(reading_id)
    transaction = db.transaction()
    
    @firestore.transactional
    def update_in_transaction(txn, read_ref):
        reading_doc = txn.get(read_ref)
        if not reading_doc.exists:
            raise FileNotFoundError(f"Reading {reading_id} not found.")

        old_reading = reading_doc.to_dict()
        cin_no = old_reading["cin_no"]
        cycle_id = old_reading["cycle_id"]

        consumer_ref = db.collection("consumers").document(cin_no)
        consumer_doc = txn.get(consumer_ref)
        if not consumer_doc.exists:
            raise FileNotFoundError(f"Consumer {cin_no} not found.")
        consumer = consumer_doc.to_dict()
        consumer["cin_no"] = cin_no

        rates_ref = db.collection("charges_config").document("current")
        rates_doc = txn.get(rates_ref)
        rates = rates_doc.to_dict() if rates_doc.exists else DEFAULT_CHARGES_CONFIG

        cycle_ref = db.collection("billing_cycles").document(cycle_id)
        cycle_doc = txn.get(cycle_ref)
        cycle = cycle_doc.to_dict() if cycle_doc.exists else {}

        # Rollback old bill amount from consumer outstanding first
        old_breakdown = old_reading.get("full_bill_breakdown", {})
        old_total_amount = float(old_breakdown.get("total_amount", 0.0))
        old_credit_applied = float(old_breakdown.get("credit_applied", 0.0))

        # New values
        new_curr = float(updates.get("current_reading", old_reading["current_reading"]))
        prev_reading = float(old_reading["previous_reading"])
        new_consumption = new_curr - prev_reading
        if new_consumption < 0:
            raise ValueError("Updated current reading cannot be less than previous reading.")

        # Calculate base balances before the original bill was applied
        # total_amount = previous_outstanding + subtotal_after_credit + lps_amount
        # We need the previous_outstanding that was used for the original bill.
        base_outstanding = float(old_breakdown.get("previous_outstanding", 0.0))
        base_credit = float(consumer.get("credit_balance", 0.0)) + old_credit_applied

        last_pay_date = parse_date(cycle.get("last_payment_date")) if cycle.get("last_payment_date") else None

        new_breakdown = billing_engine.calculate_bill(
            consumption_kl=new_consumption,
            consumer=consumer,
            rates=rates,
            previous_outstanding=base_outstanding,
            credit_balance=base_credit,
            last_payment_date=last_pay_date,
            payment_date=date.today()
        )

        new_outstanding = new_breakdown["total_amount"]
        new_credit = new_breakdown["remaining_credit"]
        
        txn.update(consumer_ref, {
            "last_reading": new_curr,
            "outstanding_balance": float(new_outstanding),
            "credit_balance": float(new_credit),
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
        reading_updates = {
            "current_reading": new_curr,
            "consumption": new_consumption,
            "full_bill_breakdown": new_breakdown,
            "edited_by_admin": True,
            "notes": updates.get("notes", old_reading.get("notes"))
        }
        txn.update(read_ref, reading_updates)
        return old_reading, reading_updates

    old_reading, new_log_data = update_in_transaction(transaction, reading_ref)
    write_audit_log("ADMIN_UPDATE_READING", admin_name, f"readings/{reading_id}", old_reading, new_log_data)

def bulk_update_readings(updates_list: list, admin_name: str) -> dict:
    """Updates multiple readings and handles transactions per update."""
    success_count = 0
    errors = []
    
    for row_idx, item in enumerate(updates_list):
        try:
            reading_id = item.get("reading_id")
            updates = {"current_reading": item.get("current_reading"), "notes": item.get("notes")}
            admin_update_reading(reading_id, updates, admin_name)
            success_count += 1
        except Exception as e:
            errors.append({"row": row_idx + 2, "error": str(e)})
            
    return {"success": success_count, "errors": errors}

# ----------------------------------------------------
# Correction Query Functions
# ----------------------------------------------------
def get_pending_correction_queries() -> list:
    """Fetches all pending correction queries."""
    query = _where_eq(db.collection("correction_queries"), "status", "pending").get()
    results = []
    for doc in query:
        data = doc.to_dict()
        data["query_id"] = doc.id
        results.append(data)
    return results

def get_all_correction_queries(cycle_id: str = None) -> list:
    """Fetches all correction queries, optionally filtered by cycle_id."""
    query = db.collection("correction_queries")
    if cycle_id:
        query = _where_eq(query, "cycle_id", cycle_id)
        
    docs = query.get()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["query_id"] = doc.id
        results.append(data)
    # Sort by created_at desc
    results.sort(key=lambda x: x.get("created_at") or 0, reverse=True)
    return results

def approve_correction_query(query_id: str, admin_name: str) -> None:
    """Approves a query, updates the reading document, and recalculates balances."""
    query_ref = db.collection("correction_queries").document(query_id)
    query_doc = query_ref.get()
    if not query_doc.exists:
        raise FileNotFoundError(f"Correction query {query_id} not found.")
        
    query_data = query_doc.to_dict()
    if query_data["status"] != "pending":
        raise ValueError(f"Correction query is already {query_data['status']}")
        
    reading_id = query_data["reading_id"]
    req_reading = float(query_data["requested_corrected_reading"])
    
    # Update reading details (recalculates balances)
    admin_update_reading(reading_id, {"current_reading": req_reading, "notes": f"Corrected via Query: {query_data.get('reason')}"}, admin_name)
    
    # Mark query as approved
    query_ref.update({
        "status": "approved",
        "resolved_at": firestore.SERVER_TIMESTAMP
    })
    write_audit_log("APPROVE_CORRECTION_QUERY", admin_name, f"correction_queries/{query_id}", query_data, {"status": "approved"})

def reject_correction_query(query_id: str, rejection_note: str, admin_name: str) -> None:
    """Rejects a query and logs the rejection reason."""
    query_ref = db.collection("correction_queries").document(query_id)
    query_doc = query_ref.get()
    if not query_doc.exists:
        raise FileNotFoundError(f"Correction query {query_id} not found.")
        
    query_data = query_doc.to_dict()
    if query_data["status"] != "pending":
        raise ValueError(f"Correction query is already {query_data['status']}")
        
    updates = {
        "status": "rejected",
        "rejection_note": rejection_note,
        "resolved_at": firestore.SERVER_TIMESTAMP
    }
    query_ref.update(updates)
    write_audit_log("REJECT_CORRECTION_QUERY", admin_name, f"correction_queries/{query_id}", query_data, updates)

# ----------------------------------------------------
# Payment Functions
# ----------------------------------------------------
def record_payment(data: dict, admin_name: str) -> str:
    """Records a consumer payment, updating outstanding and credit balances atomically."""
    cin_no = data.get("cin_no")
    amount = float(data.get("amount", 0.0))
    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")
        
    payment_id = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(3).hex().upper()}"
    payment_ref = db.collection("payments").document(payment_id)
    consumer_ref = db.collection("consumers").document(cin_no)
    
    # Transactional write
    transaction = db.transaction()
    
    @firestore.transactional
    def execute_payment(txn, consumer_ref, pay_ref):
        consumer_doc = txn.get(consumer_ref)
        if not consumer_doc.exists:
            raise FileNotFoundError(f"Consumer {cin_no} not found.")
        consumer = consumer_doc.to_dict()

        curr_outstanding = float(consumer.get("outstanding_balance", 0.0))
        curr_credit = float(consumer.get("credit_balance", 0.0))

        if amount <= curr_outstanding:
            new_outstanding = curr_outstanding - amount
            new_credit = curr_credit
        else:
            new_outstanding = 0.0
            new_credit = curr_credit + (amount - curr_outstanding)

        txn.update(consumer_ref, {
            "outstanding_balance": new_outstanding,
            "credit_balance": new_credit,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
        from utils import generate_receipt_number
        pay_doc = {
            "cin_no": cin_no,
            "amount": amount,
            "payment_mode": data.get("payment_mode", "Cash"),
            "emitra_key": data.get("emitra_key") if data.get("payment_mode") == "E-Mitra" else None,
            "payment_date": data.get("payment_date"),
            "entry_date": data.get("entry_date", datetime.now().strftime("%d-%m-%Y")),
            "cycle_id": data.get("cycle_id"),
            "notes": data.get("notes"),
            "received_by": admin_name,
            "receipt_number": generate_receipt_number()
        }
        txn.set(pay_ref, pay_doc)
        
    consumer_ref = db.collection("consumers").document(cin_no)
    execute_payment(transaction, consumer_ref, payment_ref)
    
    # Log
    log_pay_doc = {
        "cin_no": cin_no,
        "amount": amount,
        "payment_mode": data.get("payment_mode"),
        "payment_date": data.get("payment_date")
    }
    write_audit_log("RECORD_PAYMENT", admin_name, f"payments/{payment_id}", None, log_pay_doc)
    return payment_id

def bulk_record_payments(data_list: list, admin_name: str) -> dict:
    """Enters multiple payments in parallel transactions."""
    success_count = 0
    errors = []
    
    for row_idx, item in enumerate(data_list):
        try:
            record_payment(item, admin_name)
            success_count += 1
        except Exception as e:
            errors.append({"row": row_idx + 2, "error": str(e)})
            
    return {"success": success_count, "errors": errors}

def get_payments_for_consumer(cin_no: str, cycle_id: str = None) -> list:
    """Retrieves payment history for a single consumer."""
    query = _where_eq(db.collection("payments"), "cin_no", cin_no)
    if cycle_id:
        query = _where_eq(query, "cycle_id", cycle_id)
        
    docs = query.get()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["payment_id"] = doc.id
        results.append(data)
    # Sort by payment_date parsed descending
    from utils import parse_date
    results.sort(key=lambda x: parse_date(x.get("payment_date")), reverse=True)
    return results

def list_payments(filters: dict = None) -> list:
    """Lists payments, supporting filters by consumer, date range, mode, or cycle."""
    query = db.collection("payments")
    if filters:
        if "cin_no" in filters and filters["cin_no"]:
            query = _where_eq(query, "cin_no", filters["cin_no"])
        if "mode" in filters and filters["mode"] and filters["mode"] != "All":
            query = _where_eq(query, "payment_mode", filters["mode"])
        if "cycle_id" in filters and filters["cycle_id"]:
            query = _where_eq(query, "cycle_id", filters["cycle_id"])
            
    docs = query.get()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["payment_id"] = doc.id
        results.append(data)
        
    # Date range filters manually evaluated since dates are stored as DD-MM-YYYY strings
    if filters and "date_from" in filters and "date_to" in filters:
        from utils import parse_date
        d_from = parse_date(filters["date_from"])
        d_to = parse_date(filters["date_to"])
        filtered = []
        for p in results:
            p_date = parse_date(p.get("payment_date"))
            if d_from <= p_date <= d_to:
                filtered.append(p)
        results = filtered
        
    return results

def update_consumer_lps_waiver(cin_no: str, waiver_amount: float, reason_note: str, admin_name: str) -> None:
    """Deducts an outstanding amount from a consumer due to an LPS waiver."""
    adj_id = f"ADJ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    adj_ref = db.collection("custom_adjustments").document(adj_id)
    consumer_ref = db.collection("consumers").document(cin_no)
    
    transaction = db.transaction()
    
    @firestore.transactional
    def apply_waiver(txn, cons_ref, adjustment_ref):
        consumer_doc = txn.get(cons_ref)
        if not consumer_doc.exists:
            raise FileNotFoundError(f"Consumer {cin_no} not found.")
        consumer = consumer_doc.to_dict()

        curr_outstanding = float(consumer.get("outstanding_balance", 0.0))
        if waiver_amount > curr_outstanding:
            raise ValueError(f"Waiver amount {waiver_amount} cannot exceed outstanding balance {curr_outstanding}")

        new_outstanding = curr_outstanding - waiver_amount

        txn.update(cons_ref, {
            "outstanding_balance": new_outstanding,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        txn.set(adjustment_ref, {
            "cin_no": cin_no,
            "type": "lps_waiver",
            "amount": waiver_amount,
            "reason_note": reason_note,
            "applied_by": admin_name,
            "applied_at": firestore.SERVER_TIMESTAMP,
            "cycle_id": None
        })
        
    apply_waiver(transaction, consumer_ref, adj_ref)
    write_audit_log("LPS_WAIVER", admin_name, f"consumers/{cin_no}", {"outstanding": curr_outstanding}, {"outstanding": new_outstanding, "waiver": waiver_amount, "reason": reason_note})

# ----------------------------------------------------
# Charges Config Functions
# ----------------------------------------------------
DEFAULT_CHARGES_CONFIG = {
    # Domestic rates (15mm-25mm)
    "domestic_slab_a_rate": 7.00,
    "domestic_slab_b_rate": 9.00,
    "domestic_slab_c_rate": 18.00,
    "domestic_slab_d_rate": 22.00,
    "domestic_min_15mm_avg_low": 88.00,
    "domestic_min_15mm_avg_high": 220.00,
    "domestic_min_20mm": 880.00,
    "domestic_min_25mm": 2200.00,
    "domestic_flat_rural": 110.00,

    # Non-Domestic rates (15mm-25mm)
    "nondomestic_slab_a_rate": 40.00,
    "nondomestic_slab_b_rate": 73.00,
    "nondomestic_slab_c_rate": 97.00,
    "nondomestic_min_15mm": 880.00,
    "nondomestic_min_20mm": 2200.00,
    "nondomestic_min_25mm": 3520.00,

    # Industrial rates (15mm-25mm)
    "industrial_slab_a_rate": 154.00,
    "industrial_slab_b_rate": 198.00,
    "industrial_slab_c_rate": 220.00,
    "industrial_min_15mm": 2200.00,
    "industrial_min_20mm": 3960.00,
    "industrial_min_25mm": 6160.00,

    # Bulk Connections (> 25mm) per KL
    "bulk_domestic_rate": 25.00,
    "bulk_nondomestic_rate": 97.00,
    "bulk_industrial_rate": 220.00,

    # Bulk Minimum Monthly
    "bulk_min_dom_40mm": 6600.00,
    "bulk_min_dom_50mm": 11000.00,
    "bulk_min_dom_80mm": 26400.00,
    "bulk_min_dom_100mm": 41800.00,
    "bulk_min_dom_150mm": 96600.00,
    "bulk_min_nondom_40mm": 10560.00,
    "bulk_min_nondom_50mm": 17600.00,
    "bulk_min_nondom_80mm": 44000.00,
    "bulk_min_nondom_100mm": 68200.00,
    "bulk_min_nondom_150mm": 185100.00,
    "bulk_min_ind_40mm": 29900.00,
    "bulk_min_ind_50mm": 46700.00,
    "bulk_min_ind_80mm": 119400.00,
    "bulk_min_ind_100mm": 186600.00,
    "bulk_min_ind_150mm": 419700.00,

    # Bulk Meter Service Charge
    "bulk_svc_40mm": 220.00,
    "bulk_svc_50mm": 440.00,
    "bulk_svc_80mm": 550.00,
    "bulk_svc_100mm": 660.00,
    "bulk_svc_150mm": 770.00,

    # Bulk Fixed Charge
    "bulk_fixed_dom_40mm": 55.00,
    "bulk_fixed_dom_50mm": 82.50,
    "bulk_fixed_dom_80mm": 110.00,
    "bulk_fixed_dom_100mm": 165.00,
    "bulk_fixed_dom_150mm": 220.00,
    "bulk_fixed_nondom_40mm": 110.00,
    "bulk_fixed_nondom_50mm": 165.00,
    "bulk_fixed_nondom_80mm": 220.00,
    "bulk_fixed_nondom_100mm": 330.00,
    "bulk_fixed_nondom_150mm": 440.00,
    "bulk_fixed_ind_40mm": 220.00,
    "bulk_fixed_ind_50mm": 330.00,
    "bulk_fixed_ind_80mm": 440.00,
    "bulk_fixed_ind_100mm": 550.00,
    "bulk_fixed_ind_150mm": 660.00,

    # General Charges
    "fixed_charge_domestic": 27.50,
    "fixed_charge_nondomestic": 55.00,
    "fixed_charge_industrial": 110.00,
    "meter_svc_15mm": 22.00,
    "meter_svc_20mm": 55.00,
    "meter_svc_25mm": 110.00,
}

def get_charges_config() -> dict:
    """Fetches the active water charges configurations."""
    doc_ref = db.collection("charges_config").document("current")
    doc = doc_ref.get()
    if doc.exists:
        rates = doc.to_dict() or {}
        missing_defaults = {k: v for k, v in DEFAULT_CHARGES_CONFIG.items() if k not in rates}
        if missing_defaults:
            doc_ref.update(missing_defaults)
            rates.update(missing_defaults)
        return rates
        
    # Baseline values for 2025 as fallback if config doesn't exist
    baseline = {
        **DEFAULT_CHARGES_CONFIG,
        "last_updated_by": "System Initialization",
        "last_updated_at": datetime.now().isoformat()
    }
    
    # Initialize baseline
    doc_ref.set(baseline)
    return baseline

def update_charges_config(new_rates: dict, admin_name: str, note: str) -> None:
    """Updates active water charges configurations. Stores pre-change snapshots in history collection."""
    current_ref = db.collection("charges_config").document("current")
    current_doc = current_ref.get()
    
    old_rates = current_doc.to_dict() if current_doc.exists else {}
    
    new_rates["last_updated_by"] = admin_name;
    new_rates["last_updated_at"] = datetime.now().isoformat();
    
    # Write to config history
    history_id = f"CH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    db.collection("charges_config_history").document(history_id).set({
        "snapshot_before": old_rates,
        "changed_by": admin_name,
        "changed_at": firestore.SERVER_TIMESTAMP,
        "admin_note": note
    })
    
    current_ref.set(new_rates)
    write_audit_log("UPDATE_CHARGES_CONFIG", admin_name, "charges_config/current", old_rates, new_rates)

def apply_annual_increment(admin_name: str) -> None:
    """Increments all numeric values inside charges_config by 10% (x1.10)."""
    current_rates = get_charges_config()
    updated_rates = {}
    
    for k, v in current_rates.items():
        if isinstance(v, (int, float)) and not k.endswith("date") and not k.endswith("by"):
            updated_rates[k] = round(v * 1.10, 2)
        else:
            updated_rates[k] = v
            
    update_charges_config(updated_rates, admin_name, "Annual 10% tariff increment applied.")

def get_charges_config_history() -> list:
    """Fetches charges modification historical logs."""
    history = db.collection("charges_config_history").order_by("changed_at", direction=firestore.Query.DESCENDING).get()
    results = []
    for doc in history:
        data = doc.to_dict()
        data["entry_id"] = doc.id
        results.append(data)
    return results

# ----------------------------------------------------
# Meter Reader Functions
# ----------------------------------------------------
def create_meter_reader(data: dict, admin_name: str) -> str:
    """Creates a Firebase Authentication user and sets their profile document in Firestore."""
    username = data.get("username", "")
    if "@" not in username:
        email = f"{username}@rjb.local"
    else:
        email = username
        
    password = data.get("password")
    
    # Create Firebase auth user
    user = auth.create_user(
        email=email,
        password=password,
        display_name=data.get("name")
    )
    
    uid = user.uid
    doc_ref = db.collection("meter_readers").document(uid)
    
    doc_data = {
        "uid": uid,
        "name": data.get("name"),
        "employee_id": data.get("employee_id"),
        "username": email,
        "phone_number": data.get("phone_number"),
        "designation": data.get("designation"),
        "address": data.get("address"),
        "zone": int(data.get("zone")) if data.get("zone") is not None else None,
        "is_active": True,
        "created_at": firestore.SERVER_TIMESTAMP
    }
    
    doc_ref.set(doc_data)
    write_audit_log("CREATE_METER_READER", admin_name, f"meter_readers/{uid}", None, doc_data)
    return uid

def get_meter_reader(uid: str) -> dict | None:
    """Retrieves profile of a specific meter reader."""
    doc = db.collection("meter_readers").document(uid).get()
    if doc.exists:
        data = doc.to_dict()
        data["uid"] = doc.id
        return data
    return None

def list_meter_readers(active_only: bool = False) -> list:
    """Lists all meter readers with status filtering."""
    query = db.collection("meter_readers")
    if active_only:
        query = _where_eq(query, "is_active", True)
        
    docs = query.get()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["uid"] = doc.id
        results.append(data)
    return results

def update_meter_reader(uid: str, updates: dict, admin_name: str) -> None:
    """Updates fields on a reader profile doc."""
    doc_ref = db.collection("meter_readers").document(uid)
    old_doc = doc_ref.get()
    if not old_doc.exists:
        raise FileNotFoundError(f"Reader profile {uid} not found.")
        
    old_data = old_doc.to_dict()
    
    # Clean inputs
    if "zone" in updates and updates["zone"] is not None:
        updates["zone"] = int(updates["zone"])
        
    doc_ref.update(updates)
    write_audit_log("UPDATE_METER_READER", admin_name, f"meter_readers/{uid}", old_data, updates)

def deactivate_meter_reader(uid: str, admin_name: str) -> None:
    """Disables the user in Firebase Auth and updates is_active in Firestore."""
    auth.update_user(uid, disabled=True)
    update_meter_reader(uid, {"is_active": False}, admin_name)
    write_audit_log("DEACTIVATE_METER_READER", admin_name, f"meter_readers/{uid}", None, {"disabled": True})

def reactivate_meter_reader(uid: str, admin_name: str) -> None:
    """Enables the user in Firebase Auth and updates is_active in Firestore."""
    auth.update_user(uid, disabled=False)
    update_meter_reader(uid, {"is_active": True}, admin_name)
    write_audit_log("REACTIVATE_METER_READER", admin_name, f"meter_readers/{uid}", None, {"disabled": False})

def reset_meter_reader_password(uid: str, new_password: str, admin_name: str) -> None:
    """Resets the Firebase Auth password for the user."""
    auth.update_user(uid, password=new_password)
    write_audit_log("RESET_METER_READER_PASSWORD", admin_name, f"auth_users/{uid}", None, {"password_reset": True})

# ----------------------------------------------------
# Custom Adjustment Functions
# ----------------------------------------------------
def add_custom_adjustment(cin_no: str, adj_type: str, amount: float, reason_note: str, admin_name: str, cycle_id: str = None) -> str:
    """Applies a custom debit/credit adjustment (penalty/waiver) to a consumer's account."""
    adj_id = f"ADJ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    adj_ref = db.collection("custom_adjustments").document(adj_id)
    consumer_ref = db.collection("consumers").document(cin_no)
    
    transaction = db.transaction()
    
    @firestore.transactional
    def apply_adjustment(txn, cons_ref, adjustment_ref):
        consumer_doc = txn.get(cons_ref)
        if not consumer_doc.exists:
            raise FileNotFoundError(f"Consumer {cin_no} not found.")
        consumer = consumer_doc.to_dict()

        curr_outstanding = float(consumer.get("outstanding_balance", 0.0))
        curr_credit = float(consumer.get("credit_balance", 0.0))

        # Adjust balances based on type
        if adj_type == "penalty":
            # Penalties increase outstanding balance
            new_outstanding = curr_outstanding + amount
            new_credit = curr_credit
        elif adj_type == "waiver":
            # Waivers reduce outstanding balance or increase credit balance
            if amount <= curr_outstanding:
                new_outstanding = curr_outstanding - amount
                new_credit = curr_credit
            else:
                new_outstanding = 0.0
                new_credit = curr_credit + (amount - curr_outstanding)
        elif adj_type == "lps_waiver":
            new_outstanding = max(0.0, curr_outstanding - amount)
            new_credit = curr_credit
        else:
            raise ValueError(f"Unknown adjustment type: {adj_type}")

        txn.update(cons_ref, {
            "outstanding_balance": new_outstanding,
            "credit_balance": new_credit,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        txn.set(adjustment_ref, {
            "cin_no": cin_no,
            "type": adj_type,
            "amount": amount,
            "reason_note": reason_note,
            "applied_by": admin_name,
            "applied_at": firestore.SERVER_TIMESTAMP,
            "cycle_id": cycle_id
        })
        
    apply_adjustment(transaction, consumer_ref, adj_ref)
    write_audit_log("ADD_CUSTOM_ADJUSTMENT", admin_name, f"custom_adjustments/{adj_id}", {"outstanding": curr_outstanding, "credit": curr_credit}, {"outstanding": new_outstanding, "credit": new_credit})
    return adj_id

def get_adjustments_for_consumer(cin_no: str) -> list:
    """Retrieves custom adjustments applied to a consumer's account."""
    query = _where_eq(db.collection("custom_adjustments"), "cin_no", cin_no).get()
    results = []
    for doc in query:
        data = doc.to_dict()
        data["adj_id"] = doc.id
        results.append(data)
    results.sort(key=lambda x: x.get("applied_at") or 0, reverse=True)
    return results

# ----------------------------------------------------
# Meter Replacement Functions
# ----------------------------------------------------
def record_meter_replacement(cin_no: str, old_serial: str, new_serial: str, replacement_date: str, new_initial_reading_kl: float, admin_name: str) -> str:
    """Logs a meter replacement event, updating serial no and resetting the verified reading on consumer document."""
    log_id = f"MTR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    log_ref = db.collection("meter_replacement_log").document(log_id)
    consumer_ref = db.collection("consumers").document(cin_no)
    
    transaction = db.transaction()
    
    @firestore.transactional
    def replace_meter(txn, cons_ref, l_ref):
        consumer_doc = txn.get(cons_ref)
        if not consumer_doc.exists:
            raise FileNotFoundError(f"Consumer {cin_no} not found.")

        txn.update(cons_ref, {
            "meter_serial_no": new_serial,
            "initial_meter_reading": float(new_initial_reading_kl),
            "last_reading": float(new_initial_reading_kl),
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        txn.set(l_ref, {
            "cin_no": cin_no,
            "old_meter_serial": old_serial,
            "new_meter_serial": new_serial,
            "replacement_date": replacement_date,
            "new_initial_reading": float(new_initial_reading_kl),
            "recorded_by": admin_name,
            "recorded_at": firestore.SERVER_TIMESTAMP
        })
        
    replace_meter(transaction, consumer_ref, log_ref)
    write_audit_log("RECORD_METER_REPLACEMENT", admin_name, f"consumers/{cin_no}", {"old_serial": old_serial}, {"new_serial": new_serial, "new_reading": new_initial_reading_kl})
    return log_id

def get_meter_replacement_history(cin_no: str) -> list:
    """Retrieves replacement history logs for a single consumer."""
    query = _where_eq(db.collection("meter_replacement_log"), "cin_no", cin_no).get()
    results = []
    for doc in query:
        data = doc.to_dict()
        data["log_id"] = doc.id
        results.append(data)
    results.sort(key=lambda x: x.get("recorded_at") or 0, reverse=True)
    return results

# ----------------------------------------------------
# Audit + Report Functions
# ----------------------------------------------------
def get_audit_log(filters: dict = None) -> list:
    """Retrieves records from audit logs."""
    query = db.collection("audit_log")
    
    if filters:
        if "action_type" in filters and filters["action_type"] and filters["action_type"] != "All":
            query = _where_eq(query, "action_type", filters["action_type"])
        if "performed_by" in filters and filters["performed_by"]:
            query = _where_eq(query, "performed_by_name", filters["performed_by"])
            
    docs = query.get()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["log_id"] = doc.id
        results.append(data)
        
    # Manual timestamp filter because dates can be specified
    if filters and "date_from" in filters and "date_to" in filters:
        from utils import parse_date
        d_from = parse_date(filters["date_from"])
        d_to = parse_date(filters["date_to"])
        
        filtered = []
        for r in results:
            ts = r.get("timestamp")
            if ts:
                # Firestore timestamp conversion
                if hasattr(ts, "datetime"):
                    r_date = ts.date()
                else:
                    # ISO string
                    r_date = datetime.fromisoformat(ts).date()
                    
                if d_from <= r_date <= d_to:
                    filtered.append(r)
        results = filtered
        
    # Sort by timestamp desc
    def get_time(x):
        ts = x.get("timestamp")
        if not ts:
            return datetime.min
        if hasattr(ts, "timestamp"):
            return ts
        return datetime.fromisoformat(ts)
        
    results.sort(key=get_time, reverse=True)
    return results

def get_meter_reader_activity(date_from, date_to, reader_uid=None, zone=None) -> list:
    """Aggregates readings submissions made by meter readers."""
    from utils import parse_date
    d_from = parse_date(date_from)
    d_to = parse_date(date_to)
    
    query = db.collection("readings")
    if reader_uid:
        query = _where_eq(query, "reader_uid", reader_uid)
        
    docs = query.get()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["reading_id"] = doc.id
        
        # Read date conversion and match
        r_date = parse_date(data.get("reading_date", ""))
        if d_from <= r_date <= d_to:
            # Join consumer details to get Zone / Consumer Name
            cons = get_consumer(data["cin_no"])
            if cons:
                data["consumer_name"] = cons["name"]
                data["zone"] = cons["zone"]
                data["employee_id"] = data.get("reader_employee_id", "Field Reader")
                
                # Check zone filter
                if zone is not None and int(data["zone"]) != int(zone):
                    continue
                results.append(data)
                
    # Sort by reading_date desc
    results.sort(key=lambda x: parse_date(x.get("reading_date")), reverse=True)
    return results

def get_billing_summary(cycle_id: str) -> dict:
    """Calculates summary KPIs for a specific billing cycle."""
    readings = get_readings_for_cycle(cycle_id)
    payments = list_payments({"cycle_id": cycle_id})
    
    total_billed = 0.0
    total_collected = 0.0
    
    for r in readings:
        if r.get("status") == "finalized":
            total_billed += r.get("full_bill_breakdown", {}).get("total_amount", 0.0)
            
    for p in payments:
        total_collected += p.get("amount", 0.0)
        
    # Outstanding
    total_outstanding = max(0.0, total_billed - total_collected)
    
    # Calculate consumer counts
    cycle_data = get_billing_cycle(cycle_id)
    consumer_count = 0
    if cycle_data:
        counts = cycle_data.get("consumer_count_per_zone", {})
        consumer_count = sum(counts.values())
        
    return {
        "total_billed": total_billed,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
        "consumer_count": consumer_count,
        "readings_count": len(readings)
    }

def get_zone_collection_report(cycle_id: str) -> list:
    """Prepares table data showing billing vs collection performance metrics per zone."""
    cycle = get_billing_cycle(cycle_id)
    if not cycle:
        return []
        
    zones = cycle.get("zones", [])
    readings = get_readings_for_cycle(cycle_id)
    payments = list_payments({"cycle_id": cycle_id})
    
    # Pre-fetch consumers for zones to map CIN -> Zone
    cin_to_zone = {}
    for zone in zones:
        for c in list_consumers({"zone": zone}):
            cin_to_zone[c["cin_no"]] = zone
            
    # Accumulators
    zone_data = {}
    for z in zones:
        zone_data[z] = {
            "zone": z,
            "total_consumers": cycle.get("consumer_count_per_zone", {}).get(str(z), 0),
            "read_consumers": 0,
            "cannot_read_consumers": 0,
            "pending_consumers": 0,
            "billed_amount": 0.0,
            "collected_amount": 0.0
        }
        
    for r in readings:
        r_cin = r.get("cin_no")
        r_zone = cin_to_zone.get(r_cin)
        if r_zone in zone_data:
            if r.get("status") == "finalized":
                zone_data[r_zone]["read_consumers"] += 1
                zone_data[r_zone]["billed_amount"] += r.get("full_bill_breakdown", {}).get("total_amount", 0.0)
            elif r.get("status") == "skipped":
                zone_data[r_zone]["cannot_read_consumers"] += 1
                
    for p in payments:
        p_cin = p.get("cin_no")
        p_zone = cin_to_zone.get(p_cin)
        if p_zone in zone_data:
            zone_data[p_zone]["collected_amount"] += p.get("amount", 0.0)
            
    # Resolve pending metrics
    for z in zones:
        total = zone_data[z]["total_consumers"]
        read = zone_data[z]["read_consumers"]
        skipped = zone_data[z]["cannot_read_consumers"]
        zone_data[z]["pending_consumers"] = max(0, total - (read + skipped))
        
    return list(zone_data.values())

def get_outstanding_balance_report() -> list:
    """Prepares list of all consumers who carry an active outstanding balance."""
    consumers = list_consumers({"is_active": True})
    outstanding = []
    
    for c in consumers:
        bal = float(c.get("outstanding_balance", 0.0))
        if bal > 0:
            # Format report item
            outstanding.append({
                "cin_no": c["cin_no"],
                "name": c["name"],
                "zone": c["zone"],
                "category": c["category"],
                "outstanding_balance": bal,
                "credit_balance": float(c.get("credit_balance", 0.0)),
                "status": c.get("consumer_status")
            })
            
    # Sort descending
    outstanding.sort(key=lambda x: x["outstanding_balance"], reverse=True)
    return outstanding

def get_skipped_readings_report(cycle_id: str) -> list:
    """Retrieves readings in a cycle marked with skipped/cannot read status."""
    readings = get_readings_for_cycle(cycle_id)
    skipped = []
    for r in readings:
        if r.get("status") == "skipped":
            cons = get_consumer(r["cin_no"])
            skipped.append({
                "cin_no": r["cin_no"],
                "name": cons["name"] if cons else "Unknown",
                "zone": cons["zone"] if cons else "Unknown",
                "reason": r.get("cannot_read_reason"),
                "reader_name": r.get("reader_name"),
                "reading_date": r.get("reading_date"),
                "notes": r.get("notes")
            })
    return skipped

def export_full_data_backup() -> dict:
    """Retrieves all documents in major collections to assemble an Excel backup."""
    backup = {}
    collections = ["consumers", "billing_cycles", "readings", "payments", "meter_readers", "custom_adjustments", "meter_replacement_log", "audit_log"]
    for c_name in collections:
        docs = db.collection(c_name).get()
        rows = []
        for doc in docs:
            data = doc.to_dict()
            data["document_id"] = doc.id
            # Flatten maps/lists to strings for Excel readability
            flat_data = {}
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    flat_data[k] = str(serialize_val(v))
                elif hasattr(v, "isoformat"):
                    flat_data[k] = v.isoformat()
                else:
                    flat_data[k] = v
            rows.append(flat_data)
        backup[c_name] = rows
    return backup
