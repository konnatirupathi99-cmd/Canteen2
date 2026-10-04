import { foodService } from './foodService';
import { authService } from './authService';

const delay = (ms) => new Promise(res => setTimeout(res, ms));

let mockOrders = [];
let nextOrderId = 1024;

export const orderService = {
  async placeOrder(cartItems) {
    await delay(800); // Simulate network

    const user = authService.getCurrentUser();
    if (!user) throw new Error("Authentication required");

    // Re-validate stock atomically
    for (let item of cartItems) {
      const dbItem = (await foodService.getFoodItems()).find(f => f.id === item.id);
      if (!dbItem || dbItem.stock < item.quantity) {
        throw new Error(`Only ${dbItem ? dbItem.stock : 0} ${item.name} are currently available. Please update your quantity.`);
      }
    }

    // Decrement stock
    for (let item of cartItems) {
      foodService.simulateStockDecrement(item.id, item.quantity);
    }

    const total = cartItems.reduce((acc, curr) => acc + (curr.price * curr.quantity), 0);
    const orderId = `CAN-2026-00${nextOrderId++}`;

    const newOrder = {
      id: orderId,
      userId: user.id,
      items: cartItems.map(i => ({ ...i })),
      totalAmount: total,
      status: 'QUEUED',
      createdAt: new Date().toISOString(),
      pickupStall: cartItems.length > 0 ? cartItems[0].stall : 'Main Canteen',
      estimatedReadyTime: new Date(Date.now() + 15 * 60000).toISOString() // 15 mins from now
    };

    mockOrders.push(newOrder);

    // Simulate real-time updates (Queued -> Preparing -> Ready)
    setTimeout(() => {
      const order = mockOrders.find(o => o.id === orderId);
      if(order) order.status = 'PREPARING';
    }, 5000);

    setTimeout(() => {
      const order = mockOrders.find(o => o.id === orderId);
      if(order) order.status = 'READY';
    }, 15000);

    return newOrder;
  },

  async getOrder(orderId) {
    await delay(300);
    return mockOrders.find(o => o.id === orderId);
  },

  async getUserOrders() {
    await delay(300);
    const user = authService.getCurrentUser();
    if (!user) return [];
    return mockOrders.filter(o => o.userId === user.id).sort((a,b) => new Date(b.createdAt) - new Date(a.createdAt));
  }
};
