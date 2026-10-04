import React, { useState, useEffect } from 'react';
import { Search, Clock, Plus, Minus, Trash2, ChevronRight, AlertTriangle, Info, MapPin, ShoppingBag } from 'lucide-react';
import { foodService } from '../services/foodService';
import { orderService } from '../services/orderService';
import { authService } from '../services/authService';
import { useNavigate, useLocation } from 'react-router-dom';
import FoodDetailsModal from '../components/FoodDetailsModal';
import './Ordering.css';

export default function Ordering() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  
  // Data State
  const [categories, setCategories] = useState([]);
  const [foodItems, setFoodItems] = useState([]);
  
  // Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [availabilityFilter, setAvailabilityFilter] = useState('AVAILABLE'); // ALL, AVAILABLE
  
  // Cart State
  const [cart, setCart] = useState(location.state?.cart || []);
  const [cartOpenMobile, setCartOpenMobile] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [checkoutError, setCheckoutError] = useState(null);
  
  // Details Modal
  const [selectedFood, setSelectedFood] = useState(null);

  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);
    loadData();
    if (location.state?.cart) {
      navigate('/customer/ordering', { replace: true, state: {} });
    }
  }, []);

  const loadData = async () => {
    const cats = await foodService.getCategories();
    const items = await foodService.getFoodItems();
    setCategories(cats);
    setFoodItems(items);
  };

  // -------------------------------------------------------------
  // CART LOGIC
  // -------------------------------------------------------------
  const addToCart = (item) => {
    setCheckoutError(null);
    setCart(prev => {
      const existing = prev.find(i => i.id === item.id);
      if (existing) {
        if (existing.quantity >= item.stock) return prev; // Cannot exceed stock
        return prev.map(i => i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i);
      }
      return [...prev, { ...item, quantity: 1 }];
    });
  };

  const updateCartQty = (id, delta) => {
    setCheckoutError(null);
    setCart(prev => {
      return prev.map(item => {
        if (item.id === id) {
          const newQ = item.quantity + delta;
          if (newQ > item.stock) return item; // Block
          return { ...item, quantity: newQ };
        }
        return item;
      }).filter(item => item.quantity > 0);
    });
  };

  const cartTotal = cart.reduce((acc, curr) => acc + (curr.price * curr.quantity), 0);
  const cartItemCount = cart.reduce((acc, curr) => acc + curr.quantity, 0);

  const handleCheckout = () => {
    if (cart.length === 0) return;
    navigate('/customer/checkout', { state: { cart } });
  };

  // -------------------------------------------------------------
  // FILTERING LOGIC
  // -------------------------------------------------------------
  const filteredItems = foodItems.filter(item => {
    // 1. Search
    if (searchQuery && !item.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    // 2. Category
    if (activeCategory !== 'all' && item.categoryId !== activeCategory) return false;
    // 3. Availability
    if (availabilityFilter === 'AVAILABLE' && !item.isAvailable) return false;
    return true;
  });

  return (
    <div className="ordering-page">
      <div className="ordering-container">
        
        {/* Left Side: Browsing */}
        <div className="browsing-section">
          
          <div className="greeting-section">
            <h1>Good evening, {user?.name?.split(' ')[0] || 'Student'}!</h1>
            <p>What are you craving today?</p>
          </div>

          <div className="system-status-banner mb-6">
            <span className="live-dot"></span> Live availability • Canteen Open
          </div>

          {/* Search Bar */}
          <div className="search-wrapper mb-6">
            <Search className="search-icon" size={20} />
            <input 
              type="text" 
              className="main-search-input" 
              placeholder="Search for dosa, biryani, tea, meals..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Categories */}
          <div className="categories-wrapper mb-6">
            {categories.map(cat => (
              <button 
                key={cat.id} 
                className={`category-pill ${activeCategory === cat.id ? 'active' : ''}`}
                onClick={() => setActiveCategory(cat.id)}
              >
                {cat.name}
              </button>
            ))}
          </div>

          {/* Availability Toggle */}
          <div className="flex justify-between items-center mb-4">
            <h2 className="section-title">{activeCategory === 'all' ? 'All Items' : categories.find(c=>c.id===activeCategory)?.name}</h2>
            <select 
              className="filter-select"
              value={availabilityFilter}
              onChange={(e) => setAvailabilityFilter(e.target.value)}
            >
              <option value="AVAILABLE">Available Now</option>
              <option value="ALL">Show All (Including Unavailable)</option>
            </select>
          </div>

          {/* Food Grid */}
          {filteredItems.length === 0 ? (
            <div className="empty-state">
              <p>No food items found matching your criteria.</p>
              <button className="btn btn-outline mt-4" onClick={() => { setSearchQuery(''); setActiveCategory('all'); setAvailabilityFilter('AVAILABLE'); }}>Clear Filters</button>
            </div>
          ) : (
            <div className="food-grid">
              {filteredItems.map(item => (
                <div key={item.id} className={`food-card ${!item.isAvailable ? 'unavailable' : ''}`} onClick={() => setSelectedFood(item)}>
                  <div className="food-image" style={{ backgroundImage: `url(${item.image || (item.images && item.images[0])})` }}>
                    {item.popular && <span className="absolute top-2 left-2 bg-primary text-white text-xs font-bold px-2 py-1 rounded shadow z-10">🔥 POPULAR</span>}
                    {item.rating >= 4.5 && <span className="absolute top-2 left-2 bg-warning text-dark text-xs font-bold px-2 py-1 rounded shadow z-10" style={item.popular ? {marginTop: '28px'} : {}}>★ TOP RATED</span>}
                    
                    {item.vegStatus === 'VEG' ? (
                      <span className="veg-badge bg-white text-success border border-success z-10">● VEG</span>
                    ) : (
                      <span className="veg-badge bg-white text-danger border border-danger z-10">▲ NON-VEG</span>
                    )}
                  </div>
                  <div className="food-info">
                    <div className="flex justify-between items-start mb-1">
                      <h3 className="food-name">{item.name}</h3>
                      <span className="food-price">₹{item.price}</span>
                    </div>
                    
                    <div className="flex justify-between items-center mb-1">
                      <p className="food-stall m-0">{item.stall}</p>
                      {item.rating > 0 && (
                        <div className="flex items-center text-sm font-bold">
                          <span className="text-warning mr-1">★</span> {item.rating.toFixed(1)} <span className="text-xs text-secondary font-normal ml-1">({item.reviewCount})</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="food-meta mb-4">
                      {item.isAvailable ? (
                        <span className={`status-badge ${item.stock <= (item.lowStockThreshold || 10) ? 'text-warning bg-warning-light' : 'text-success bg-success-light'}`}>
                          {item.stock <= (item.lowStockThreshold || 10) ? `⚠ Only ${item.stock} left` : '● Available'}
                        </span>
                      ) : (
                        <span className="status-badge text-danger bg-danger-light">Out of Stock</span>
                      )}
                      <span className="prep-time"><Clock size={12}/> {item.preparationTime}</span>
                    </div>

                    <button 
                      className={`btn w-full ${item.isAvailable ? 'btn-primary' : 'btn-disabled'}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        item.isAvailable && addToCart(item);
                      }}
                      disabled={!item.isAvailable}
                    >
                      {item.isAvailable ? '+ ADD TO CART' : 'UNAVAILABLE'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

        </div>

        {/* Right Side: Cart (Desktop) */}
        <div className="cart-section desktop-cart">
          <div className="cart-card">
            <h2 className="cart-title">YOUR ORDER</h2>
            
            {cart.length === 0 ? (
              <div className="empty-cart">
                <ShoppingBag size={48} className="text-border mb-4" />
                <p>Your cart is empty.</p>
                <p className="text-sm text-secondary">Add some items to get started!</p>
              </div>
            ) : (
              <div className="cart-content">
                {checkoutError && (
                  <div className="alert alert-error text-sm mb-4">
                    <AlertTriangle size={14}/> {checkoutError}
                  </div>
                )}
                
                <div className="cart-items">
                  {cart.map(item => (
                    <div key={item.id} className="cart-item">
                      <div className="cart-item-info">
                        <h4>{item.name}</h4>
                        <span className="text-secondary text-sm">₹{item.price}</span>
                      </div>
                      <div className="cart-qty-controls">
                        <button onClick={() => updateCartQty(item.id, -1)}><Minus size={14}/></button>
                        <span>{item.quantity}</span>
                        <button onClick={() => updateCartQty(item.id, 1)}><Plus size={14}/></button>
                      </div>
                      <div className="cart-item-total">
                        ₹{item.price * item.quantity}
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="cart-summary">
                  <div className="summary-row">
                    <span>Subtotal</span>
                    <span>₹{cartTotal}</span>
                  </div>
                  <div className="summary-row text-sm text-secondary">
                    <span>Taxes & Fees</span>
                    <span>₹0</span>
                  </div>
                  <div className="summary-row total-row">
                    <span>Total</span>
                    <span>₹{cartTotal}</span>
                  </div>
                </div>

                <div className="pickup-info mt-4 mb-4 p-3 bg-background rounded-lg text-sm">
                  <div className="flex items-center gap-2 font-medium mb-1"><MapPin size={14}/> Pickup Location</div>
                  <div className="text-secondary">{cart[0]?.stall || 'Main Canteen'}</div>
                </div>

                <button 
                  className="btn btn-primary w-full btn-large checkout-btn"
                  onClick={handleCheckout}
                  disabled={checkoutLoading}
                >
                  {checkoutLoading ? 'PROCESSING...' : `PLACE ORDER (₹${cartTotal})`}
                  {!checkoutLoading && <ChevronRight size={18}/>}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Floating Cart Button */}
      {cartItemCount > 0 && (
        <div className="mobile-cart-float" onClick={() => setCartOpenMobile(true)}>
          <div className="flex items-center gap-2">
            <ShoppingBag size={20} />
            <span className="font-bold">{cartItemCount} ITEMS</span>
          </div>
          <div className="font-bold">₹{cartTotal}</div>
        </div>
      )}

      {/* Mobile Cart Drawer (Simplified for prompt) */}
      {cartOpenMobile && (
        <div className="mobile-cart-drawer">
          <div className="drawer-overlay" onClick={() => setCartOpenMobile(false)}></div>
          <div className="drawer-content">
             <div className="flex justify-between items-center mb-4">
                <h2 className="cart-title m-0">YOUR ORDER</h2>
                <button className="btn-icon" onClick={() => setCartOpenMobile(false)}>✕</button>
             </div>
             
             {checkoutError && (
                <div className="alert alert-error text-sm mb-4">
                  <AlertTriangle size={14}/> {checkoutError}
                </div>
              )}

             <div className="cart-items" style={{ maxHeight: '50vh', overflowY: 'auto' }}>
                {cart.map(item => (
                  <div key={item.id} className="cart-item">
                    <div className="cart-item-info">
                      <h4>{item.name}</h4>
                      <span className="text-secondary text-sm">₹{item.price}</span>
                    </div>
                    <div className="cart-qty-controls">
                      <button onClick={() => updateCartQty(item.id, -1)}><Minus size={14}/></button>
                      <span>{item.quantity}</span>
                      <button onClick={() => updateCartQty(item.id, 1)}><Plus size={14}/></button>
                    </div>
                    <div className="cart-item-total font-medium">
                      ₹{item.price * item.quantity}
                    </div>
                  </div>
                ))}
              </div>

              <div className="cart-summary mt-4 pt-4 border-t border-border">
                <div className="summary-row total-row">
                  <span>Total</span>
                  <span>₹{cartTotal}</span>
                </div>
              </div>

              <button 
                className="btn btn-primary w-full btn-large checkout-btn mt-4"
                onClick={handleCheckout}
                disabled={checkoutLoading}
              >
                {checkoutLoading ? 'PROCESSING...' : `PLACE ORDER (₹${cartTotal})`}
              </button>
          </div>
        </div>
      )}

      {selectedFood && (
        <FoodDetailsModal 
          food={selectedFood}
          onClose={() => setSelectedFood(null)}
          onAddToCart={addToCart}
        />
      )}
    </div>
  );
}
