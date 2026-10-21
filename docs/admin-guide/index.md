# 🛡️ Server Administration & Security Guide

This guide covers everything system administrators need to know to secure, configure, and manage a `qibocal-report` instance in multi-user quantum laboratory environments.

---

## 🔒 Authentication Overview

By default, `qibocal-report` starts in **open/single-user mode** for frictionless local developer workflows. In lab environments with shared servers or network deployments, you can enable **Role-Based Access Control (RBAC)** to enforce user authentication and split privileges across three distinct roles:

- **Viewer**: Read-only access. Ideal for external collaborators, students, or dashboard monitors who should view calibration plots and download artifacts without modifying reports.
- **Editor**: Full read-and-write permissions on reports and archives. Ideal for experimental physicists who tag runs, edit authors, regenerate plots, and archive runs.
- **Admin**: Full control over server configuration, user accounts, role assignments, and invitation token lifecycles.

---

## 🚀 Starting the Server with Authentication

To enable authentication on your report server, pass the `--auth` flag when starting the CLI:

```bash
# Production server mode with authentication enabled
qibocal report server /path/to/reports --auth --host 0.0.0.0 --port 8000

# Development mode with authentication enabled
qibocal report dev /path/to/reports --auth --port 8000
```

Alternatively, you can set the environment variable:

```bash
export QIBOCAL_AUTH_ENABLED=1
qibocal report server /path/to/reports
```

When started with `--auth`, the server:
1. Enforces JSON Web Token (JWT) bearer authentication on all data-access and modification endpoints.
2. Rejects unauthenticated requests with `401 Unauthorized`.
3. Rejects requests lacking required permissions with `403 Forbidden`.
4. Leaves public documentation endpoints (`/api/docs-nav`, `/api/docs-content/*`) open to everyone without requiring login.

### Connecting and changing accounts

Click a registered server on `/servers` to connect. The interface checks its current
authentication mode: an authenticated server prompts for sign-in when needed and
applies the signed-in user's role; an open server grants full access without a
login. Restarting a server with or without `--auth` does not require registering it
again.

To change accounts, choose **Log out** in the server card's three-dots menu, or below
**Documentation** in the shared sidebar. This removes the saved session for that
server only. Click the server again to sign in as a different user.

---

## 🔑 Initial Setup: The First Administrator

When a server starts with `--auth` for the first time and no users exist in the database, `qibocal-report` **automatically generates a secure initial Admin Invitation**:

```text
╭──────────────────────── ⚛️  Qibocal Report Server ────────────────────────╮
│ 📁 Reports Directory : /path/to/reports                                   │
│ ⚙️  FastAPI Server   : http://0.0.0.0:8000                                │
│ 📖 REST API Docs     : http://0.0.0.0:8000/api/docs/swagger               │
│ 🖥️  Dashboard        : https://qibo.science/qibocal-report                │
│ 🔒 Auth & Roles       : Enabled                                           │
│ 🔑 Admin Invite Link  : https://qibo.science/qibocal-report/#/invite?     │
│    token=adm_a8f10b89e...&server=http%3A%2F%2F0.0.0.0%3A8000             │
│                                                                           │
│ The server has no page of its own: add its address in the dashboard,      │
│ or in the Qibocal desktop application. Press Ctrl+C to stop the server.   │
╰───────────────────────────────────────────────────────────────────────────╯
```

The link opens the deployed dashboard — `QIBOCAL_DASHBOARD_URL` names another one — and tells it the server's address. A server bound to `0.0.0.0` is announced as such: regenerate the link with `qibocal report admin invite --server-url` and the address the browser reaches it at, if that one does not work from there.

### Steps to Bootstrap:
1. Copy the setup link printed in the terminal.
2. Open the link in your web browser.
3. Choose a username and password.
4. Click **Complete Registration**. You are immediately authenticated as the primary **Admin**.

> [!NOTE]
> The initial setup token is single-use and valid for 30 days. Once used to register the initial administrator, it is automatically revoked.

---

## 🖥️ Server Administration Dashboard

Once authenticated as an Admin, access the dedicated administration page by navigating to:
- **Server Administration** in the left sidebar navigation.
- **Server Administration** button in the top navigation bar of the Server Management page (`#/servers`).
- Direct URL: `#/server-admin`.

The Server Administration dashboard provides three main panels:
1. **User Roles & Access Control**: View all registered users, dynamically change their roles via dropdown (`Viewer`, `Editor`, `Admin`), or delete user accounts.
2. **Invitation Tokens Generator & Manager**: Generate new invitation tokens with specific roles, configurable expirations, and usage limits. Instantly copy invite links or revoke active tokens.
3. **Server Configuration**: Summary of the reports directory, authentication status, total active runs, registered users, and active tokens.

---

## 📤 Uploads from other servers

Reports can be uploaded to a server from another one, through the dashboard. With authentication on, the **Uploads** card of Server Administration says who may: administrators always, and, as chosen, editors too, every signed-in user, or selected individuals. The choice is kept in `auth.json`, next to the users. Without authentication, the server accepts uploads from anyone who reaches it. From a browser, either way, only the pages of the dashboard, the desktop application and this machine may change anything — further origins are listed in `QIBOCAL_ALLOWED_ORIGINS`; any other page is answered `403`.

## 💾 Storage & Cryptography Architecture

- **Password Hashing**: Passwords are encrypted using **PBKDF2-HMAC-SHA256** with 100,000 iterations and unique 16-byte random salts per user. Raw passwords are never stored.
- **JWT Tokens**: Authenticated sessions issue signed JSON Web Tokens (HS256) valid for 7 days.
- **Persistence**: User credentials, roles, and invitation tokens are persisted in `auth.json` inside the server configuration directory (`$XDG_CONFIG_HOME/qibocal/`, falling back to `$HOME/.config/qibocal/`). `$QIBOCAL_REPORT_CONFIG_DIR` overrides this directory; `$QIBOCAL_AUTH_FILE` can override the authentication file separately.
