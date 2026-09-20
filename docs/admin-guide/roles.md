# 👥 User Roles & Permissions Matrix

`qibocal-report` implements a three-tier Role-Based Access Control (RBAC) model. Each role is designed for specific laboratory workflows while guaranteeing data integrity.

---

## 🎭 The Three Roles

### 1. 👁️ Viewer (Read-Only)
- **Target Audience**: External collaborators, students, visiting researchers, or dashboard displays.
- **Capabilities**:
  - View all calibration reports, figures, histograms, and statistics.
  - Inspect platform files (`parameters.json`, `calibration.json`).
  - Download full report packages, platform files, and protocol data as `.zip` archives.
  - Peek into archived report packages without unzipping.
  - Filter, search, and sort reports.
  - Read all documentation and guides.
- **Restrictions**:
  - **No modification rights**: Cannot add/remove tags, cannot edit author names, cannot delete reports, cannot regenerate plots, cannot create/restore/delete archives, and cannot change server directories.
  - **UI Enforcement**: All modification buttons and actions are visually disabled and greyed out with explanatory tooltips.
  - **API Enforcement**: All write endpoints reject Viewer requests with `403 Forbidden`.

---

### 2. ✏️ Editor (Read & Modify)
- **Target Audience**: Laboratory physicists, hardware calibration engineers, and active experimenters.
- **Capabilities**:
  - Includes all Viewer capabilities.
  - **Report Modifications**: Add and remove tags/labels from individual or bulk reports.
  - **Author Mapping**: Edit and normalize author metadata.
  - **Report Deletion**: Delete corrupted or superseded calibration runs.
  - **Plot Regeneration**: Trigger background plot re-evaluation and cache invalidation.
  - **Archive Operations**: Create consolidated zip archives, peak into archive contents, restore archived runs back to active views, and delete old archives.
  - **Directory Switching**: Switch active calibration directories via the folder browser.
- **Restrictions**:
  - Cannot access the Server Administration page (`#/server-admin`).
  - Cannot create, list, or revoke invitation tokens.
  - Cannot view or modify user accounts.

---

### 3. 👑 Admin (Full Control)
- **Target Audience**: Lab managers, principal investigators, and system administrators.
- **Capabilities**:
  - Includes all Editor capabilities.
  - **User Administration**: View all registered users across the server.
  - **Role Management**: Dynamically elevate or demote users between Viewer, Editor, and Admin roles.
  - **Account Deletion**: Delete user accounts when members leave the team.
  - **Invitation Generation**: Create invitation tokens with designated roles (`viewer`, `editor`, `admin`), custom expiration lifetimes, and usage limits.
  - **Token Revocation**: List all active invitations and instantly revoke tokens.
  - **Server Registration**: Register and manage global server configurations.

> [!CAUTION]
> The server enforces a safety constraint preventing the last remaining Administrator from being deleted or demoted. At least one active Admin must exist at all times.

---

## 📊 Detailed Permission Matrix

| Feature / Action | Viewer | Editor | Admin |
| :--- | :---: | :---: | :---: |
| **Browse Reports & Search** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Inspect Protocol Plots & Data** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Download Report & Platform ZIPs** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Print Publication-Ready PDF** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Read Documentation & Guides** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Tag & Untag Reports (Single & Bulk)** | ❌ *Disabled* | ✅ Yes | ✅ Yes |
| **Edit Report Author** | ❌ *Disabled* | ✅ Yes | ✅ Yes |
| **Regenerate Plots & Invalidate Cache** | ❌ *Disabled* | ✅ Yes | ✅ Yes |
| **Delete Calibration Reports** | ❌ *Disabled* | ✅ Yes | ✅ Yes |
| **Create Archive Packages** | ❌ *Disabled* | ✅ Yes | ✅ Yes |
| **Restore Archived Reports** | ❌ *Disabled* | ✅ Yes | ✅ Yes |
| **Delete Archives** | ❌ *Disabled* | ✅ Yes | ✅ Yes |
| **Switch Server Working Directory** | ❌ *Disabled* | ✅ Yes | ✅ Yes |
| **Access Server Administration Page** | ❌ *Forbidden* | ❌ *Forbidden* | ✅ Yes |
| **Generate Invitation Tokens** | ❌ *Forbidden* | ❌ *Forbidden* | ✅ Yes |
| **Revoke Invitation Tokens** | ❌ *Forbidden* | ❌ *Forbidden* | ✅ Yes |
| **Assign & Change User Roles** | ❌ *Forbidden* | ❌ *Forbidden* | ✅ Yes |
| **Delete User Accounts** | ❌ *Forbidden* | ❌ *Forbidden* | ✅ Yes |
