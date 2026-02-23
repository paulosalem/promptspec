## Frontend: Dashboard & Data Visualization

### Dashboard Layout
- Responsive grid: 1 column on mobile, 2 on tablet, 3–4 on desktop.
- Each widget is a self-contained card with: title bar, content area, optional action menu.
- Widgets MUST support a loading skeleton state and an error state with retry button.
- Drag-to-reorder and show/hide widgets (persisted to user preferences).

### Charts & Graphs
- Use a lightweight charting library (e.g., Chart.js, Recharts, or Plotly).
- Required chart types:
  - **Line chart**: time series data (e.g., balance over time) with zoom/pan.
  - **Bar chart**: categorical comparisons (e.g., spending by category).
  - **Donut/pie chart**: proportional breakdowns (e.g., expense distribution).
  - **Sparkline**: compact inline trend indicator for widgets.
- All charts MUST support: dark/light theme, responsive resize, accessible color palettes,
  tooltip on hover with formatted values, and export as PNG.

### Data Tables
- Sortable columns (click header to toggle asc/desc, shift-click for multi-sort).
- Filterable: text search + dropdown filters per column.
- Paginated: 10/25/50/100 rows per page, with total count.
- Row actions: edit, delete (with confirmation modal), view detail.
- Bulk actions: select-all checkbox, bulk delete, bulk export.
- Empty state: illustration + "No data yet" message + CTA button.

### Date Ranges
- Global date range picker: preset ranges (This Month, Last 30 Days, This Year, Custom).
- Date range selection applies to all dashboard widgets and data tables simultaneously.
- Custom range: calendar picker with min/max date constraints.
- Display format: user-locale-aware (e.g., MM/DD/YYYY for US, DD/MM/YYYY for EU).
