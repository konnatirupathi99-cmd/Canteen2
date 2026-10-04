# Hackathon Demonstration Script

**Project:** Cross-Platform Canteen Management Ecosystem  
**Value Proposition:** "An institutional canteen ecosystem where every transaction, inventory movement, kitchen operation, and supply-chain event is synchronized in real time, while predictive and prescriptive intelligence helps operators prevent stockouts, reduce waiting time, minimize waste, and optimize resources."

---

## Preparation
1. Run `python scripts/seed_demo.py` to reset the database and populate safe seed data.
2. Ensure the API Gateway, Event Bus (SocketIO), and backend are running.
3. Open 3 browser windows side-by-side to simulate:
   - **Window 1 (Manager/Intelligence)**: Command Center Dashboard
   - **Window 2 (Kitchen)**: Kitchen Display System (KDS)
   - **Window 3 (Customer/Cashier)**: POS / Ordering App

---

## The Story: The Lunch Rush

**Narrator:** *"A busy institutional lunch period is approaching. In traditional canteens, this leads to chaos: out-of-stock items, angry customers, and overwhelmed kitchens. Let's see how our Intelligent Canteen Ecosystem prevents this."*

### Step 1: The Command Center (Manager View)
- **Action:** Open Window 1. Log in as `manager@canteen.com`. Navigate to the **Intelligence Dashboard** (`/api/v1/intelligence/snapshot`).
- **Talking Point:** "Here is the Command Center. The manager has a real-time operational snapshot of the entire campus. Currently, everything is healthy. We see active orders, kitchen utilization, and inventory health."

### Step 2: Customer Ordering & Real-Time Availability
- **Action:** Open Window 3. Log in as `customer@canteen.com`. View the menu.
- **Talking Point:** "Our customer opens their app. Notice that 'Bottled Water' shows exactly **1 unit remaining**. In a legacy system, 10 people might order that same bottle, leading to 9 refunds."

### Step 3: Concurrency & Atomic Checkout (The Stress Test)
- **Action:** 
  1. Open a *4th incognito window* as `cashier@canteen.com`.
  2. In both the Customer (Win 3) and Cashier (Win 4) windows, attempt to checkout the last 'Bottled Water' at the **exact same time**.
- **Result:** One succeeds. The other immediately receives an `OUT_OF_STOCK` error (`409 Conflict`).
- **Talking Point:** "We just fired two concurrent purchase attempts for the final item. Our backend uses atomic database reservations. Only one transaction succeeded. The other was cleanly rejected. **No race conditions. No negative inventory. No overselling.**"

### Step 4: Real-Time Event Streaming (KDS)
- **Action:** Look at Window 2 (Kitchen KDS).
- **Result:** The successful order instantly appears without refreshing the page.
- **Talking Point:** "Because of our Event-Driven architecture, the successful order bypassed standard polling and was pushed instantly to the Kitchen Display System via WebSockets."

### Step 5: Kitchen Operations & Customer Updates
- **Action:** In Window 2 (Kitchen), click "Accept Order" -> "Ready".
- **Result:** The Customer (Window 3) instantly receives a status update ("Your order is Ready!").
- **Talking Point:** "As the kitchen advances the ticket, the customer is kept in the loop in real time. This eliminates counter crowding."

### Step 6: Prescriptive Intelligence (The Demand Surge)
- **Action:** Run the `POST /api/v1/intelligence/simulate` endpoint with a `DEMAND_SPIKE` scenario for the 'Classic Burger'.
- **Result:** The Intelligence Engine detects a simulated 300% surge and flags an anomaly.
- **Talking Point:** "Now, a massive crowd arrives. Our Intelligence Engine runs in the background. It detects a Demand Surge."
- **Action:** In Window 1 (Manager), show the new `Recommendation` ("Demand surged. Increase preparation volume by 150%").
- **Talking Point:** "Rather than acting autonomously and causing chaos, the AI generates a Prescriptive Recommendation for the manager. The manager is always in control."

### Step 7: Final Analytics
- **Action:** Navigate to the Analytics dashboard.
- **Talking Point:** "Because every module—orders, inventory, kitchen, intelligence—shares a single source of truth, our analytics are perfectly accurate. We can track stockouts avoided, wait times reduced, and overall ecosystem health."

---

## Conclusion
"We haven't just built a food ordering app. We've built a **fault-tolerant, real-time operating system** for food-court logistics."
