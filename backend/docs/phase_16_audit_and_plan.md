# Phase 16: Architecture & Technical Debt Audit (Milestone 1)

## Current Architecture Assessment
1. **Multi-Tenancy (The Gap):**
   - The system currently has `Institution`, `Campus`, `Canteen`, and `Stall` in the database, but operational models (`Order`, `Product`, `Inventory`, `Supplier`) do not explicitly enforce an `institution_id` (tenant ID).
   - Authorization relies on a global `User.role`. This means a `CANTEEN_MANAGER` technically has system-wide manager privileges, violating tenant isolation rules.
2. **Configuration Hierarchy (The Gap):**
   - Configuration (like default currency, low stock thresholds) is currently hardcoded in environment variables or hard-coded defaults in the database.
   - We need a `Configuration` model that can resolve settings at Global -> Institution -> Canteen -> Stall levels.
3. **Observability (The Gap):**
   - We have simple text logs and a correlation ID (`X-Correlation-ID`).
   - We lack a robust DLQ (Dead Letter Queue) for the Outbox pattern and an incident correlation engine.

## Action Plan for Phase 16

### MILESTONE 2: Multi-Tenant Foundations
- **Database Schema Updates:** Denormalize `institution_id` onto core tables (`User`, `Order`, `GlobalProduct`, `Supplier`, `Alert`).
- **Authorization Refactoring:** Evolve `@require_role` to `@require_tenant_role` which cross-references `OrganizationMembership`.
- **Tenant Context:** Middleware to inject `current_tenant_id` into `flask.g` for implicit filtering.

### MILESTONE 3: Configuration Hierarchy
- Create a `Configuration` model.
- Build a resolution engine (`get_config('tax_rate', canteen_id=123)`).

### MILESTONE 4-6: Event Governance & Observability
- Add `version` and `tenant_id` to `OutboxEvent`.
- Build a DLQ interface and retry mechanism.
- Create `Incident` model for grouping repeated failures (e.g., 5 stockouts in 10 minutes = 1 Incident).

### MILESTONE 7+: Advanced Optimization
- Implement Multi-objective optimization for Inventory & Procurement.
- Implement Kitchen Batching intelligence.
- Implement Customer Queue/ETA prediction logic.

---
*Proceeding with Milestone 2: Multi-tenant foundations without breaking backward compatibility.*
