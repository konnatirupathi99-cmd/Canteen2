# Operations Runbook and Disaster Recovery

## 1. System Components
- Canteen Backend (Flask, SQLAlchemy, SocketIO)
- Database (SQLite / PostgreSQL in prod)
- Event Bus (SocketIO)

## 2. Health Monitoring
- Liveness Probe: `GET /api/v1/health/live`
- Readiness Probe: `GET /api/v1/health/ready` (checks DB and Event Bus connectivity)
- Logs: Check stdout for correlation IDs (`[X-Correlation-ID]`).

## 3. Disaster Recovery Procedures

### 3.1 Database Connection Failure
- **Symptom**: `GET /api/v1/health/ready` returns 500, Database status `error`.
- **Action**: 
    1. Check if the database process is running.
    2. Verify `DATABASE_URL` credentials.
    3. If transient, the idempotency mechanisms will prevent duplicate orders on retry.

### 3.2 WebSocket Event Sync Failure
- **Symptom**: KDS not updating, inventory not syncing on clients.
- **Action**:
    1. Verify SocketIO connection in frontend console.
    2. When KDS reconnects, it automatically fires `request_kds_state` to sync missed orders.
    3. The Outbox table (`outbox_events`) holds transactional events. A background worker can be spawned to replay failed events if necessary.

### 3.3 Rate Limiting / High Traffic
- **Symptom**: 429 Too Many Requests.
- **Action**:
    - Application is protected by idempotency keys to prevent double-charging during high-concurrency "Last Item" checkout races.

## 4. Maintenance
- Run `python seed.py` to reset the database (DEVELOPMENT ONLY).
- Regularly backup the SQLite `.db` file or PostgreSQL database.
