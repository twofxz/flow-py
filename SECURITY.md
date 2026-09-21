# Security Policy

## Supported Versions

Only the latest release receives security fixes and maintenance updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

If you discover a potential security vulnerability in `google-flow-api`:

1. **DO NOT** create a public GitHub issue.
2. Email the maintainers directly or use GitHub Private Vulnerability Reporting.
3. Provide detailed steps, reproduction script, and affected environments.
4. Allow reasonable time for remediation before any public disclosure.

---

## Credential Security & Threat Model

`google-flow-api` automates interactions with the Google Flow web canvas using an isolated, persistent local Chromium instance. It stores authentication state locally on your machine.

### Local Storage Layout

By default, persistent session state and runtime caches are stored in the user's home directory under `~/.google-flow/`:

| Path | Contents | Recommended Permissions |
| :--- | :--- | :--- |
| `~/.google-flow/chrome_profile/` | Default persistent Playwright/Chromium session profile | `0o700` (owner-only directory) |
| `~/.google-flow/profiles/<session>/` | Multi-agent isolated profiles (e.g. `--session agent-1`) | `0o700` (owner-only directory) |
| `~/.google-flow/active_project_*.json` | Cached active project UUID and metadata | `0o600` (owner-only file) |

> **Note on Windows vs POSIX**:
> On Linux and macOS, permissions are strictly checked or set to `0600`/`0700`. On Windows, the storage relies on the current user's inherited filesystem Access Control Lists (ACLs).

---

### Bearer Token & Session Protection

1. **Protect Your Profile Directory**:
   - The directory `~/.google-flow/` contains live Google authentication cookies and local storage states.
   - Anyone with read access to this folder can execute requests authenticated as your Google account within Google Flow.
   - **Never** commit, publish, or share files from `~/.google-flow/`.

2. **Git Hygiene**:
   Ensure `~/.google-flow/` or any local profile folders are in your `.gitignore`:
   ```gitignore
   .google-flow/
   chrome_profile/
   *.session
   active_project*.json
   ```

3. **Session Rotation & Revocation**:
   - Google Flow web sessions typically persist for days or weeks.
   - If you suspect a session leak, immediately visit [Google Account Security](https://myaccount.google.com/device-activity) and sign out of the active session.
   - Run `google-flow stop` and delete the `~/.google-flow/` directory locally before re-authenticating with `google-flow login`.

---

### CI/CD and Headless Environments

- **Do not commit raw profile directories to CI repositories.**
- For headless agent runners and automated pipelines, mount credentials securely into `~/.google-flow/` using encrypted secret stores or container volumes with restricted access (`chmod 700`).
- Always run `google-flow auth-check --json` in preflight scripts to ensure the session is valid before starting media generation jobs.

---

### What This Library Does NOT Do

- **No Third-Party Telemetry**: This library contains zero tracking scripts, telemetry, or external API relays. All network communications occur strictly between your local Chromium instance and official Google domains (`flow.google.com`, `accounts.google.com`).
- **No Password Interception**: The library never prompts for, reads, or stores your Google account password. Initial authentication is performed interactively via the official Google login flow.
- **Strict Scope**: The automation engine only accesses the Google Flow canvas and does not read or manipulate any other Google services (Gmail, Drive, Photos, etc.).
