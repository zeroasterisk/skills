# Mandatory Secure Web Coding Rules

This document defines mandatory secure coding rules for web applications to prevent critical vulnerabilities (SQL injection, XSS, CSRF, insecure session management, path traversal, etc.).

---

## 1. Secure Coding Guidelines

*   **Input Validation & Sanitization:** Treat all external data as untrusted. Validate inputs against an allow-list of expected types, lengths, and formats to prevent SQL injection and cross-site scripting (XSS).
*   **Output Encoding:** Convert data into a safe format before sending it to the client. This ensures that browsers treat potentially malicious scripts as plain text rather than executable code.
*   **Authentication & Authorization:** Require strong authentication for non-public pages. Use modern protocols like OAuth 2.0 or OpenID Connect to verify users, and JSON Web Tokens (JWT) for secure, stateless session management. Never hardcode JWT secrets or API keys in source code.
*   **Password Management:** Use established libraries for password hashing (e.g., Argon2 or bcrypt) with unique salts, and never store passwords in plaintext.
*   **Principle of Least Privilege:** Grant users and processes only the minimum permissions necessary to perform their functions. Use Role-Based Access Control (RBAC) to manage these permissions centrally.
*   **Secure Session Management:** Generate cryptographically strong, random session identifiers on the server. Protect these tokens by using the `HttpOnly`, `Secure`, and `SameSite` flags on cookies and enforcing short inactivity timeouts.
*   **Secure Architecture (BFF Pattern):** Use a Backend-for-Frontend (BFF) to allow the frontend to communicate with a secure, server-side BFF layer rather than directly with public APIs, keeping sensitive keys off the client.
*   **Path & File System Security:** Never trust user input (including uploaded filenames and extracted file metadata like ID3 tags/formats) in file paths. Sanitize inputs (e.g., using `path.basename()`) to strip traversal sequences (`../`, `..\`) before passing them to file system sinks. Avoid custom sanitization like `split('/')` which fails against Windows backslashes. When restricting access to specific directories, resolve paths fully and strictly verify the directory boundary (e.g., enforce a trailing slash when using prefix checks) to prevent partial matching bypasses.
*   **System Command Execution:** Do not pass unvalidated user input directly to execution sinks (`exec`, `spawn`, etc.). Always validate binary paths and arguments against a strict, hardcoded allow-list. Ensure execution directories are also strictly verified against partial matching bypasses.
*   **Error Handling & Logging:** Display generic error messages to users while logging detailed diagnostic information securely for developers. Ensure logs do not contain sensitive data like passwords or session tokens.
*   **Data Encryption:** Encrypt sensitive data both at rest and in transit (using TLS 1.2 or higher).
*   **Fail Safe:** When something fails, fail close (deny access).
*   **Cryptography:** Use established libraries and secure primitives. Use authenticated encryption and secure cryptographic hashes. Use secure PRNGs from the OS.

---

## 2. Secure Web Frontend (XSS Prevention)

### Framework-Native Escaping
*   **Do not trust** data from databases, configuration files, uploaded files, or user requests that the user may control directly or indirectly.
*   **Escape or validate** untrusted data in all outgoing HTML, JavaScript, CSS, and HTTP headers.
*   **Rely on framework-native auto-escaping** (e.g., React JSX, Angular interpolation).
*   **Always quote HTML attributes** when using variables in templates to prevent attribute breakout.
    *   *Vulnerable:* `<div class={{ var }}>`
    *   *Secure:* `<div class="{{ var }}">`
*   **Do not use unsafe methods** like React's `dangerouslySetInnerHTML` or Angular's `bypassSecurityTrustHtml` without rigorous justification and sanitization.
*   **Use `DOMPurify`** when rendering raw HTML string inputs that are unavoidable (e.g., from rich text editors).

#### Examples
*   **Vulnerable (React):** `<div dangerouslySetInnerHTML={{ __html: userInput }} />`
*   **Secure (React with DOMPurify):** `<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />`

### Vanilla JavaScript DOM Manipulation
*   **Do not use** unsafe DOM properties/methods like `innerHTML`, `outerHTML`, `document.write`, or `insertAdjacentHTML`.
*   **Use `textContent` or `innerText`** to safely insert text.
*   **Use `document.createElement()`, `setAttribute()`, and `appendChild()`** to build structural DOM elements instead of raw HTML strings.
*   **Use `element.replaceChildren()`** or `element.textContent = ''` to clear an element's content instead of `element.innerHTML = ''`.
*   **Use `DOMParser`** to safely parse and insert complex static structures (like SVGs) to completely avoid `innerHTML` assignments, even for strictly hardcoded strings.

#### Examples
*   **Vulnerable (Vanilla JS):** `element.innerHTML = "<span>" + userInput + "</span>";`
*   **Secure (Vanilla JS):**
    ```javascript
    const span = document.createElement('span');
    span.textContent = userInput;
    element.appendChild(span);
    ```
*   **Secure (Clearing Elements):** `element.replaceChildren();`

---

## 3. Storage & Session

### Sensitive Data Storage
*   **Do not store** sensitive authentication tokens (Session IDs, Bearer tokens) in `localStorage` or `sessionStorage` due to XSS vulnerability exposure.
*   **Rely on secure cookies** (`HttpOnly`, `Secure`, `SameSite=Lax` or `Strict`) for session management.

### Session Lifecycle
*   **Clear client-side state** (e.g., Redux, Context, local variables) on logout.
*   **Trigger a full page reload** or redirect to clear cache on logout.

---

## 4. Frontend Configuration

### Content Security Policy (CSP)
*   **Implement a strict Content Security Policy (CSP)** to mitigate XSS risks.
*   **Use nonces** for inline scripts or strictly limit `script-src` to trusted origins.
*   **Do not use** `unsafe-inline` or `unsafe-eval` in CSP without explicit security review.
    *   *Secure Header Example:* `Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-random123'; object-src 'none';`

### Subresource Integrity (SRI)
*   **Use Subresource Integrity (SRI) hashes** when loading assets from non-first-party CDNs. Prefer a package manager over a CDN for dependencies when possible.

### Clickjacking Protection
*   **Configure anti-clickjacking guards** using `X-Frame-Options: DENY` (or `SAMEORIGIN`) and CSP `frame-ancestors`.

---

## 5. Data Handling & UI

### PII Masking
*   **Do not surface full PII** (e.g., SSN, Email, Credit card numbers) directly in UI labels.
*   **Apply masking** on safe text renders (e.g., `***-***-1234`).

### Logging & UI Interaction
*   **Do not print** structured user objects or tokens using `console.log` or error stack traces.
*   **Do not use** native `alert()`, `confirm()`, or `prompt()` dialogues in production code. Rely on framework-native modal components.

---

## 6. Secure Web Backend (Session & Auth)

### Password Security
*   **Enforce strong user passwords:** Minimum 8 characters (12+ recommended), no maximum length, and allow all characters.
*   **Store credentials** using memory-hard hashing (e.g., Argon2, bcrypt, or scrypt) with unique per-user salts.
*   **Implement CSRF tokens** if authentication is based on cookies for all state-changing requests (POST, PUT, DELETE, PATCH).
*   **Do not send credentials** in URL parameters.
*   **Do not log credentials** server-side, even for failed login attempts.

### Session Management
*   **Use the web framework's built-in support** for session management if available.
*   **Set expiration periods** for sessions. Do not use infinite sessions.
*   **Invalidate all sessions** when logging a user out, when an account is deactivated, or when a user is removed from an organization.

### Authentication & JWT
*   When using JWT:
    *   Reject the `none` algorithm.
    *   Hardcode the expected algorithm for verification; never derive it from the unverified token header.
    *   Set the `exp` (expiration) claim and validate it.
*   **Do not store secrets** (e.g., API keys, JWT secrets) in code. Use environment variables or secret managers. Fall back to a securely generated random value in test environments and log a warning.

---

## 7. Database Security & SQLi Prevention

*   **Do not use string concatenation** to build SQL queries.
*   **Use parameterized queries**, prepared statements, or ORMs.
    *   *Vulnerable:* `db.query("SELECT * FROM users WHERE id = " + req.body.id);`
    *   *Secure (Parameterized):* `db.execute("SELECT * FROM users WHERE id = ?", [req.body.id]);`
    *   *Secure (ORM):* `db.users.find({ where: { id: req.body.id } });`
*   **Do not trust user strings** retrieved from databases; escape and validate them before rendering.
*   **Database Configuration (Least Privilege):**
    *   Ensure the application's database user only has the permissions it strictly needs (e.g., `SELECT`, `INSERT`, `UPDATE`).
    *   Do not use `root` or `admin` accounts for your web application.
    *   Isolate databases per application.

---

## 8. File Upload Security

*   **Validate the extension and content:** Use server-side libraries to inspect the file content (magic bytes) to confirm the file is what it claims to be.
*   **Use an allow-list:** Only permit specific file types required (e.g., PDF and PNG).
*   **Impose size limits** (e.g., 1MB–10MB) to prevent DoS attacks.
*   **Generate unique filenames:** Rename every uploaded file to an unpredictable random string (e.g., UUID) on the server.
*   **Store outside the web root:** Save files in a directory not directly accessible by a URL. Serve them via authorized endpoints.
*   **Serve with correct headers:**
    *   `Content-Disposition: attachment` (forces download)
    *   `X-Content-Type-Options: nosniff`
    *   `Content-Type` matching the actual verified file type.
*   **XML Parsing Hardening:** If you support XML-based uploads (DOCX, SVG, PDF), disable external entity expansion (XXE) and DTD processing.
