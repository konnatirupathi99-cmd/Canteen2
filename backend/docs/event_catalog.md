# Event Catalog

This document formalized the event schemas used in the Canteen Management Ecosystem as of Phase 16. 
All events are stored via the Outbox pattern (`OutboxEvent`) and dispatched to subscribers (e.g. Webhooks) and internal consumers.

## Core Schema Structure
All events adhere to the following schema:
```json
{
  "event_id": "uuid",
  "event_type": "string",
  "version": "v1",
  "timestamp": "ISO-8601",
  "producer": "string",
  "correlation_id": "string",
  "payload": { ... }
}
```

## Supported Events

### 1. `ORDER_CREATED`
- **Producer**: `order_service`
- **Consumers**: `kds_service`, `analytics_service`, `inventory_service`
- **Payload**:
  - `order_id`: Integer
  - `order_number`: String
  - `total`: Float
  - `canteen_id`: Integer
- **Idempotency Requirements**: Orders must be deduplicated via `X-Idempotency-Key`.

### 2. `ORDER_FULFILLED`
- **Producer**: `kds_service`
- **Consumers**: `analytics_service`, `customer_notification_service`
- **Payload**:
  - `order_id`: Integer
  - `stall_id`: Integer

### 3. `INVENTORY_LOW`
- **Producer**: `inventory_service`
- **Consumers**: `intelligence_service`, `procurement_service`
- **Payload**:
  - `product_id`: Integer
  - `current_quantity`: Integer
  - `threshold`: Integer

### 4. `STOCKOUT`
- **Producer**: `inventory_service`
- **Consumers**: `intelligence_service`, `menu_service` (auto-disable items)
- **Payload**:
  - `product_id`: Integer

### 5. `PURCHASE_RECEIVED`
- **Producer**: `procurement_service`
- **Consumers**: `inventory_service`, `analytics_service`
- **Payload**:
  - `purchase_order_id`: Integer
  - `received_items`: Array of objects (product_id, quantity)

## Dead-Letter & Retry Policy
Events that fail processing (internal consumers) or delivery (Webhooks) more than 3 times are moved to the DLQ state (`retry_count >= 3`).
Administrators can inspect, retry, or discard these via `/api/v1/events/failed`.
