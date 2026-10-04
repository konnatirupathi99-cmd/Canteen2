# Architecture Decision Records

## ADR-001: Why PostgreSQL?
**Decision:** PostgreSQL is selected because the project requires transactional consistency and concurrency-safe inventory operations.

## ADR-002: Why Modular Monolith?
**Decision:** A modular monolith is preferred for hackathon speed and operational simplicity while retaining clear internal boundaries.

## ADR-003: Why WebSockets?
**Decision:** WebSockets provide low-latency bidirectional communication required for live inventory/order synchronization across multiple roles (cashier, kitchen, customer).
