import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import './Layout.css';

const getPageTitle = (pathname) => {
  const titles = {
    '/': 'Operations Command Center',
    '/pos': 'Point of Sale',
    '/orders': 'Active Orders',
    '/kds': 'Kitchen Display System',
    '/inventory': 'Inventory Management',
    '/digital-twin': 'Operational Digital Twin',
    '/automation': 'Automation Center',
    '/incidents': 'Incident Center',
    '/health': 'System Health',
    '/settings': 'Administration'
  };
  return titles[pathname] || 'CanteenOS';
};

export default function Layout() {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-wrapper">
        <Topbar title={getPageTitle(location.pathname)} />
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
