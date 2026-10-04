import { authService } from './authService';
import { foodService } from './foodService';
import { orderService } from './orderService';

const MOCK_DELAY = 1500;

// In-memory state for mock backend
let paymentConfigs = {
  'CAN-001': {
    canteenId: 'CAN-001',
    provider: 'UPI',
    displayName: 'Main Campus Canteen - Official',
    merchantReference: 'maincanteen@upi',
    status: 'ACTIVE',
    qrImageUrl: 'https://upload.wikimedia.org/wikipedia/commons/d/d0/QR_code_for_mobile_English_Wikipedia.svg'
  }
};

let payments = []; // Array of payment objects

export const paymentService = {
  // MANAGER: Get configuration
  getPaymentConfig: async () => {
    return new Promise(resolve => setTimeout(() => {
      resolve(paymentConfigs['CAN-001'] || null);
    }, 500));
  },

  // MANAGER: Update configuration
  updatePaymentConfig: async (configUpdates) => {
    return new Promise(resolve => setTimeout(() => {
      const existing = paymentConfigs['CAN-001'] || {};
      paymentConfigs['CAN-001'] = { ...existing, ...configUpdates };
      resolve(paymentConfigs['CAN-001']);
    }, 500));
  },

  // MANAGER: Get payments analytics and list
  getPaymentsAnalytics: async () => {
    return new Promise(resolve => setTimeout(() => {
      const today = payments.filter(p => new Date(p.createdAt).toDateString() === new Date().toDateString());
      
      const successful = today.filter(p => p.status === 'SUCCESS');
      const pending = today.filter(p => p.status === 'PENDING');
      const failed = today.filter(p => p.status === 'FAILED');

      resolve({
        totalRevenue: successful.reduce((sum, p) => sum + p.amount, 0),
        successfulCount: successful.length,
        pendingCount: pending.length,
        failedCount: failed.length,
        recentPayments: [...payments].sort((a,b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, 50)
      });
    }, 500));
  },

  // CUSTOMER: Initiate Checkout & Reserve Inventory
  initiateCheckout: async (cart) => {
    return new Promise(async (resolve, reject) => {
      setTimeout(async () => {
        try {
          // Re-validate inventory & prices
          let subtotal = 0;
          for (let item of cart) {
            // Check real stock
            const realItem = (await foodService.getFoodItems()).find(f => f.id === item.id);
            if (!realItem) throw new Error(`${item.name} is no longer available in the menu.`);
            if (!realItem.isAvailable) throw new Error(`${realItem.name} is temporarily unavailable.`);
            if (realItem.stock < item.quantity) throw new Error(`Only ${realItem.stock} portions of ${realItem.name} are left.`);
            
            subtotal += realItem.price * item.quantity;
          }

          const taxes = Math.round(subtotal * 0.05);
          const convenienceFee = 5;
          const total = subtotal + taxes + convenienceFee;

          // Reserve inventory (Atomic mock)
          for (let item of cart) {
            const realItem = (await foodService.getFoodItems()).find(f => f.id === item.id);
            await foodService.updateFoodItem(item.id, { stock: realItem.stock - item.quantity });
          }

          // Generate Checkout Session ID
          const checkoutId = 'CHK-' + Math.random().toString(36).substr(2, 9).toUpperCase();
          
          resolve({
            checkoutId,
            subtotal,
            taxes,
            convenienceFee,
            total,
            expiresIn: 300 // 5 minutes
          });
        } catch (error) {
          reject(error.message);
        }
      }, 800);
    });
  },

  // CUSTOMER: Process Payment
  processPayment: async (checkoutId, amount, method, cart) => {
    return new Promise((resolve, reject) => {
      // Create pending payment
      const paymentId = 'PAY-' + Math.floor(10000000 + Math.random() * 90000000);
      const user = authService.getCurrentUser();
      
      const paymentObj = {
        id: paymentId,
        checkoutId,
        canteenId: 'CAN-001',
        userId: user.id,
        userName: user.name,
        amount,
        method,
        status: 'PENDING',
        createdAt: new Date().toISOString()
      };
      
      payments.push(paymentObj);

      // Simulate provider verification delay
      setTimeout(async () => {
        // Mock 5% failure rate for realism
        const isSuccess = Math.random() > 0.05;

        if (isSuccess) {
          const p = payments.find(p => p.id === paymentId);
          p.status = 'SUCCESS';
          p.completedAt = new Date().toISOString();

          // Publish order confirmation event / KDS integration
          const orderItems = cart.map(item => ({
            id: item.id,
            name: item.name,
            quantity: item.quantity,
            price: item.price
          }));

          const orderReq = {
            canteenId: 'CAN-001',
            userId: user.id,
            totalAmount: amount,
            items: orderItems,
            paymentId
          };

          // Create the confirmed order
          const confirmedOrder = await orderService.createOrder(orderReq);
          p.orderId = confirmedOrder.id;
          
          resolve({
            success: true,
            paymentId,
            orderId: confirmedOrder.id,
            token: confirmedOrder.token || 'A-' + Math.floor(100 + Math.random()*900)
          });
        } else {
          const p = payments.find(p => p.id === paymentId);
          p.status = 'FAILED';
          
          // Release inventory reservation
          for (let item of cart) {
            const realItem = (await foodService.getFoodItems()).find(f => f.id === item.id);
            if (realItem) {
               await foodService.updateFoodItem(item.id, { stock: realItem.stock + item.quantity });
            }
          }

          reject("Payment gateway declined the transaction.");
        }
      }, 3000);
    });
  },
  
  cancelCheckout: async (cart) => {
    // Release inventory reservation
    for (let item of cart) {
      const realItem = await foodService.getFoodItems().then(items => items.find(f => f.id === item.id));
      if (realItem) {
          await foodService.updateFoodItem(item.id, { stock: realItem.stock + item.quantity });
      }
    }
  }
};
