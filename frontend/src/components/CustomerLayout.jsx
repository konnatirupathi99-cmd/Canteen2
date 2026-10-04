import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { ShoppingBag, Heart, Clock, User, LogOut, Bell } from 'lucide-react';
import { authService } from '../services/authService';
import './CustomerLayout.css';

export default function CustomerLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = authService.getCurrentUser();

  const handleLogout = () => {
    authService.logout();
    navigate('/auth');
  };

  const navItems = [
    { path: '/customer/ordering', label: 'Order Food', icon: <ShoppingBag size={20} /> },
    { path: '/customer/favorites', label: 'Favorites', icon: <Heart size={20} /> },
    { path: '/customer/orders', label: 'My Orders', icon: <Clock size={20} /> }
  ];

  return (
    <div className="customer-layout">
      {/* Top Navigation */}
      <header className="customer-header">
        <div className="customer-header-inner">
          <div className="brand-logo-small cursor-pointer" onClick={() => navigate('/customer/ordering')}>
            CANTEEN<span className="text-primary">OS</span>
          </div>

          <nav className="desktop-nav">
            {navItems.map(item => (
              <button 
                key={item.path}
                className={`nav-btn ${location.pathname.startsWith(item.path) ? 'active' : ''}`}
                onClick={() => navigate(item.path)}
              >
                {item.icon} {item.label}
              </button>
            ))}
          </nav>

          <div className="header-actions">
            <button className="icon-btn relative">
              <Bell size={20} />
              <span className="notification-badge">2</span>
            </button>
            <div className="user-profile-menu">
              <div className="avatar">
                <User size={18} />
              </div>
              <div className="user-info hidden-mobile">
                <span className="user-name">{user?.name || 'Student'}</span>
                <span className="user-role">{user?.role || 'STUDENT'}</span>
              </div>
            </div>
            <button className="icon-btn logout-btn" onClick={handleLogout} title="Logout">
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="customer-main">
        <Outlet />
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="mobile-bottom-nav">
        {navItems.map(item => (
          <button 
            key={item.path}
            className={`mobile-nav-btn ${location.pathname.startsWith(item.path) ? 'active' : ''}`}
            onClick={() => navigate(item.path)}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
