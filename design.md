# design.md — Rajasthan Jal Board Admin Console
## PySide6 Desktop Application Design System v1.0

---

## 1. DESIGN PHILOSOPHY

**Concept: "Precision Ledger"**

This is a high-density government billing instrument. Every screen is data-first — forms, tables, and figures dominate. The aesthetic is that of a well-worn but meticulously maintained ledger: authoritative, legible, and completely unambiguous. Nothing decorative exists unless it earns its place by aiding comprehension.

The JetBrains Mono typeface is the defining character of the interface. Monospace alignment makes billing figures scannable, columns visually self-organised, and the entire app feel like a precision instrument built specifically for this job — not a generic form runner.

Colour is used with strict economy. The dark navy background creates depth. The saffron accent (a nod to Rajasthan's desert palette) marks every actionable primary element. Blue marks informational and navigational states. Everything else is greyscale.

---

## 2. COLOUR SYSTEM

Define all colours as Python constants in a `theme.py` file (or at the top of `main.py` as a dict). Apply via a single QSS stylesheet loaded at app startup. Never hardcode colours inline.

### Base Palette

| Token | Hex | Use |
|---|---|---|
| `BG_BASE` | `#090E1A` | Main window background |
| `BG_SURFACE` | `#0F1624` | Panels, frames, page content area |
| `BG_ELEVATED` | `#162030` | Cards, QGroupBox, dialogs |
| `BG_RAISED` | `#1C2A3E` | Hovered rows, selected items, input fields |
| `BG_SIDEBAR` | `#070B14` | Left sidebar background |
| `BG_SIDEBAR_HOVER` | `#0F1624` | Sidebar item hover state |
| `BG_SIDEBAR_ACTIVE` | `#162030` | Active sidebar item background |

### Border Palette

| Token | Hex | Use |
|---|---|---|
| `BORDER_SUBTLE` | `#1A2540` | Card/group box borders, table grid lines |
| `BORDER_DEFAULT` | `#243252` | Input default border, separator lines |
| `BORDER_FOCUS` | `#3B7DD8` | Input focused border |
| `BORDER_ACCENT` | `#C97B2E` | Sidebar active left-edge indicator |

### Text Palette

| Token | Hex | Use |
|---|---|---|
| `TEXT_PRIMARY` | `#D8E0EE` | Body text, table data, input values |
| `TEXT_SECONDARY` | `#7A8AAA` | Labels, captions, placeholder text |
| `TEXT_MUTED` | `#3D4F6E` | Disabled text, ghost text |
| `TEXT_ON_ACCENT` | `#FFFFFF` | Text on coloured buttons |
| `TEXT_HEADING` | `#EAF0FF` | Page titles, section headings |

### Accent — Saffron (Primary Actions)

| Token | Hex | Use |
|---|---|---|
| `ACCENT_SAFFRON` | `#E8913A` | Primary button background, active sidebar indicator dot |
| `ACCENT_SAFFRON_HOVER` | `#CF7D2A` | Primary button hover |
| `ACCENT_SAFFRON_DIM` | `#2A1A07` | Saffron-tinted backgrounds (badge bg, highlight row) |
| `ACCENT_SAFFRON_TEXT` | `#F5B06A` | Saffron text on dark background (status tags) |

### Accent — Blue (Secondary / Informational)

| Token | Hex | Use |
|---|---|---|
| `ACCENT_BLUE` | `#3B7DD8` | Secondary buttons, links, focus rings, info badges |
| `ACCENT_BLUE_HOVER` | `#2D6BC4` | Secondary button hover |
| `ACCENT_BLUE_DIM` | `#0A1A35` | Blue-tinted background (info tags, selected rows) |
| `ACCENT_BLUE_TEXT` | `#6BA3E8` | Blue text on dark background |

### Semantic Colours

| Token | Hex | Use |
|---|---|---|
| `SEM_SUCCESS` | `#2EA84A` | Success states, Active status |
| `SEM_SUCCESS_DIM` | `#0A2015` | Success badge background |
| `SEM_SUCCESS_TEXT` | `#5CCF78` | Success text |
| `SEM_WARNING` | `#D4950A` | Warning states, anomaly flags |
| `SEM_WARNING_DIM` | `#221500` | Warning badge background |
| `SEM_WARNING_TEXT` | `#F0B730` | Warning text |
| `SEM_ERROR` | `#C93B3B` | Error states, Disconnected status, danger buttons |
| `SEM_ERROR_DIM` | `#200A0A` | Error badge background |
| `SEM_ERROR_TEXT` | `#EF7070` | Error text |
| `SEM_NEUTRAL` | `#4A5A78` | Inactive/neutral states |
| `SEM_NEUTRAL_DIM` | `#121A2A` | Neutral badge background |
| `SEM_NEUTRAL_TEXT` | `#7A8AAA` | Neutral text |

---

## 3. TYPOGRAPHY

**Font family: JetBrains Mono, everywhere, without exception.**

This is a deliberate choice. The monospace grid gives numerical data (billing figures, KL readings, CIN numbers) perfect column alignment without any table trickery. Load via `QApplication.setFont(QFont("JetBrains Mono", 10))`.

JetBrains Mono must be bundled with the application or installed as a system font. Include it in an `assets/fonts/` directory and load it via `QFontDatabase.addApplicationFont()` at startup before the main window is created.

### Type Scale

| Role | Size | Weight | Colour Token | Use |
|---|---|---|---|---|
| `TYPE_PAGE_TITLE` | 15pt | Bold (700) | `TEXT_HEADING` | Page/tab titles (e.g. "Consumers", "Billing Cycles") |
| `TYPE_SECTION_HEADING` | 11pt | Bold (700) | `TEXT_HEADING` | QGroupBox titles, section headers |
| `TYPE_BODY` | 10pt | Regular (400) | `TEXT_PRIMARY` | All body text, form values, table cells |
| `TYPE_LABEL` | 10pt | Regular (400) | `TEXT_SECONDARY` | Form labels, table column headers |
| `TYPE_SMALL` | 9pt | Regular (400) | `TEXT_SECONDARY` | Captions, status bar, metadata |
| `TYPE_MONOFIGURE` | 10pt | Regular (400) | `TEXT_PRIMARY` | Numeric fields (₹ amounts, KL, dates) — inherits from body but called out explicitly |
| `TYPE_BADGE` | 8pt | Bold (700) | varies | Status badges, count pills |
| `TYPE_BUTTON_PRIMARY` | 10pt | Bold (700) | `TEXT_ON_ACCENT` | Primary action buttons |
| `TYPE_BUTTON_SECONDARY` | 10pt | Regular (400) | `TEXT_PRIMARY` | Secondary/ghost buttons |
| `TYPE_SIDEBAR_ITEM` | 10pt | Regular (400) | `TEXT_SECONDARY` | Sidebar nav items (inactive) |
| `TYPE_SIDEBAR_ACTIVE` | 10pt | Bold (700) | `TEXT_HEADING` | Sidebar nav active item |

---

## 4. SPACING & LAYOUT SYSTEM

Base unit: **8px**. All spacing is a multiple of this unit.

| Token | Value | Use |
|---|---|---|
| `SPACE_XS` | 4px | Icon-to-text gaps, tight inline padding |
| `SPACE_SM` | 8px | Default widget margin, compact padding |
| `SPACE_MD` | 16px | Standard section padding, form row spacing |
| `SPACE_LG` | 24px | Between major sections, card padding |
| `SPACE_XL` | 32px | Page-level top padding |

### Border Radius

| Token | Value | Use |
|---|---|---|
| `RADIUS_SM` | 3px | Buttons, inputs, tags |
| `RADIUS_MD` | 5px | Cards, QGroupBox |
| `RADIUS_LG` | 8px | Dialogs, tooltips |

### Application Layout Dimensions

| Element | Value |
|---|---|
| Sidebar width | 200px |
| Sidebar item height | 40px |
| Sidebar item left padding | 16px |
| Sidebar section separator | 1px `BORDER_SUBTLE` |
| Toolbar / header bar height | 44px |
| Status bar height | 26px |
| Content area padding | 24px |
| Form label minimum width | 160px |
| Input minimum height | 30px |
| Table row height | 32px |
| Table header height | 36px |
| Dialog minimum width | 480px |
| Dialog maximum width | 720px |

---

## 5. COMPONENT SPECIFICATIONS

### 5.1 Main Window

```
QMainWindow {
    background: BG_BASE;
}
```

Structure:
```
QMainWindow
├── Central widget (QWidget)
│   ├── HBoxLayout
│   │   ├── Sidebar (QWidget, fixed 200px)
│   │   └── Content stack (QStackedWidget, stretch=1)
└── QStatusBar
```

### 5.2 Sidebar

Background: `BG_SIDEBAR`. No border on the right — let the content surface (`BG_SURFACE`) sit flush. The depth difference between `#070B14` and `#0F1624` creates implicit separation.

**App header section** (top of sidebar, 64px tall):
- Text: `"RJB Admin"` — 12pt Bold, `TEXT_HEADING`
- Subtext: `"PHED Rajasthan"` — 8pt, `TEXT_MUTED`
- Add a 2px wide saffron left border on the entire header block (decorative, always visible)

**Nav items:**
```
Normal:    bg BG_SIDEBAR,           text TEXT_SECONDARY 10pt,    left-padding 16px
Hover:     bg BG_SIDEBAR_HOVER,     text TEXT_PRIMARY
Active:    bg BG_SIDEBAR_ACTIVE,    text TEXT_HEADING 10pt bold,
           3px left border ACCENT_SAFFRON (clip the left edge — use setContentsMargins(3,0,0,0) and a QFrame border-left trick)
```

Nav item layout: `[SPACE_MD] [emoji icon 14px] [SPACE_SM] [label text]`

Use emoji icons as-is (they render fine at small sizes in Qt). Or optionally load SVG icons from `assets/icons/` if design.md is updated to include icon set.

**Divider between nav groups:** 1px `BORDER_SUBTLE`, 8px vertical margin, 16px horizontal inset.

**Bottom of sidebar** (pinned): admin name (9pt, `TEXT_SECONDARY`) and a "Lock / Logout" small button.

### 5.3 QTabWidget

```
Tab bar background:       BG_SURFACE
Tab (inactive):           bg BG_SURFACE,    text TEXT_SECONDARY,  border-bottom 2px transparent,  padding 8px 16px
Tab (hover):              text TEXT_PRIMARY
Tab (active/selected):    bg BG_ELEVATED,   text TEXT_HEADING bold, border-bottom 2px ACCENT_SAFFRON
Tab pane:                 bg BG_ELEVATED,   border 1px BORDER_SUBTLE, border-radius RADIUS_MD (bottom + sides only)
```

No rounded top corners on tabs. The active tab bottom-border saffron line is the only colour indicator.

### 5.4 QGroupBox

```
QGroupBox {
    background:    BG_ELEVATED;
    border:        1px solid BORDER_SUBTLE;
    border-radius: RADIUS_MD;
    padding:       SPACE_MD;
    margin-top:    18px;    /* space for the title label */
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: -2px;
    padding: 0 6px;
    background: BG_ELEVATED;
    color: TEXT_SECONDARY;
    font-size: 10pt;
    font-weight: bold;
}
```

### 5.5 QPushButton

Use `setObjectName()` to apply variant styles:

**Primary** (`objectName="primary"`):
```
background:    ACCENT_SAFFRON;
color:         TEXT_ON_ACCENT;
border:        none;
border-radius: RADIUS_SM;
padding:       6px 18px;
font-weight:   bold;
min-height:    30px;

:hover   → background ACCENT_SAFFRON_HOVER
:pressed → background darken ACCENT_SAFFRON_HOVER by 10%
:disabled → opacity 0.4
```

**Secondary** (`objectName="secondary"` — default if no objectName set):
```
background:    transparent;
color:         TEXT_PRIMARY;
border:        1px solid BORDER_DEFAULT;
border-radius: RADIUS_SM;
padding:       6px 18px;
min-height:    30px;

:hover   → background BG_RAISED,  border-color ACCENT_BLUE
:pressed → background BG_ELEVATED
:disabled → opacity 0.4
```

**Danger** (`objectName="danger"`):
```
background:    SEM_ERROR;
color:         TEXT_ON_ACCENT;
border:        none;
border-radius: RADIUS_SM;
padding:       6px 18px;
font-weight:   bold;
min-height:    30px;

:hover   → background darken SEM_ERROR by 15%
:disabled → opacity 0.4
```

**Ghost / Link** (`objectName="ghost"`):
```
background:    transparent;
color:         ACCENT_BLUE_TEXT;
border:        none;
padding:       4px 8px;
text-decoration: underline;

:hover → color ACCENT_BLUE
```

### 5.6 QLineEdit / QTextEdit / QPlainTextEdit

```
background:    BG_RAISED;
color:         TEXT_PRIMARY;
border:        1px solid BORDER_DEFAULT;
border-radius: RADIUS_SM;
padding:       5px 10px;
min-height:    30px;
selection-background-color: ACCENT_BLUE_DIM;
selection-color: TEXT_PRIMARY;

:focus  → border 1px solid BORDER_FOCUS (ACCENT_BLUE)
:disabled → background BG_SURFACE, color TEXT_MUTED, border-color BORDER_SUBTLE
```

Placeholder text colour: `TEXT_MUTED` (`QLineEdit::placeholderText` → set via `setPlaceholderText`, colour via QSS `color` on `QLineEdit[text=""]` or directly in QSS using `placeholder-text-color`).

### 5.7 QComboBox

```
QComboBox {
    background:    BG_RAISED;
    color:         TEXT_PRIMARY;
    border:        1px solid BORDER_DEFAULT;
    border-radius: RADIUS_SM;
    padding:       5px 10px;
    min-height:    30px;
}
QComboBox:focus { border-color: BORDER_FOCUS; }
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    /* Use a simple Unicode char or a small SVG arrow */
    image: url(assets/icons/chevron_down.svg);
    width: 12px;
}
QComboBox QAbstractItemView {
    background:      BG_ELEVATED;
    border:          1px solid BORDER_DEFAULT;
    selection-background-color: ACCENT_BLUE_DIM;
    selection-color: TEXT_PRIMARY;
    padding:         4px 0;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding:    6px 12px;
    min-height: 28px;
}
QComboBox QAbstractItemView::item:hover {
    background: BG_RAISED;
}
```

### 5.8 QSpinBox / QDoubleSpinBox

Same base styles as `QLineEdit`. Additionally:

```
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background:   BG_ELEVATED;
    border:       none;
    width:        20px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: BG_RAISED;
}
```

### 5.9 QCheckBox / QRadioButton

```
QCheckBox, QRadioButton {
    color:   TEXT_PRIMARY;
    spacing: 8px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width:            16px;
    height:           16px;
    border:           1px solid BORDER_DEFAULT;
    border-radius:    3px;   /* 50% for radio */
    background:       BG_RAISED;
}
QCheckBox::indicator:hover {
    border-color: ACCENT_BLUE;
}
QCheckBox::indicator:checked {
    background:   ACCENT_SAFFRON;
    border-color: ACCENT_SAFFRON;
    /* Use a checkmark SVG or set image: url(assets/icons/check.svg) */
}
QRadioButton::indicator { border-radius: 8px; }
QRadioButton::indicator:checked {
    background:   ACCENT_SAFFRON;
    border-color: ACCENT_SAFFRON;
}
```

### 5.10 QTableWidget

```
QTableWidget {
    background:          BG_SURFACE;
    alternate-background-color: BG_ELEVATED;
    gridline-color:      BORDER_SUBTLE;
    color:               TEXT_PRIMARY;
    border:              1px solid BORDER_SUBTLE;
    border-radius:       RADIUS_MD;
    selection-background-color: ACCENT_BLUE_DIM;
    selection-color:     TEXT_PRIMARY;
    outline:             none;
}
QTableWidget::item {
    padding:    0 12px;
    height:     32px;
    border:     none;
}
QTableWidget::item:selected {
    background: ACCENT_BLUE_DIM;
    color:      TEXT_PRIMARY;
}
QHeaderView::section {
    background:   BG_BASE;
    color:        TEXT_SECONDARY;
    font-weight:  bold;
    font-size:    9pt;
    border:       none;
    border-bottom: 1px solid BORDER_DEFAULT;
    border-right:  1px solid BORDER_SUBTLE;
    padding:      0 12px;
    height:       36px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QHeaderView::section:last { border-right: none; }
```

**Column alignment conventions:**
- CIN No, Meter Serial, Name, Address: left-align
- ₹ amounts, KL figures, dates, integers: **right-align** (monospace makes this look sharp)
- Status badges: centre-align

**Row colours** (set via `setAlternatingRowColors(True)`):
- Even rows: `BG_SURFACE`
- Odd rows: `BG_ELEVATED`

**Status cell rendering:** Inject status badges as `QLabel` via `setCellWidget` — never plain text for status. See Section 5.14 for badge specs.

### 5.11 QScrollBar

```
QScrollBar:vertical {
    background: BG_SURFACE;
    width:      8px;
    margin:     0;
}
QScrollBar::handle:vertical {
    background:    BORDER_DEFAULT;
    border-radius: 4px;
    min-height:    32px;
}
QScrollBar::handle:vertical:hover { background: TEXT_MUTED; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: BG_SURFACE;
    height:     8px;
}
QScrollBar::handle:horizontal {
    background:   BORDER_DEFAULT;
    border-radius: 4px;
    min-width:    32px;
}
```

### 5.12 QTabWidget (revisited — full QSS)

```
QTabWidget::pane {
    background:   BG_ELEVATED;
    border:       1px solid BORDER_SUBTLE;
    border-top:   none;
    border-radius: 0 0 RADIUS_MD RADIUS_MD;
}
QTabBar::tab {
    background:    BG_SURFACE;
    color:         TEXT_SECONDARY;
    padding:       8px 20px;
    border:        none;
    border-bottom: 2px solid transparent;
    margin-right:  2px;
}
QTabBar::tab:hover { color: TEXT_PRIMARY; background: BG_ELEVATED; }
QTabBar::tab:selected {
    background:    BG_ELEVATED;
    color:         TEXT_HEADING;
    font-weight:   bold;
    border-bottom: 2px solid ACCENT_SAFFRON;
}
```

### 5.13 QDialog

```
QDialog {
    background:   BG_ELEVATED;
    border:       1px solid BORDER_DEFAULT;
    border-radius: RADIUS_LG;
}
```

Dialog structure:
- Title bar: custom `QLabel` 12pt Bold `TEXT_HEADING`, 16px top/left padding, 44px height
- Separator: 1px `BORDER_SUBTLE`, full width
- Content area: 24px padding on all sides
- Button row: right-aligned, 16px bottom padding, 8px gap between buttons
- Always: Primary action on the right, Secondary/Cancel on the left

### 5.14 Status Badges

Render as `QLabel` with stylesheet applied. Do not use plain text in table cells for status.

```python
def make_status_badge(text: str, bg: str, fg: str) -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet(f"""
        QLabel {{
            background: {bg};
            color: {fg};
            border-radius: 3px;
            padding: 2px 8px;
            font-size: 8pt;
            font-weight: bold;
        }}
    """)
    return label
```

| Consumer Status | `bg` token | `fg` token |
|---|---|---|
| Active | `SEM_SUCCESS_DIM` | `SEM_SUCCESS_TEXT` |
| Inactive | `SEM_NEUTRAL_DIM` | `SEM_NEUTRAL_TEXT` |
| Meter Faulty | `SEM_WARNING_DIM` | `SEM_WARNING_TEXT` |
| Disconnected | `SEM_ERROR_DIM` | `SEM_ERROR_TEXT` |
| Disputed | `ACCENT_SAFFRON_DIM` | `ACCENT_SAFFRON_TEXT` |

| Supply Type | `bg` token | `fg` token |
|---|---|---|
| PHED | `ACCENT_BLUE_DIM` | `ACCENT_BLUE_TEXT` |
| Own Supply | `#1A0E30` | `#B89EF5` |

| LPS Type | `bg` | `fg` |
|---|---|---|
| None | `SEM_SUCCESS_DIM` | `SEM_SUCCESS_TEXT` |
| 10% | `SEM_WARNING_DIM` | `SEM_WARNING_TEXT` |
| 10% + Interest | `SEM_ERROR_DIM` | `SEM_ERROR_TEXT` |

### 5.15 QProgressBar

```
QProgressBar {
    background:    BG_RAISED;
    border:        1px solid BORDER_SUBTLE;
    border-radius: RADIUS_SM;
    height:        8px;
    text-align:    center;
    color:         transparent;   /* hide percentage text for thin bars */
}
QProgressBar::chunk {
    background:    ACCENT_SAFFRON;
    border-radius: RADIUS_SM;
}
```

For the bulk import progress bar, set `setTextVisible(True)` and change `color` to `TEXT_PRIMARY`.

### 5.16 QStatusBar

```
QStatusBar {
    background: BG_SIDEBAR;
    color:      TEXT_SECONDARY;
    font-size:  9pt;
    border-top: 1px solid BORDER_SUBTLE;
    padding:    0 16px;
    min-height: 26px;
}
QStatusBar::item { border: none; }
```

Content (left to right): `[Admin: {name}]` — separator ` | ` — `[Date: {DD-MM-YYYY}]` — stretch — `[app version]`

### 5.17 QMessageBox

```
QMessageBox {
    background: BG_ELEVATED;
}
QMessageBox QLabel {
    color:     TEXT_PRIMARY;
    font-size: 10pt;
    min-width: 320px;
}
QMessageBox QPushButton { min-width: 80px; }
```

Always set the window title, the icon (Warning/Critical/Question), and size the dialog via `setMinimumWidth(400)`. Use `QMessageBox.question` for destructive confirmations with explicit `Yes` / `Cancel` buttons — never use default button text.

### 5.18 QSplitter (used in Meter Readers page)

```
QSplitter::handle {
    background: BORDER_SUBTLE;
    width:      1px;
}
QSplitter::handle:hover { background: ACCENT_BLUE; }
```

### 5.19 QFormLayout conventions

- `setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)`
- `setFormAlignment(Qt.AlignTop)`
- `setHorizontalSpacing(16)`
- `setVerticalSpacing(12)`
- Wrap the `QFormLayout` in a `QWidget` with `setContentsMargins(0, 0, 0, 0)`
- Required field labels: append `" *"` in `ACCENT_SAFFRON_TEXT` colour (use `QLabel` with rich text: `"Field Name <span style='color:#E8913A'>*</span>"`)

---

## 6. CHARTS (`matplotlib` embedded)

Use `FigureCanvasQTAgg` from `matplotlib.backends.backend_qtagg`.

Apply these matplotlib rcParams before any figure is created:

```python
import matplotlib
matplotlib.rcParams.update({
    "figure.facecolor":     "#0F1624",   # BG_SURFACE
    "axes.facecolor":       "#162030",   # BG_ELEVATED
    "axes.edgecolor":       "#1A2540",   # BORDER_SUBTLE
    "axes.labelcolor":      "#7A8AAA",   # TEXT_SECONDARY
    "axes.titlecolor":      "#EAF0FF",   # TEXT_HEADING
    "xtick.color":          "#7A8AAA",
    "ytick.color":          "#7A8AAA",
    "text.color":           "#D8E0EE",   # TEXT_PRIMARY
    "grid.color":           "#1A2540",
    "grid.linestyle":       "--",
    "grid.alpha":           0.5,
    "font.family":          "monospace",
    "font.monospace":       ["JetBrains Mono", "Courier New", "monospace"],
    "font.size":            9,
})
```

Chart colour sequence (use in order for multi-series charts):
```
["#E8913A", "#3B7DD8", "#2EA84A", "#D4950A", "#C93B3B", "#B89EF5"]
```

---

## 7. FULL QSS STYLESHEET

Save as `assets/style.qss`. Load at startup:
```python
with open("assets/style.qss", "r") as f:
    app.setStyleSheet(f.read())
```

The stylesheet uses the hex values directly (not the token names — QSS does not support variables). Keep a comment at the top of style.qss mapping token names to their hex values for maintainability.

```css
/* ============================================================
   RJB Admin Console — Main Stylesheet
   Font: JetBrains Mono
   ============================================================
   TOKEN MAP:
   BG_BASE         #090E1A    BG_SURFACE      #0F1624
   BG_ELEVATED     #162030    BG_RAISED       #1C2A3E
   BG_SIDEBAR      #070B14    BG_SIDEBAR_HOVER #0F1624
   BORDER_SUBTLE   #1A2540    BORDER_DEFAULT  #243252
   BORDER_FOCUS    #3B7DD8
   TEXT_PRIMARY    #D8E0EE    TEXT_SECONDARY  #7A8AAA
   TEXT_MUTED      #3D4F6E    TEXT_HEADING    #EAF0FF
   ACCENT_SAFFRON  #E8913A    ACCENT_SAFFRON_HOVER #CF7D2A
   ACCENT_BLUE     #3B7DD8    ACCENT_BLUE_DIM #0A1A35
   SEM_SUCCESS     #2EA84A    SEM_ERROR       #C93B3B
   SEM_WARNING     #D4950A
   ============================================================ */

* {
    font-family: "JetBrains Mono";
    font-size: 10pt;
    color: #D8E0EE;
    outline: none;
}

QMainWindow, QWidget {
    background: #090E1A;
}

/* ── Sidebar ─────────────────────────────────────────────── */
QWidget#sidebar {
    background: #070B14;
    border-right: 1px solid #1A2540;
}

QPushButton#nav_item {
    background:    transparent;
    color:         #7A8AAA;
    border:        none;
    border-left:   3px solid transparent;
    border-radius: 0;
    text-align:    left;
    padding:       0 0 0 16px;
    min-height:    40px;
    font-size:     10pt;
    font-weight:   normal;
}
QPushButton#nav_item:hover {
    background: #0F1624;
    color:      #D8E0EE;
}
QPushButton#nav_item_active {
    background:  #162030;
    color:       #EAF0FF;
    border-left: 3px solid #E8913A;
    font-weight: bold;
}

/* ── Content area ────────────────────────────────────────── */
QStackedWidget {
    background: #0F1624;
}

/* ── QGroupBox ───────────────────────────────────────────── */
QGroupBox {
    background:    #162030;
    border:        1px solid #1A2540;
    border-radius: 5px;
    margin-top:    18px;
    padding:       16px;
}
QGroupBox::title {
    subcontrol-origin:   margin;
    subcontrol-position: top left;
    left:       12px;
    top:        -1px;
    padding:    0 6px;
    background: #162030;
    color:      #7A8AAA;
    font-weight: bold;
    font-size:  10pt;
}

/* ── QTabWidget ──────────────────────────────────────────── */
QTabWidget::pane {
    background:    #162030;
    border:        1px solid #1A2540;
    border-top:    none;
    border-radius: 0 0 5px 5px;
}
QTabBar::tab {
    background:    #0F1624;
    color:         #7A8AAA;
    padding:       8px 20px;
    border:        none;
    border-bottom: 2px solid transparent;
    margin-right:  2px;
}
QTabBar::tab:hover   { color: #D8E0EE; background: #162030; }
QTabBar::tab:selected {
    background:    #162030;
    color:         #EAF0FF;
    font-weight:   bold;
    border-bottom: 2px solid #E8913A;
}

/* ── Inputs ──────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {
    background:    #1C2A3E;
    color:         #D8E0EE;
    border:        1px solid #243252;
    border-radius: 3px;
    padding:       5px 10px;
    min-height:    30px;
    selection-background-color: #0A1A35;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #3B7DD8;
}
QLineEdit:disabled, QTextEdit:disabled {
    background: #0F1624;
    color:      #3D4F6E;
    border-color: #1A2540;
}

QComboBox {
    background:    #1C2A3E;
    color:         #D8E0EE;
    border:        1px solid #243252;
    border-radius: 3px;
    padding:       5px 10px;
    min-height:    30px;
}
QComboBox:focus           { border-color: #3B7DD8; }
QComboBox::drop-down      { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background:               #162030;
    border:                   1px solid #243252;
    selection-background-color: #0A1A35;
    selection-color:          #D8E0EE;
    outline:                  none;
    padding:                  4px 0;
}
QComboBox QAbstractItemView::item { padding: 6px 12px; min-height: 28px; }
QComboBox QAbstractItemView::item:hover { background: #1C2A3E; }

QSpinBox, QDoubleSpinBox {
    background:    #1C2A3E;
    color:         #D8E0EE;
    border:        1px solid #243252;
    border-radius: 3px;
    padding:       5px 10px;
    min-height:    30px;
}
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #3B7DD8; }
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background: #162030;
    border: none;
    width: 20px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: #1C2A3E;
}

/* ── Buttons ─────────────────────────────────────────────── */
QPushButton {
    background:    transparent;
    color:         #D8E0EE;
    border:        1px solid #243252;
    border-radius: 3px;
    padding:       6px 18px;
    min-height:    30px;
}
QPushButton:hover   { background: #1C2A3E; border-color: #3B7DD8; }
QPushButton:pressed { background: #162030; }
QPushButton:disabled { color: #3D4F6E; border-color: #1A2540; }

QPushButton#primary {
    background:  #E8913A;
    color:       #FFFFFF;
    border:      none;
    font-weight: bold;
}
QPushButton#primary:hover   { background: #CF7D2A; }
QPushButton#primary:pressed { background: #B86D20; }
QPushButton#primary:disabled { background: #3D2C15; color: #7A5A30; border: none; }

QPushButton#danger {
    background:  #C93B3B;
    color:       #FFFFFF;
    border:      none;
    font-weight: bold;
}
QPushButton#danger:hover   { background: #A83030; }
QPushButton#danger:pressed { background: #8A2525; }

QPushButton#ghost {
    background: transparent;
    color:      #6BA3E8;
    border:     none;
    padding:    4px 8px;
    text-decoration: underline;
}
QPushButton#ghost:hover { color: #3B7DD8; }

/* ── QCheckBox / QRadioButton ────────────────────────────── */
QCheckBox, QRadioButton {
    color:   #D8E0EE;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #243252;
    border-radius: 3px;
    background: #1C2A3E;
}
QCheckBox::indicator:hover    { border-color: #3B7DD8; }
QCheckBox::indicator:checked  { background: #E8913A; border-color: #E8913A; }
QRadioButton::indicator {
    width: 16px; height: 16px;
    border: 1px solid #243252;
    border-radius: 8px;
    background: #1C2A3E;
}
QRadioButton::indicator:hover   { border-color: #3B7DD8; }
QRadioButton::indicator:checked { background: #E8913A; border-color: #E8913A; }

/* ── QTableWidget ────────────────────────────────────────── */
QTableWidget {
    background:               #0F1624;
    alternate-background-color: #162030;
    gridline-color:           #1A2540;
    color:                    #D8E0EE;
    border:                   1px solid #1A2540;
    border-radius:            5px;
    selection-background-color: #0A1A35;
    selection-color:          #D8E0EE;
    outline:                  none;
}
QTableWidget::item          { padding: 0 12px; border: none; }
QTableWidget::item:selected { background: #0A1A35; }
QHeaderView::section {
    background:    #090E1A;
    color:         #7A8AAA;
    font-weight:   bold;
    font-size:     9pt;
    border:        none;
    border-bottom: 1px solid #243252;
    border-right:  1px solid #1A2540;
    padding:       0 12px;
    height:        36px;
}
QHeaderView::section:last-child { border-right: none; }
QTableWidget QTableCornerButton::section { background: #090E1A; }

/* ── QScrollBar ──────────────────────────────────────────── */
QScrollBar:vertical {
    background: #0F1624;
    width: 8px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #243252;
    border-radius: 4px;
    min-height: 32px;
}
QScrollBar::handle:vertical:hover { background: #3D4F6E; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #0F1624;
    height: 8px;
}
QScrollBar::handle:horizontal {
    background: #243252;
    border-radius: 4px;
    min-width: 32px;
}
QScrollBar::handle:horizontal:hover { background: #3D4F6E; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── QProgressBar ────────────────────────────────────────── */
QProgressBar {
    background:    #1C2A3E;
    border:        1px solid #1A2540;
    border-radius: 3px;
    height:        8px;
    text-align:    center;
    color:         transparent;
}
QProgressBar::chunk { background: #E8913A; border-radius: 3px; }

/* ── QStatusBar ──────────────────────────────────────────── */
QStatusBar {
    background: #070B14;
    color:      #7A8AAA;
    font-size:  9pt;
    border-top: 1px solid #1A2540;
    padding:    0 16px;
    min-height: 26px;
}
QStatusBar::item { border: none; }

/* ── QDialog ─────────────────────────────────────────────── */
QDialog {
    background: #162030;
    border:     1px solid #243252;
}
QDialog QLabel { color: #D8E0EE; }

/* ── QSplitter ───────────────────────────────────────────── */
QSplitter::handle         { background: #1A2540; }
QSplitter::handle:vertical { height: 1px; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:hover   { background: #3B7DD8; }

/* ── QToolTip ────────────────────────────────────────────── */
QToolTip {
    background: #162030;
    color:      #D8E0EE;
    border:     1px solid #243252;
    padding:    6px 10px;
    border-radius: 3px;
    font-size:  9pt;
}

/* ── QScrollArea ─────────────────────────────────────────── */
QScrollArea        { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }

/* ── QLabel variants ─────────────────────────────────────── */
QLabel#page_title {
    color:      #EAF0FF;
    font-size:  15pt;
    font-weight: bold;
}
QLabel#section_label {
    color:     #7A8AAA;
    font-size: 9pt;
    font-weight: bold;
}
QLabel#error_label { color: #EF7070; font-size: 9pt; }
QLabel#success_label { color: #5CCF78; font-size: 9pt; }
QLabel#amount_large {
    color:      #E8913A;
    font-size:  14pt;
    font-weight: bold;
}

/* ── QFrame separators ───────────────────────────────────── */
QFrame[frameShape="4"],   /* HLine */
QFrame[frameShape="5"] {  /* VLine */
    background:  #1A2540;
    border:      none;
    max-height:  1px;
}
```

---

## 8. DASHBOARD STAT CARDS

Each dashboard stat is a `QFrame` styled as a card:

```python
def make_stat_card(title: str, value: str, subtitle: str = "", accent: bool = False) -> QFrame:
    card = QFrame()
    card.setObjectName("stat_card")
    card.setStyleSheet("""
        QFrame#stat_card {
            background:    #162030;
            border:        1px solid #1A2540;
            border-radius: 5px;
            padding:       16px;
        }
    """)
    # Layout: title (9pt secondary) → value (16pt bold heading/saffron) → subtitle (9pt muted)
```

If `accent=True` (e.g., total outstanding balance), render the value in `ACCENT_SAFFRON` (`#E8913A`) at 16pt bold. Otherwise `TEXT_HEADING`.

Dashboard grid: `QGridLayout` with 3 columns, equal column widths, 16px gap.

---

## 9. FONT LOADING

```python
from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtWidgets import QApplication

def load_fonts(app: QApplication):
    for weight in ["Regular", "Bold", "Medium", "Light", "Italic", "BoldItalic"]:
        path = f"assets/fonts/JetBrainsMono-{weight}.ttf"
        QFontDatabase.addApplicationFont(path)
    app.setFont(QFont("JetBrains Mono", 10))
```

Bundle JetBrains Mono TTF files in `assets/fonts/`. Download from [jetbrains.com/lp/mono](https://www.jetbrains.com/lp/mono/) (OFL licence — free to bundle). Required files:
```
assets/fonts/
├── JetBrainsMono-Regular.ttf
├── JetBrainsMono-Bold.ttf
├── JetBrainsMono-Medium.ttf
├── JetBrainsMono-Italic.ttf
└── JetBrainsMono-BoldItalic.ttf
```

---

## 10. ICON CONVENTIONS

Use emoji as nav icons in the sidebar (they render at correct size with no asset required). For action icons inside the UI (edit, delete, download, refresh), use simple SVG files in `assets/icons/`. Provide fallback text labels on all icon-only buttons via `setToolTip()`.

Recommended SVG icons needed (create minimal single-colour SVGs or source from [Feather Icons](https://feathericons.com/) — MIT licence):
```
assets/icons/
├── edit.svg
├── delete.svg
├── download.svg
├── upload.svg
├── refresh.svg
├── print.svg
├── search.svg
├── chevron_down.svg
├── check.svg
├── x.svg
└── alert_triangle.svg
```

SVG fill colour: `#7A8AAA` (`TEXT_SECONDARY`). On hover, replace via QSS or swap icon programmatically.

---

## 11. ANIMATION & TRANSITIONS

PySide6 does not support CSS transitions. Use `QPropertyAnimation` only where it meaningfully aids comprehension:

- **QProgressBar** during bulk import: animate `value` property over 200ms
- **Sidebar active item change**: no animation — instant state switch is correct for a tool app
- **Loading overlays**: a simple `QLabel` with `"Loading…"` text shown over a `QStackedWidget` layer (no spinner animation required — keep it simple)

Do not add gratuitous animations. This is a billing instrument, not a consumer app.

---

## 12. ACCESSIBILITY NOTES

- All interactive elements must have `setToolTip()` set
- All required fields use the `" *"` label suffix in saffron
- Error messages appear as `QLabel#error_label` immediately below the offending field (not in a separate dialog)
- Minimum touch/click target: 30px height (already enforced by `min-height` in QSS)
- All monetary amounts use `₹` prefix and two decimal places — monospace alignment makes scanning natural
