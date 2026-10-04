import React, { useState } from 'react';
import { Search, Plus, Filter, Edit, Trash2 } from 'lucide-react';
import './Inventory.css';

const INITIAL_INVENTORY = [
  { id: 1, name: 'Veg Meals', category: 'Meals', stock: 42, threshold: 20, status: 'Healthy', active: true, price: 60 },
  { id: 2, name: 'Idli', category: 'Breakfast', stock: 15, threshold: 20, status: 'Low', active: true, price: 30 },
  { id: 3, name: 'Dosa', category: 'Breakfast', stock: 0, threshold: 15, status: 'Out of Stock', active: false, price: 40 },
  { id: 4, name: 'Vada', category: 'Breakfast', stock: 20, threshold: 15, status: 'Healthy', active: true, price: 25 },
  { id: 5, name: 'Paneer Rice', category: 'Meals', stock: 12, threshold: 10, status: 'Healthy', active: true, price: 80 },
  { id: 6, name: 'Samosa', category: 'Snacks', stock: 5, threshold: 20, status: 'Critical', active: true, price: 20 },
];

export default function Inventory() {
  const [items, setItems] = useState(INITIAL_INVENTORY);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('All');
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  const filteredItems = items.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filter === 'All' ? true : item.status === filter;
    return matchesSearch && matchesFilter;
  });

  const getStatusBadge = (status) => {
    switch(status) {
      case 'Healthy': return <span className="badge badge-success">{status}</span>;
      case 'Low': return <span className="badge badge-warning">{status}</span>;
      case 'Critical': return <span className="badge badge-danger">{status}</span>;
      case 'Out of Stock': return <span className="badge badge-danger">{status}</span>;
      default: return <span className="badge badge-neutral">{status}</span>;
    }
  };

  const calculateStatus = (stock, threshold) => {
    if (stock === 0) return 'Out of Stock';
    if (stock <= threshold * 0.5) return 'Critical';
    if (stock <= threshold) return 'Low';
    return 'Healthy';
  };

  const handleSave = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const newItem = {
      id: editingItem ? editingItem.id : Date.now(),
      name: formData.get('name'),
      category: formData.get('category'),
      price: Number(formData.get('price')),
      stock: Number(formData.get('stock')),
      threshold: Number(formData.get('threshold')),
      active: formData.get('active') === 'on',
    };
    newItem.status = calculateStatus(newItem.stock, newItem.threshold);

    if (editingItem) {
      setItems(prev => prev.map(i => i.id === newItem.id ? newItem : i));
    } else {
      setItems(prev => [...prev, newItem]);
    }
    
    setIsModalOpen(false);
    setEditingItem(null);
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to remove this item?')) {
      setItems(prev => prev.filter(i => i.id !== id));
    }
  };

  const toggleAvailability = (id) => {
    setItems(prev => prev.map(i => {
      if (i.id === id) {
        return { ...i, active: !i.active };
      }
      return i;
    }));
  };

  return (
    <div className="inventory-page">
      <div className="inventory-actions">
        <div className="inventory-filters">
          <div className="search-box">
            <Search size={16} className="search-icon" />
            <input 
              type="text" 
              placeholder="Search items..." 
              className="input-field"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select className="input-field filter-select" value={filter} onChange={e => setFilter(e.target.value)}>
            <option value="All">All Statuses</option>
            <option value="Healthy">Healthy</option>
            <option value="Low">Low Stock</option>
            <option value="Critical">Critical</option>
            <option value="Out of Stock">Out of Stock</option>
          </select>
        </div>
        
        <button className="btn btn-primary" onClick={() => { setEditingItem(null); setIsModalOpen(true); }}>
          <Plus size={16} /> Add Food Item
        </button>
      </div>

      <div className="card table-card">
        <table>
          <thead>
            <tr>
              <th>Food Item</th>
              <th>Category</th>
              <th>Price</th>
              <th>Current Stock</th>
              <th>Threshold</th>
              <th>Status</th>
              <th>Availability</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map(item => (
              <tr key={item.id}>
                <td><strong>{item.name}</strong></td>
                <td>{item.category}</td>
                <td>₹{item.price}</td>
                <td>
                  <div className="stock-progress">
                    <div className="stock-text">{item.stock}</div>
                    <div className="progress-bar">
                      <div 
                        className={`progress-fill ${item.status.toLowerCase().replace(/ /g, '-')}`} 
                        style={{width: `${Math.min((item.stock / (item.threshold * 3)) * 100, 100)}%`}}
                      ></div>
                    </div>
                  </div>
                </td>
                <td>{item.threshold}</td>
                <td>{getStatusBadge(item.status)}</td>
                <td>
                  <label className="toggle-switch">
                    <input type="checkbox" checked={item.active} onChange={() => toggleAvailability(item.id)} />
                    <span className="slider"></span>
                  </label>
                </td>
                <td>
                  <div className="action-buttons">
                    <button className="btn-icon" onClick={() => { setEditingItem(item); setIsModalOpen(true); }}><Edit size={16}/></button>
                    <button className="btn-icon danger" onClick={() => handleDelete(item.id)}><Trash2 size={16}/></button>
                  </div>
                </td>
              </tr>
            ))}
            {filteredItems.length === 0 && (
              <tr>
                <td colSpan="8" className="empty-state">No food items found matching your criteria.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal card">
            <h3 className="modal-title">{editingItem ? 'Edit Food Item' : 'Add Food Item'}</h3>
            <form onSubmit={handleSave}>
              <div className="form-grid grid-cols-2">
                <div className="form-group">
                  <label>Food Name</label>
                  <input name="name" type="text" className="input-field" defaultValue={editingItem?.name} required />
                </div>
                <div className="form-group">
                  <label>Category</label>
                  <select name="category" className="input-field" defaultValue={editingItem?.category || 'Meals'}>
                    <option value="Breakfast">Breakfast</option>
                    <option value="Meals">Meals</option>
                    <option value="Snacks">Snacks</option>
                    <option value="Beverages">Beverages</option>
                    <option value="Desserts">Desserts</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Price (₹)</label>
                  <input name="price" type="number" className="input-field" defaultValue={editingItem?.price} required min="0" />
                </div>
                <div className="form-group">
                  <label>Current Stock</label>
                  <input name="stock" type="number" className="input-field" defaultValue={editingItem?.stock} required min="0" />
                </div>
                <div className="form-group">
                  <label>Low Stock Threshold</label>
                  <input name="threshold" type="number" className="input-field" defaultValue={editingItem?.threshold} required min="1" />
                </div>
                <div className="form-group flex-align-center">
                  <label className="toggle-container">
                    <input name="active" type="checkbox" defaultChecked={editingItem ? editingItem.active : true} />
                    <span>Available in POS</span>
                  </label>
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-outline" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save Item</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
