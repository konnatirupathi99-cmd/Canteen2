# Authentication & Authorization Architecture

## Authentication Strategy (Token/Session)
For this MVP, we will use **JWT (JSON Web Tokens)** for stateless authentication.
- **Access Tokens:** Short-lived JWTs (e.g., 30-60 minutes) containing minimal claims (`sub` = user_id, `role`).
- **Storage:** To mitigate XSS, we will return the token in an HttpOnly cookie (or alternatively, instruct the frontend to manage it securely in memory while leaning on local storage for persistence if cookies are complex to setup cross-origin in the hackathon constraints). For simplicity in the hackathon while retaining security, standard HTTP Authorization headers (`Bearer <token>`) will be used, and the frontend will store it.
- **Expiration:** Tokens naturally expire. The backend validates the signature and expiration on every protected request.
- **Logout:** Handled by deleting the token on the client-side. We can implement a server-side token blocklist if immediate revocation is required, though for MVP simply expiring them is often sufficient.

## Frontend vs Backend Responsibilities

### Backend (The Authority)
- **Authentication:** Verifies email/password against the `password_hash` in the database. Checks if `status == ACTIVE`. Issues JWT.
- **Authorization:** Uses decorators (e.g., `@require_role('ADMIN')` or `@require_permission('PRODUCT_CREATE')`) to intercept requests.
- **Enforcement:** Reads the JWT, verifies the signature, extracts the role, and explicitly allows or denies (401/403) the action.

### Frontend (The UX Layer)
- **State Management:** Uses React Context (`AuthContext`) to track the current user and role.
- **Navigation:** Hides links and redirects users away from unauthorized routes (e.g., Cashier is redirected away from `/admin`).
- **Error Handling:** If an API call returns 401, it logs the user out and redirects to `/login`. If it returns 403, it shows an "Access Denied" message.
- **Rule:** The frontend **NEVER** trusts itself for security. It only adapts the UI for convenience.

## Role-Permission Matrix

| Resource / Action | ADMIN | CANTEEN_MANAGER | CASHIER | KITCHEN_STAFF |
| :--- | :--- | :--- | :--- | :--- |
| **Users** | CREATE, READ, UPDATE | READ (limited) | READ (self) | READ (self) |
| **Products** | FULL | FULL | READ | READ (assigned items) |
| **Categories** | FULL | FULL | READ | READ |
| **Stalls** | FULL | FULL | READ | READ |
| **Inventory** | FULL | FULL | READ | READ (limited) |
| **Orders** | READ | READ | CREATE, READ | READ, UPDATE (status) |
| **Audit Logs** | READ | NONE | NONE | NONE |

## WebSocket Authentication (Future-Proofing)
In Phase 4/5, WebSockets will require authentication to prevent unauthorized eavesdropping.
- When a client connects via `socket.io-client`, they will pass the JWT token in the connection payload (e.g., `auth: { token: "..." }`).
- The backend `connect` event handler will verify the JWT.
- If valid, the user is mapped to their `sid` (Socket ID) and placed into role-specific or stall-specific rooms (e.g., `room:stall_1_kitchen`).
- If invalid, the connection is forcibly disconnected.
- This ensures only authorized users receive sensitive real-time broadcasts.
