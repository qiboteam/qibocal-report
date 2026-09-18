# Developer: Design System & Aesthetics

`qibocal-report` implements a modern, editorial aesthetic inspired by *BackMarket* design principles, favoring spacious layouts, subtle monochromatic purple accents, and warm typography over generic enterprise dashboard designs.

---

## 🎨 Color Palette

| Role | Color Hex | Class / Usage | Description |
| :--- | :--- | :--- | :--- |
| **Main Background** | `#f7f7f7` | `bg-[#f7f7f7]` | Very pale, warm gray background across all views. |
| **Card Background** | `#ffffff` | `bg-white` | Crisp pure white background for cards, tables, and buttons. |
| **Primary Accent** | `#833dff` | `text-[#833dff]`, `bg-[#833dff]` | Distinctive purple used for active states, primary buttons, and highlights. |
| **Mild Accent** | `#c8a8ff` | `border-purple-300`, `accentMild` | Subtle borders, focus rings, and secondary badge outlines. |
| **Light Accent** | `#ebe0ff` | `bg-[#ebe0ff]`, `accentLight` | Soft tint used for active sidebar items and badge backgrounds. |
| **Base Text** | `#111827` / `#000` | `text-gray-900`, `text-black` | High-contrast body text. |
| **Subtle Muted** | `#4a4a4a` / `#6b7280` | `text-gray-500`, `note` | Metadata labels, timestamps, and secondary captions. |

---

## 🔤 Typography

- **Headings (`h1`)**: Editorial serif typeface (Georgia, Cambria, Times New Roman) delivering a distinguished research-journal presence.
- **Headings (`h2`, `h3`) & Body**: Crisp, geometric sans-serif (Inter, system sans-serif) for high legibility across dense data tables and charts.
- **Chips, Badges & Code**: Monospace font (`font-mono`) for qubit numbers, commit hashes, timing durations, and JSON keys.

---

## 🔲 Card Elevation & Borders

- **Cards (`.bm-card`)**: Built with subtle, multi-layered shadows (`shadow-2xs`, `shadow-xs`) with rounded corners (`rounded-2xl`).
- **Borders**: Thin, soft border lines (`border-gray-200` or `border-gray-100`) rather than heavy stark dividing lines.

---

## 🖨️ Print Media Styles (`@media print`)

Located in `frontend/src/assets/style.css`, print styles guarantee that printing from the browser produces clean, publication-grade output:

- **Isolated Content**: Sidebar navigation, search inputs, pagination controls, and action buttons are assigned `display: none !important;`.
- **Page Breaks**: Protocol cards specify `break-inside: avoid;` and `page-break-inside: avoid;` to keep individual routines cohesive.
- **Plotly Responsiveness**: Chart containers expand to the full page width while retaining high raster clarity.
