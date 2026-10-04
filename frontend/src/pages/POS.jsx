import React, { useState } from 'react';
import { ShoppingCart, Plus, Minus, X } from 'lucide-react';
import './POS.css';

const MOCK_CATEGORIES = ['All', 'Breakfast', 'Meals', 'Snacks', 'Beverages', 'Desserts'];

const MOCK_ITEMS = [
  { id: 1, name: 'Veg Meals', category: 'Meals', price: 60, stock: 42, available: true },
  { id: 2, name: 'Idli', category: 'Breakfast', price: 30, stock: 15, available: true },
  { id: 3, name: 'Dosa', category: 'Breakfast', price: 40, stock: 0, available: false },
  { id: 4, name: 'Vada', category: 'Breakfast', price: 25, stock: 20, available: true },
  { id: 5, name: 'Paneer Rice', category: 'Meals', price: 80, stock: 12, available: true },
  { id: 6, name: 'Chicken Rice', category: 'Meals', price: 100, stock: 5, available: true },
  { id: 7, name: 'Samosa', category: 'Snacks', price: 20, stock: 35, available: true },
  { id: 8, name: 'Tea', category: 'Beverages', price: 15, stock: 50, available: true },
  { id: 9, name: 'Coffee', category: 'Beverages', price: 20, stock: 40, available: true },
  { id: 10, name: 'Fresh Lime', category: 'Beverages', price: 25, stock: 10, available: true }
];

export default function POS() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [cart, setCart] = useState([]);
  
  const filteredItems = activeCategory === 'All' 
    ? MOCK_ITEMS 
    : MOCK_ITEMS.filter(item => item.category === activeCategory);

  const addToCart = (item) => {
    if (item.stock === 0 || !item.available) return;
    
    setCart(prev => {
      const existing = prev.find(i => i.id === item.id);
      if (existing) {
        if (existing.qty >= item.stock) return prev; // Cannot add more than stock
        return prev.map(i => i.id === item.id ? { ...i, qty: i.qty + 1 } : i);
      }
      return [...prev, { ...item, qty: 1 }];
    });
  };

  const updateQty = (id, delta) => {
    setCart(prev => prev.map(i => {
      if (i.id === id) {
        const newQty = i.qty + delta;
        return newQty > 0 ? { ...i, qty: newQty } : i;
      }
      return i;
    }));
  };

  const removeItem = (id) => {
    setCart(prev => prev.filter(i => i.id !== id));
  };

  const subtotal = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
  const tax = subtotal * 0.05;
  const total = subtotal + tax;

  const handleCheckout = () => {
    if (cart.length === 0) return;
    alert(`Checkout successful! Order total: ₹${total.toFixed(2)}\n(Demo Mode: Backend integration pending)`);
    setCart([]);
  };

  return (
    <div className="pos-container">
      {/* Categories */}
      <div className="pos-categories card">
        <h4 className="pos-section-title">Categories</h4>
        <ul className="category-list">
          {MOCK_CATEGORIES.map(cat => (
            <li 
              key={cat}
              className={`category-item ${activeCategory === cat ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat)}
            >
              {cat}
            </li>
          ))}
        </ul>
      </div>

      {/* Food Items */}
      <div className="pos-items-grid">
        {filteredItems.map(item => (
          <div key={item.id} className={`pos-item-card card ${!item.available || item.stock === 0 ? 'disabled' : ''}`}>
            <div className="item-details">
              <h5 className="item-name">{item.name}</h5>
              <div className="item-price">₹{item.price}</div>
              
              <div className="item-status">
                {item.stock === 0 || !item.available ? (
                  <span className="badge badge-danger">OUT OF STOCK</span>
                ) : (
                  <span className="badge badge-success">● Available ({item.stock} left)</span>
                )}
              </div>
            </div>
            <button 
              className="btn btn-primary btn-add" 
              disabled={item.stock === 0 || !item.available}
              onClick={() => addToCart(item)}
            >
              ADD
            </button>
          </div>
        ))}
      </div>

      {/* Cart */}
      <div className="pos-cart card">
        <div className="cart-header">
          <h4 className="pos-section-title">Current Order</h4>
          <span className="badge badge-neutral">{cart.length} Items</span>
        </div>
        
        <div className="cart-items">
          {cart.length === 0 ? (
            <div className="empty-cart">
              <ShoppingCart size={48} className="empty-icon" />
              <p>Cart is empty</p>
            </div>
          ) : (
            cart.map(item => (
              <div key={item.id} className="cart-item">
                <div className="cart-item-info">
                  <div className="cart-item-name">{item.name}</div>
                  <div className="cart-item-price">₹{item.price}</div>
                </div>
                
                <div className="cart-item-actions">
                  <button className="qty-btn" onClick={() => updateQty(item.id, -1)}><Minus size={14}/></button>
                  <span className="qty-display">{item.qty}</span>
                  <button className="qty-btn" onClick={() => updateQty(item.id, 1)} disabled={item.qty >= item.stock}><Plus size={14}/></button>
                </div>
                
                <div className="cart-item-total">₹{item.price * item.qty}</div>
                <button className="remove-btn" onClick={() => removeItem(item.id)}><X size={16}/></button>
              </div>
            ))
          )}
        </div>
        
        <div className="cart-summary">
          <div className="summary-row">
            <span>Subtotal</span>
            <span>₹{subtotal.toFixed(2)}</span>
          </div>
          <div className="summary-row">
            <span>Tax (5%)</span>
            <span>₹{tax.toFixed(2)}</span>
          </div>
          <div className="summary-row total">
            <span>Total</span>
            <span>₹{total.toFixed(2)}</span>
          </div>
          
          <button 
            className="btn btn-primary btn-checkout" 
            disabled={cart.length === 0}
            onClick={handleCheckout}
          >
            PROCEED TO PAYMENT
          </button>
        </div>
      </div>
    </div>
  );
}
