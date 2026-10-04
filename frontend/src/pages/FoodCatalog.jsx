import React, { useState, useEffect } from 'react';
import { Search, Plus, Filter, Edit, Trash2, Power, AlertTriangle, X } from 'lucide-react';
import { foodService } from '../services/foodService';
import './FoodCatalog.css';

export default function FoodCatalog() {
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isLive, setIsLive] = useState(true);

  // Search & Filter
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');

  // Modals
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  
  const [isStockModalOpen, setIsStockModalOpen] = useState(false);
  const [stockItem, setStockItem] = useState(null);
  const [stockInput, setStockInput] = useState('');

  // Image Upload State
  const [editImages, setEditImages] = useState([]);
  
  const handleImageUpload = (e) => {
    // Mock upload: in reality you'd upload to a server and get URLs back
    // Here we'll just read as object URL for preview purposes (or push a mock URL)
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      const newUrls = files.map(f => URL.createObjectURL(f));
      setEditImages([...editImages, ...newUrls]);
    }
  };

  const removeImage = (index) => {
    setEditImages(editImages.filter((_, i) => i !== index));
  };

  const setPrimaryImage = (index) => {
    if (index === 0) return;
    const newImages = [...editImages];
    const [selected] = newImages.splice(index, 1);
    newImages.unshift(selected);
    setEditImages(newImages);
  };

  // Initial Load
  useEffect(() => {
    loadData();
    // Simulate live connection
    const interval = setInterval(() => {
      // In a real app this would be a websocket listener fetching diffs.
      // We will re-fetch data quietly.
      loadDataQuietly();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    setLoading(true);
    await loadDataQuietly();
    setLoading(false);
  };

  const loadDataQuietly = async () => {
    try {
      const fetchedItems = await foodService.getFoodItems();
      const fetchedCategories = await foodService.getCategories();
      // Ensure all mock items explicitly have isActive unless set to false
      const standardizedItems = fetchedItems.map(i => ({...i, isActive: i.isActive !== false}));
      setItems(standardizedItems);
      setCategories(fetchedCategories);
      setIsLive(true);
    } catch {
      setIsLive(false);
    }
  };

  // --------------------------------------------------------
  // CALCULATED METRICS
  // --------------------------------------------------------
  const activeItems = items.filter(i => i.isActive);
  const totalCount = activeItems.length;
  const availableCount = activeItems.filter(i => i.isAvailable && i.stock > 0).length;
  const outOfStockCount = activeItems.filter(i => i.stock === 0).length;
  const lowStockCount = activeItems.filter(i => i.stock > 0 && i.stock <= (i.lowStockThreshold || 5)).length;
  const unavailableCount = activeItems.filter(i => !i.isAvailable).length; // Manager intentionally disabled

  // --------------------------------------------------------
  // ACTIONS
  // --------------------------------------------------------
  const toggleAvailability = async (item) => {
    const newStatus = !item.isAvailable;
    const confirm = window.confirm(`Mark ${item.name} as ${newStatus ? 'AVAILABLE' : 'UNAVAILABLE'}?`);
    if (!confirm) return;
    
    // Optimistic update
    setItems(prev => prev.map(i => i.id === item.id ? { ...i, isAvailable: newStatus } : i));
    
    try {
      await foodService.updateFoodItem(item.id, { isAvailable: newStatus });
    } catch (e) {
      alert("Failed to update availability. Rolling back.");
      loadDataQuietly();
    }
  };

  const deactivateItem = async (item) => {
    const confirm = window.confirm(`Deactivate ${item.name}?\nCustomers will no longer see this item.`);
    if (!confirm) return;
    
    setItems(prev => prev.filter(i => i.id !== item.id)); // Optimistic UI removal
    try {
      await foodService.deactivateFoodItem(item.id);
    } catch (e) {
      alert("Failed to deactivate.");
      loadDataQuietly();
    }
  };

  const saveFoodItem = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const data = {
      name: fd.get('name'),
      categoryId: fd.get('categoryId'),
      stall: fd.get('stall'),
      price: Number(fd.get('price')),
      stock: Number(fd.get('stock')),
      lowStockThreshold: Number(fd.get('lowStockThreshold')),
      preparationTime: fd.get('preparationTime'),
      vegStatus: fd.get('vegStatus'),
      isAvailable: fd.get('isAvailable') === 'true',
      images: editImages.length > 0 ? editImages : ['https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=400&q=80'],
    };

    setIsEditModalOpen(false);

    try {
      if (editingItem) {
        await foodService.updateFoodItem(editingItem.id, data);
      } else {
        await foodService.addFoodItem(data);
      }
      loadDataQuietly();
    } catch (err) {
      alert("Failed to save food item.");
    }
  };

  const updateStock = async (e) => {
    e.preventDefault();
    const newStock = Number(stockInput);
    setIsStockModalOpen(false);

    // Optimistic UI
    setItems(prev => prev.map(i => i.id === stockItem.id ? { ...i, stock: newStock } : i));

    try {
      await foodService.updateFoodItem(stockItem.id, { stock: newStock });
      loadDataQuietly();
    } catch (err) {
      alert("Failed to update stock.");
      loadDataQuietly();
    }
  };

  // --------------------------------------------------------
  // FILTERING & STATUS DETERMINATION
  // --------------------------------------------------------
  const getOperationalStatus = (item) => {
    if (!item.isAvailable) return { label: 'UNAVAILABLE', color: 'danger', icon: '○' };
    if (item.stock === 0) return { label: 'OUT OF STOCK', color: 'danger', icon: '●' };
    if (item.stock <= (item.lowStockThreshold || 5)) return { label: 'LOW STOCK', color: 'warning', icon: '⚠' };
    return { label: 'AVAILABLE', color: 'success', icon: '●' };
  };

  const filteredItems = activeItems.filter(item => {
    // Text search
    if (search && !item.name.toLowerCase().includes(search.toLowerCase()) && !item.id.toLowerCase().includes(search.toLowerCase())) return false;
    
    // Status Filter
    const opStatus = getOperationalStatus(item).label;
    if (statusFilter !== 'All') {
      if (statusFilter === 'Available' && opStatus !== 'AVAILABLE') return false;
      if (statusFilter === 'Low Stock' && opStatus !== 'LOW STOCK') return false;
      if (statusFilter === 'Out of Stock' && opStatus !== 'OUT OF STOCK') return false;
      if (statusFilter === 'Unavailable' && opStatus !== 'UNAVAILABLE') return false;
    }
    return true;
  });

  return (
    <div className="manager-page p-6 max-w-7xl mx-auto">
      
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold text-dark m-0">Food Items</h1>
          <p className="text-secondary mt-1">Manage menu items, prices, availability and stock.</p>
        </div>
        <div className="flex flex-col items-end gap-2">
           <div className={`live-indicator-pill ${isLive ? 'bg-success-light text-success border-success' : 'bg-danger-light text-danger border-danger'}`}>
             <span className={`live-dot ${isLive ? 'bg-success' : 'bg-danger'} ${isLive ? 'animate-pulse' : ''}`}></span>
             {isLive ? 'Inventory Sync: LIVE' : 'SYNC PAUSED'}
           </div>
           <button className="btn btn-primary" onClick={() => { 
             setEditingItem(null); 
             setEditImages([]);
             setIsEditModalOpen(true); 
           }}>
             <Plus size={16} /> ADD FOOD ITEM
           </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-5 gap-4 mb-8">
        <div className="summary-card">
          <h4>TOTAL ITEMS</h4>
          <h2>{totalCount}</h2>
        </div>
        <div className="summary-card border-success">
          <h4>AVAILABLE</h4>
          <h2 className="text-success">{availableCount}</h2>
        </div>
        <div className="summary-card border-warning">
          <h4>LOW STOCK</h4>
          <h2 className="text-warning">{lowStockCount}</h2>
        </div>
        <div className="summary-card border-danger">
          <h4>OUT OF STOCK</h4>
          <h2 className="text-danger">{outOfStockCount}</h2>
        </div>
        <div className="summary-card border-neutral">
          <h4>UNAVAILABLE</h4>
          <h2>{unavailableCount}</h2>
        </div>
      </div>

      {/* Actions Bar */}
      <div className="flex justify-between items-center mb-6 bg-white p-4 rounded-xl border border-border shadow-sm">
        <div className="flex flex-1 max-w-md items-center relative">
          <Search size={18} className="absolute left-3 text-secondary" />
          <input 
            type="text" 
            className="input-field pl-10 w-full"
            placeholder="Search food items (name or ID)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-secondary" />
            <select className="input-field" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="All">All Statuses</option>
              <option value="Available">Available</option>
              <option value="Low Stock">Low Stock</option>
              <option value="Out of Stock">Out of Stock</option>
              <option value="Unavailable">Unavailable</option>
            </select>
          </div>
        </div>
      </div>

      {/* Food Table */}
      <div className="card table-card overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-secondary">Loading food catalog...</div>
        ) : (
          <table className="manager-table">
            <thead>
              <tr>
                <th>FOOD ITEM</th>
                <th>CATEGORY</th>
                <th>STALL</th>
                <th>PRICE</th>
                <th>STOCK</th>
                <th>STATUS</th>
                <th>AVAILABLE (POS/APP)</th>
                <th className="text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map(item => {
                const opStatus = getOperationalStatus(item);
                return (
                  <tr key={item.id} className={!item.isAvailable ? 'row-unavailable' : ''}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-cover bg-center border border-border" style={{ backgroundImage: `url(${item.images ? item.images[0] : item.image})` }}></div>
                        <div>
                          <p className="font-bold m-0">{item.name}</p>
                          <p className="text-xs text-secondary m-0">{item.id}</p>
                        </div>
                      </div>
                    </td>
                    <td>{categories.find(c => c.id === item.categoryId)?.name || item.categoryId}</td>
                    <td>{item.stall}</td>
                    <td className="font-bold">₹{item.price}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <span className={`font-bold ${item.stock <= (item.lowStockThreshold || 5) ? 'text-warning' : ''} ${item.stock === 0 ? 'text-danger' : ''}`}>
                          {item.stock}
                        </span>
                        <button className="text-xs text-primary underline" onClick={() => { setStockItem(item); setStockInput(item.stock); setIsStockModalOpen(true); }}>Edit</button>
                      </div>
                    </td>
                    <td>
                      <span className={`status-badge text-${opStatus.color} bg-${opStatus.color}-light`}>
                        {opStatus.icon} {opStatus.label}
                      </span>
                    </td>
                    <td>
                      <label className="toggle-switch">
                        <input type="checkbox" checked={item.isAvailable} onChange={() => toggleAvailability(item)} />
                        <span className="slider"></span>
                      </label>
                    </td>
                    <td className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button className="btn-icon" title="Edit Item" onClick={() => { 
                          setEditingItem(item); 
                          setEditImages(item.images && item.images.length > 0 ? [...item.images] : [item.image || '']);
                          setIsEditModalOpen(true); 
                        }}><Edit size={16}/></button>
                        <button className="btn-icon danger" title="Deactivate Item" onClick={() => deactivateItem(item)}><Power size={16}/></button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {filteredItems.length === 0 && (
                <tr>
                  <td colSpan="8" className="p-8 text-center text-secondary">No food items found.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* MODALS */}
      {/* Edit/Add Food Modal */}
      {isEditModalOpen && (
        <div className="modal-overlay">
          <div className="modal card w-full max-w-3xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold m-0">{editingItem ? 'Edit Food Item' : 'Add New Food Item'}</h2>
              <button className="btn-icon" onClick={() => setIsEditModalOpen(false)}><X size={20}/></button>
            </div>
            
            <form onSubmit={saveFoodItem}>
              <div className="grid grid-cols-2 gap-6">
                {/* Basic Info */}
                <div className="col-span-2"><h4 className="text-secondary uppercase text-sm tracking-wider m-0 mb-2 border-b border-border pb-2">Basic Information</h4></div>
                <div className="form-group">
                  <label>Food Name</label>
                  <input type="text" name="name" className="input-field" defaultValue={editingItem?.name} required />
                </div>
                <div className="form-group">
                  <label>Dietary Type</label>
                  <select name="vegStatus" className="input-field" defaultValue={editingItem?.vegStatus || 'VEG'}>
                    <option value="VEG">Vegetarian</option>
                    <option value="NON-VEG">Non-Vegetarian</option>
                    <option value="EGG">Egg</option>
                  </select>
                </div>
                
                {/* Classification */}
                <div className="col-span-2 mt-2"><h4 className="text-secondary uppercase text-sm tracking-wider m-0 mb-2 border-b border-border pb-2">Classification</h4></div>
                <div className="form-group">
                  <label>Category</label>
                  <select name="categoryId" className="input-field" defaultValue={editingItem?.categoryId || 'meals'}>
                    {categories.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Fulfillment Stall</label>
                  <select name="stall" className="input-field" defaultValue={editingItem?.stall || 'Main Canteen'}>
                    <option value="Main Canteen">Main Canteen</option>
                    <option value="South Indian Stall">South Indian Stall</option>
                    <option value="North Indian Stall">North Indian Stall</option>
                    <option value="Snacks Stall">Snacks Stall</option>
                    <option value="Beverage Stall">Beverage Stall</option>
                  </select>
                </div>

                {/* Operations */}
                <div className="col-span-2 mt-2"><h4 className="text-secondary uppercase text-sm tracking-wider m-0 mb-2 border-b border-border pb-2">Pricing & Inventory</h4></div>
                <div className="form-group">
                  <label>Price (₹)</label>
                  <input type="number" name="price" className="input-field" defaultValue={editingItem?.price} required min="0" />
                </div>
                <div className="form-group">
                  <label>Current Stock</label>
                  <input type="number" name="stock" className="input-field" defaultValue={editingItem?.stock} required min="0" />
                </div>
                <div className="form-group">
                  <label>Low Stock Threshold</label>
                  <input type="number" name="lowStockThreshold" className="input-field" defaultValue={editingItem?.lowStockThreshold || 5} required min="0" />
                </div>
                <div className="form-group">
                  <label>Est. Prep Time (e.g., "10 min")</label>
                  <input type="text" name="preparationTime" className="input-field" defaultValue={editingItem?.preparationTime || '10 min'} required />
                </div>

                {/* Availability */}
                <div className="col-span-2 mt-2"><h4 className="text-secondary uppercase text-sm tracking-wider m-0 mb-2 border-b border-border pb-2">Operational Availability</h4></div>
                <div className="form-group col-span-2">
                  <label>Available for Ordering (Visible in App)</label>
                  <select name="isAvailable" className="input-field" defaultValue={editingItem ? editingItem.isAvailable.toString() : 'true'}>
                    <option value="true">YES - Available to customers</option>
                    <option value="false">NO - Marked Unavailable</option>
                  </select>
                </div>
                
                {/* Images */}
                <div className="col-span-2 mt-2"><h4 className="text-secondary uppercase text-sm tracking-wider m-0 mb-2 border-b border-border pb-2">Food Images</h4></div>
                <div className="col-span-2">
                  <div className="border-2 border-dashed border-border rounded-xl p-8 text-center bg-background">
                    <div className="mb-4 text-secondary">
                      <p className="font-bold">Upload Food Images</p>
                      <p className="text-sm">JPG, PNG, WEBP (Max 5MB)</p>
                    </div>
                    <label className="btn btn-outline cursor-pointer inline-block">
                      Browse Files
                      <input type="file" multiple accept="image/*" className="hidden" onChange={handleImageUpload} />
                    </label>
                  </div>
                  
                  {editImages.length > 0 && (
                    <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                      {editImages.map((img, idx) => (
                        <div key={idx} className={`relative rounded-lg overflow-hidden border-2 ${idx === 0 ? 'border-primary' : 'border-border'}`}>
                          <img src={img} alt="preview" className="w-full h-32 object-cover" />
                          {idx === 0 && (
                            <div className="absolute top-0 left-0 bg-primary text-white text-xs font-bold px-2 py-1">
                              PRIMARY
                            </div>
                          )}
                          <div className="absolute bottom-0 left-0 right-0 bg-dark bg-opacity-70 p-1 flex justify-between">
                            {idx !== 0 ? (
                              <button type="button" className="text-xs text-white hover:text-primary px-1" onClick={() => setPrimaryImage(idx)}>Make Primary</button>
                            ) : <span></span>}
                            <button type="button" className="text-xs text-danger hover:text-white px-1" onClick={() => removeImage(idx)}>Remove</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

              </div>
              
              <div className="flex justify-end gap-4 mt-8 pt-6 border-t border-border">
                <button type="button" className="btn btn-outline" onClick={() => setIsEditModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary px-8">Save Food Item</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Stock Quick Update Modal */}
      {isStockModalOpen && (
        <div className="modal-overlay">
          <div className="modal card max-w-sm">
            <h3 className="text-xl font-bold mb-4">Adjust Stock</h3>
            <p className="text-secondary text-sm mb-4">Updating inventory for <strong>{stockItem?.name}</strong>.</p>
            <form onSubmit={updateStock}>
              <div className="form-group">
                <label>New Stock Quantity</label>
                <input 
                  type="number" 
                  className="input-field text-xl font-bold" 
                  value={stockInput} 
                  onChange={e => setStockInput(e.target.value)} 
                  required 
                  min="0"
                />
              </div>
              <div className="flex gap-2 mt-6">
                <button type="button" className="btn btn-outline flex-1" onClick={() => setIsStockModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary flex-1">Update</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
