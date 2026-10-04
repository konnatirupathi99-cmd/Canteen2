# Cross-Platform Canteen Management Ecosystem

## Description
A cross-platform real-time canteen management system designed to solve extreme load, rapid concurrency, and cross-platform syncing during peak lunch rushes.

## Problem Being Solved
Managing concurrent orders, rapid inventory deduction, and real-time syncing between Cashiers, Kitchens, and Managers during short, intense peak times.

## Architecture Overview
The system follows a Modular Monolith architecture for the backend (Flask + PostgreSQL) and a single-page application for the frontend (React + Vite). Real-time events are delivered via WebSockets (Socket.IO).

## Technology Stack
- **Frontend:** React, Vite
- **Backend:** Python, Flask
- **Database:** PostgreSQL
- **Real-time:** WebSockets (Flask-SocketIO)
- **ORM:** SQLAlchemy
- **Authentication:** JWT (Planned for Phase 3)

## Repository Structure
```
canteen-management-system/
├── backend/       # Flask API and business logic
├── frontend/      # React Vite application
└── docs/          # Architecture, API, and Decision Records
```

## Prerequisites
- Node.js (v18+)
- Python (3.10+)
- PostgreSQL (running locally or via Docker)
- Git

## Installation & Setup

### Database Setup
1. Ensure PostgreSQL is running.
2. Create a local database named `canteen_db`:
   ```sql
   CREATE DATABASE canteen_db;
   ```

### Backend Startup
1. Navigate to the backend directory: `cd backend`
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment:
   - Windows: `.\venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure your `DATABASE_URL`.
6. Run the server: `python run.py`

### Frontend Startup
1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`

### Testing
- Backend tests can be run using pytest:
  ```bash
  cd backend
  pytest
  ```

## Development Workflow
The recommended workflow requires running the frontend, backend, and database concurrently.

1. Terminal 1: Ensure PostgreSQL is running.
2. Terminal 2: Start Flask backend.
3. Terminal 3: Start React frontend.
4. Open the frontend URL in the browser and verify the **Technical Foundation** dashboard shows that all services are **CONNECTED**.

## Future Phases
- Phase 2: Database Architecture & Data Model
- Phase 3: Authentication & Authorization
- Phase 4: Product & Menu Management
- Phase 5: POS & Inventory Concurrency
- Phase 6: Kitchen Display System
- Phase 7: Polish & Analytics
