# Architecture

## High-Level Architecture

The system follows a Modular Monolithic Architecture with a React frontend and a Flask backend.

### Frontend (React + Vite)
- Responsible for all presentation logic.
- Connects to backend via HTTP (for REST) and WebSockets (for Real-time).
- Uses role-based routing (Admin, Canteen Manager, Cashier, Kitchen).

### Backend (Flask)
- A Modular Monolith organized by feature domains (Routes, Services, Repositories).
- Serves as the authoritative source of truth.
- Validates all requests, enforces permissions, and maintains inventory consistency.
- Connects to PostgreSQL using SQLAlchemy ORM.

### Database (PostgreSQL)
- The persistent source of truth.
- Ensures atomic, concurrency-safe inventory operations.

### Event Layer (WebSockets)
- Emits real-time events to connected clients.
- Used for live order queues, inventory updates, and dashboard metrics.
- State is NOT persisted here. It's a delivery mechanism only.

## Conceptual Flow
1. **Frontend** triggers an action (e.g., checkout).
2. **Backend API** validates the request.
3. **Backend Service** executes business logic (e.g., inventory deduction).
4. **Database** commits the transaction.
5. **Event Publisher** emits success event to WebSocket layer.
6. **WebSocket** broadcasts updates to Kitchen and Cashier clients.
