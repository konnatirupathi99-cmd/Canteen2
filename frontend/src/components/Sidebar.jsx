import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, ShoppingCart, ListOrdered, ChefHat, 
  PackageSearch, Activity, BrainCircuit, Box, ShieldAlert, Users, MessageSquare
} from 'lucide-react';
import './Sidebar.css';

const navSections = [
  {
    title: 'OVERVIEW',
    items: [
      { name: 'Dashboard', path: '/', icon: <LayoutDashboard size={18} /> }
    ]
  },
  {
    title: 'OPERATIONS',
    items: [
      { name: 'POS', path: '/pos', icon: <ShoppingCart size={18} /> },
      { name: 'Orders', path: '/orders', icon: <ListOrdered size={18} /> },
      { name: 'Kitchen Display', path: '/kds', icon: <ChefHat size={18} /> }
    ]
  },
  {
    title: 'INVENTORY',
    items: [
      { name: 'Food Items', path: '/inventory', icon: <PackageSearch size={18} /> },
      { name: 'Feedback & Reviews', path: '/feedback', icon: <MessageSquare size={18} /> }
    ]
  },
  {
    title: 'INTELLIGENCE',
    items: [
      { name: 'Digital Twin', path: '/digital-twin', icon: <Box size={18} /> },
      { name: 'Automation', path: '/automation', icon: <BrainCircuit size={18} /> }
    ]
  },
  {
    title: 'MONITORING',
    items: [
      { name: 'Incidents', path: '/incidents', icon: <ShieldAlert size={18} /> },
      { name: 'System Health', path: '/health', icon: <Activity size={18} /> }
    ]
  },
  {
    title: 'ADMINISTRATION',
    items: [
      { name: 'Settings', path: '/settings', icon: <Users size={18} /> }
    ]
  }
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1 className="brand-title">CanteenOS</h1>
      </div>
      
      <div className="sidebar-navs">
        {navSections.map((section, idx) => (
          <div key={idx} className="nav-section">
            <h4 className="nav-section-title">{section.title}</h4>
            <ul className="nav-list">
              {section.items.map((item, i) => (
                <li key={i}>
                  <NavLink 
                    to={item.path} 
                    className={({isActive}) => isActive ? "nav-item active" : "nav-item"}
                  >
                    {item.icon}
                    <span>{item.name}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </aside>
  );
}
