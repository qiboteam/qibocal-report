# User Guide: Dashboard & Server Management

The `qibocal-report` dashboard provides a centralized management hub for exploring calibration history, filtering runs across multiple criteria, and managing distributed measurement servers.

---

## 📡 Multi-Server Management

Access the server registry via the **Servers** tab (`/#/servers`) in the top navigation or sidebar:

- **Connect New Servers**: Paste the URL of any running `qibocal report server` instance into the input bar and press Enter.
- **Names and Avatars**: Each server is assigned a name and an abstract geometric avatar, which you can customize.
- **Customization**: Use the three-dots menu on any server card to update its name, description, avatar, or target address.
- **Authentication Status**: Auth-enabled servers display a lock to the left of their name: closed when signed out, open when signed in. Open/no-auth servers have no lock and no **Administer** entry in their three-dots menu.
- **Default Server**: Set any server as the default active instance so the dashboard automatically opens to it.
- **Browser-Local Registry**: Registration, customization, deletion, and card ordering are saved automatically in this browser, whether the client is hosted by a report server or deployed standalone. They do not modify a report server's `servers.json`. Deleting a card does not delete reports or stop the server.
- **Save Client State**: Download a JSON backup of the server list and ordering, active server, report history, search filters and pagination, sidebar preferences, and remembered table/sidebar dimensions.
- **Load Client State**: Select a previously saved JSON file and confirm replacement of this browser's settings. Invalid files are rejected without changing settings. Loading clears current sign-in sessions; passwords and authentication tokens are never included in backups. Authenticated servers require signing in again. Live report data, connection status, and open dialogs are not backed up.

---

## 🔍 Instant Search & Smart Facets

The dashboard provides rich search and faceted filtering:

- **Full-Text Search Bar**: Search dynamically across report titles, platform names, author handles, executed protocols, and custom tags.
- **Author Filtering**: Filter runs by specific calibration scientists.
- **Frequency-Ranked Protocols**: Select protocols from a list ranked in descending order of execution count.
- **Interactive Date Histogram**: A timeline bar chart visualizing calibration activity across time. Click any bucket or drag a date range to filter.
- **Tag / Label Filtering**: Filter reports by custom tags assigned to them.
- **Active Filter Summary**: A clear banner summarizing all applied filters with one-click clear options.

---

## 📊 Dual Display Modes: Table vs. Card View

Toggle between two optimized display styles using the view switcher:

1. **Table View**:
   - Compact and dense view displaying Platform, Title, Author, Date, Duration, and Tags in columns.
   - Click column headers to sort ascending or descending.
   - Resize columns by dragging table column borders.
   - Quick action menus per row (Copy ID, Edit Author, Add Tag, Delete).

2. **Card View**:
   - Rich Inspire-HEP inspired cards providing full-width context for each calibration run.
   - Highlights platform badges, executed protocol chips, qubit counts, and execution timestamps at a glance.

---

## 📈 Statistics View

Navigate to **Statistics** (`/#/statistics`) from the sidebar:

- **Run Totals**: Total calibration runs, platforms tested, and routine executions.
- **Activity Over Time**: Chronological distribution chart displaying throughput and calibration runs per day/week.
- **Protocol Frequency Breakdown**: Bar charts displaying the most frequently calibrated protocols.
- **Platform Breakdown**: Distribution of runs across hardware chips and platforms.
- **Author Leaderboard**: Distribution of calibration activity by researcher.

---

## ⚡ Bulk Actions

Manage multiple reports simultaneously directly from the dashboard:

1. Use the row checkboxes in Table View to select reports.
2. An action bar appears at the bottom of the screen:
   - **Tag Selected**: Add tags or labels to all selected runs at once.
   - **Assign Author**: Batch update the author field for selected reports.
   - **Delete Selected**: Safely remove unwanted calibration runs from the server disk with confirmation.
