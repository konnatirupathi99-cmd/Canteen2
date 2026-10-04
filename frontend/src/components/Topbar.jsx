import React from 'react';
import { Bell, Search, User, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import './Topbar.css';

export default function Topbar({ title = 'Operations Command Center' }) {
  const navigate = useNavigate();
  const user = authService.getCurrentUser() || { name: 'Admin', role: 'Administrator' };

  const handleLogout = () => {
    authService.logout();
    navigate('/auth');
  };

  return (
    <header className="topbar">
      <div className="topbar-left">
        <h2 className="page-title">{title}</h2>
      </div>
      
      <div className="topbar-center">
        <div className="search-bar">
          <Search size={16} className="search-icon" />
          <input type="text" placeholder="Global search..." className="search-input" />
        </div>
      </div>
      
      <div className="topbar-right">
        <div className="system-health">
          <span className="live-indicator"></span>
          <span className="health-text">System Healthy</span>
        </div>
        
        <button className="icon-btn">
          <Bell size={20} />
          <span className="notification-badge">4</span>
        </button>
        
        <div className="user-profile">
          <div className="avatar">
            <User size={18} />
          </div>
          <div className="user-info">
            <span className="user-name">{user.name}</span>
            <span className="user-role">{user.role}</span>
          </div>
        </div>

        <button className="icon-btn logout-btn" onClick={handleLogout} title="Logout">
          <LogOut size={20} />
        </button>
      </div>
    </header>
  );
}
