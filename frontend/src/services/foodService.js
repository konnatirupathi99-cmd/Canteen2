const delay = (ms) => new Promise(res => setTimeout(res, ms));

// Mock Data
let mockCategories = [
  { id: 'all', name: 'ALL' },
  { id: 'breakfast', name: 'BREAKFAST' },
  { id: 'meals', name: 'MEALS' },
  { id: 'snacks', name: 'SNACKS' },
  { id: 'beverages', name: 'BEVERAGES' },
];

let mockReviews = [
  { id: 'r1', foodItemId: 'f2', userId: 'u2', userName: 'Rahul K.', rating: 5, comment: 'Crispy and tasty. Sambar was excellent.', isVerifiedPurchase: true, createdAt: '2026-10-01T10:00:00Z', managerResponse: null },
  { id: 'r2', foodItemId: 'f2', userId: 'u3', userName: 'Amit S.', rating: 4, comment: 'Good dosa, but a bit oily.', isVerifiedPurchase: true, createdAt: '2026-10-02T12:00:00Z', managerResponse: 'Thank you for your feedback. We will ask our chefs to use less oil.' },
  { id: 'r3', foodItemId: 'f4', userId: 'u4', userName: 'Priya M.', rating: 3, comment: 'Samosa was cold.', isVerifiedPurchase: true, createdAt: '2026-10-03T09:00:00Z', managerResponse: null },
];

let mockFoodItems = [
  { id: 'f1', name: 'Veg Meals', categoryId: 'meals', price: 60, isAvailable: true, stock: 20, stall: 'Main Canteen', preparationTime: '10 min', image: 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=400&q=80', images: ['https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=800&q=80'], vegStatus: 'VEG', popular: true, description: 'Traditional vegetarian thali served with rice, dal, two curries, papad, and pickle.', ingredients: ['Rice', 'Dal', 'Vegetables', 'Spices'], allergens: ['None'], servingInfo: '1 Plate', rating: 4.8, reviewCount: 120 },
  { id: 'f2', name: 'Masala Dosa', categoryId: 'breakfast', price: 40, isAvailable: true, stock: 15, stall: 'South Indian Stall', preparationTime: '8 min', image: 'https://images.unsplash.com/photo-1589301760014-d929f39ce9b1?auto=format&fit=crop&w=400&q=80', images: ['https://images.unsplash.com/photo-1589301760014-d929f39ce9b1?auto=format&fit=crop&w=800&q=80', 'https://images.unsplash.com/photo-1610192773928-76949f91d8bb?auto=format&fit=crop&w=800&q=80'], vegStatus: 'VEG', popular: true, description: 'A traditional crispy dosa prepared with fermented rice and urad dal batter and served with fresh coconut chutney and hot sambar.', ingredients: ['Rice batter', 'Potato Masala', 'Oil'], allergens: ['Mustard seeds'], servingInfo: '1 Dosa with Sambar & Chutney', rating: 4.5, reviewCount: 247 },
  { id: 'f3', name: 'Idli', categoryId: 'breakfast', price: 30, isAvailable: true, stock: 50, stall: 'South Indian Stall', preparationTime: '5 min', image: 'https://images.unsplash.com/photo-1589301773112-0071376269b6?auto=format&fit=crop&w=400&q=80', images: ['https://images.unsplash.com/photo-1589301773112-0071376269b6?auto=format&fit=crop&w=800&q=80'], vegStatus: 'VEG', description: 'Soft and fluffy steamed rice cakes served with sambar and chutney.', rating: 4.6, reviewCount: 89 },
  { id: 'f4', name: 'Samosa', categoryId: 'snacks', price: 20, isAvailable: true, stock: 5, stall: 'Snacks Stall', preparationTime: '4 min', image: 'https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=400&q=80', images: ['https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=800&q=80'], vegStatus: 'VEG', lowStockThreshold: 10, description: 'Crispy pastry filled with spiced potatoes and peas.', rating: 3.0, reviewCount: 1 },
  { id: 'f5', name: 'Chicken Rice', categoryId: 'meals', price: 100, isAvailable: true, stock: 12, stall: 'North Indian Stall', preparationTime: '12 min', image: 'https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=400&q=80', images: ['https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=800&q=80'], vegStatus: 'NON-VEG', popular: true, description: 'Flavorful fried rice cooked with tender chicken pieces and spices.', rating: 4.7, reviewCount: 200 },
  { id: 'f6', name: 'Paneer Rice', categoryId: 'meals', price: 80, isAvailable: true, stock: 8, stall: 'North Indian Stall', preparationTime: '10 min', image: 'https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=400&q=80', images: ['https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=800&q=80'], vegStatus: 'VEG', description: 'Fried rice cooked with soft paneer cubes.', rating: 4.2, reviewCount: 45 },
  { id: 'f7', name: 'Tea', categoryId: 'beverages', price: 15, isAvailable: true, stock: 100, stall: 'Beverage Stall', preparationTime: '3 min', image: 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=400&q=80', images: ['https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=800&q=80'], vegStatus: 'VEG', description: 'Hot Indian milk tea infused with spices.', rating: 4.5, reviewCount: 300 },
  { id: 'f8', name: 'Coffee', categoryId: 'beverages', price: 20, isAvailable: true, stock: 100, stall: 'Beverage Stall', preparationTime: '3 min', image: 'https://images.unsplash.com/photo-1559525839-b184a4d698c7?auto=format&fit=crop&w=400&q=80', images: ['https://images.unsplash.com/photo-1559525839-b184a4d698c7?auto=format&fit=crop&w=800&q=80'], vegStatus: 'VEG', description: 'Freshly brewed filter coffee.', rating: 4.8, reviewCount: 150 },
  { id: 'f9', name: 'Special Thali', categoryId: 'meals', price: 120, isAvailable: false, stock: 0, stall: 'Main Canteen', preparationTime: '15 min', image: 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=400&q=80', images: ['https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=800&q=80'], vegStatus: 'VEG', description: 'A grand feast with multiple curries, rotis, rice, and dessert.', rating: 4.9, reviewCount: 400 }
];

export const foodService = {
  async getCategories() {
    await delay(200);
    return [...mockCategories];
  },

  async getFoodItems() {
    await delay(300);
    return [...mockFoodItems];
  },

  async getFoodById(id) {
    await delay(200);
    const item = mockFoodItems.find(f => f.id === id);
    if (!item) throw new Error("Food not found");
    return item;
  },

  async getReviews(foodItemId) {
    await delay(300);
    return mockReviews.filter(r => r.foodItemId === foodItemId).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  },

  async addReview(foodItemId, reviewData) {
    await delay(500);
    const newReview = {
      id: `r${Date.now()}`,
      foodItemId,
      userId: reviewData.userId || 'u1',
      userName: reviewData.userName || 'Anonymous',
      rating: reviewData.rating,
      comment: reviewData.comment,
      isVerifiedPurchase: true, // Assuming true for mock
      createdAt: new Date().toISOString(),
      managerResponse: null
    };
    mockReviews.push(newReview);
    
    // Update aggregate rating
    const itemIndex = mockFoodItems.findIndex(f => f.id === foodItemId);
    if (itemIndex > -1) {
      const item = mockFoodItems[itemIndex];
      const itemReviews = mockReviews.filter(r => r.foodItemId === foodItemId);
      const avg = itemReviews.reduce((sum, r) => sum + r.rating, 0) / itemReviews.length;
      item.rating = Math.round(avg * 10) / 10;
      item.reviewCount = itemReviews.length;
    }
    
    return newReview;
  },
  
  async updateManagerResponse(reviewId, responseText) {
    await delay(400);
    const review = mockReviews.find(r => r.id === reviewId);
    if (review) {
      review.managerResponse = responseText;
      return review;
    }
    throw new Error("Review not found");
  },

  async getAllReviews() {
    await delay(400);
    return [...mockReviews].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  },

  async addFoodItem(itemData) {
    await delay(500);
    const newItem = {
      ...itemData,
      id: `f${Date.now()}`, // mock ID
      stock: parseInt(itemData.stock, 10) || 0,
      price: parseFloat(itemData.price) || 0,
      lowStockThreshold: parseInt(itemData.lowStockThreshold, 10) || 5,
      rating: 0,
      reviewCount: 0,
      images: itemData.images || [itemData.image || '']
    };
    if (newItem.stock === 0) newItem.isAvailable = false;
    mockFoodItems.push(newItem);
    return newItem;
  },

  async updateFoodItem(id, updates) {
    await delay(500);
    const index = mockFoodItems.findIndex(i => i.id === id);
    if (index === -1) throw new Error("Item not found");
    
    const currentItem = mockFoodItems[index];
    const updatedItem = { ...currentItem, ...updates };
    
    if (updates.stock !== undefined) {
       updatedItem.stock = parseInt(updates.stock, 10);
    }
    
    // Sync main image if images array is updated
    if (updates.images && updates.images.length > 0) {
       updatedItem.image = updates.images[0];
    }

    mockFoodItems[index] = updatedItem;
    return updatedItem;
  },

  async deactivateFoodItem(id) {
    await delay(500);
    const index = mockFoodItems.findIndex(i => i.id === id);
    if (index === -1) throw new Error("Item not found");
    mockFoodItems[index].isActive = false;
    mockFoodItems[index].isAvailable = false;
    return true;
  },

  simulateStockDecrement(itemId, quantity) {
    const item = mockFoodItems.find(i => i.id === itemId);
    if (item && item.stock >= quantity) {
      item.stock -= quantity;
      return true;
    }
    return false;
  }
};
