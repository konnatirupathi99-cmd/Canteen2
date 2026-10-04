# Phase 22: Resilience, High Availability & Disaster Recovery

## Architecture Decision Records (ADRs)

### ADR 1: Event Delivery and Processing
**Decision:** Implement Transactional Outbox pattern with At-Least-Once delivery.
**Rationale:** Directly emitting Socket.io events during a web request is unsafe because if the database transaction rolls back, the event is still sent. The outbox pattern decouples business logic from event publishing. Background workers (`outbox_processor.py`) pick up unhandled events and dispatch them safely, using a `processed` flag.

### ADR 2: Payment Circuit Breaker and Idempotency
**Decision:** Integrate Circuit Breaker for external payment calls and accept `idempotency_key`.
**Rationale:** Payment gateways can degrade or fail. A Circuit Breaker prevents cascading failure by fast-failing. If the gateway fails or is half-open, the order is created with `PAYMENT_PENDING` and a `Payment` entity is marked `UNKNOWN` or `FAILED`. The background worker (`reconciliation.py`) reconciles the true state later without blocking the POS.

### ADR 3: Database Concurrency and Isolation
**Decision:** Continue authoritative database reservations for inventory.
**Rationale:** Inventory MUST NOT go negative. We lock rows atomically (`UPDATE ... RETURNING`) and fail the request if stock is insufficient. We do not sacrifice transactional correctness for availability.

## Operational Runbooks

### Runbook 1: External Payment Provider Outage
**Symptom:** `CircuitBreakerOpenException` is firing. Payments are stuck in `UNKNOWN` or `PENDING`.
**Action:**
1. Do NOT manually update database states.
2. The `PaymentCircuitBreaker` will automatically trip and fast-fail incoming requests. Orders will gracefully degrade to `PAYMENT_PENDING` (Offline mode).
3. Once the provider recovers, the `reconciliation.py` worker will query the provider and either update the order to `CONFIRMED` or `PAYMENT_FAILED` (and automatically restock the inventory).

### Runbook 2: Event Broker (Socket.io) Unavailability
**Symptom:** Real-time updates to KDS are failing.
**Action:**
1. Do nothing directly to the core application; checkout will continue processing via the Outbox.
2. Restart the Socket.io/Event service instance.
3. The `outbox_processor.py` will retry sending unprocessed events. The KDS should be designed to pull its initial state on reconnect to avoid missed events.

### Runbook 3: High Latency / Database Exhaustion
**Symptom:** API requests are hanging and returning 500s.
**Action:**
1. We have configured `pool_timeout=10` in SQLAlchemy. If the DB is saturated, connections will fail fast rather than hanging the web server indefinitely.
2. Autoscaling should scale out the API instances to handle connection queues. 
3. Consider load-shedding low-priority requests (Analytics/AI).

## SLA / RPO / RTO
* **RPO (Recovery Point Objective):** 0 for authoritative transactions (Orders/Payments/Inventory). Database replication should be synchronous for these paths.
* **RTO (Recovery Time Objective):** < 5 minutes for core POS API. KDS and reporting can withstand longer RTOs.
