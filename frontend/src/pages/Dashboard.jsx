import React from 'react';
import { Utensils, TrendingUp, AlertTriangle, Activity, PackageX, Users, Clock, MonitorStop } from 'lucide-react';
import './Dashboard.css';

const kpis = [
  { title: "ACTIVE ORDERS", value: "128", trend: "+12.4%", status: "success", icon: <Utensils size={24}/> },
  { title: "READY ORDERS", value: "24", trend: "Steady", status: "info", icon: <MonitorStop size={24}/> },
  { title: "LOW STOCK ITEMS", value: "8", trend: "+2", status: "warning", icon: <AlertTriangle size={24}/> },
  { title: "TODAY'S REVENUE", value: "₹42,500", trend: "+8.1%", status: "success", icon: <TrendingUp size={24}/> },
  { title: "KITCHEN LOAD", value: "85%", trend: "High", status: "warning", icon: <Activity size={24}/> },
  { title: "ACTIVE STALLS", value: "4/5", trend: "1 Offline", status: "neutral", icon: <Users size={24}/> },
  { title: "QUEUE WAIT TIME", value: "8m 12s", trend: "-1m", status: "success", icon: <Clock size={24}/> },
  { title: "SYSTEM HEALTH", value: "99.9%", trend: "Optimal", status: "success", icon: <Activity size={24}/> },
];

const liveOrders = [
  { id: '#1024', items: '2 × Veg Meals, 1 × Tea', status: 'Preparing', time: '2m ago' },
  { id: '#1025', items: '1 × Chicken Rice', status: 'Ready', time: '4m ago' },
  { id: '#1026', items: '3 × Samosa', status: 'Queued', time: 'Just now' },
  { id: '#1027', items: '2 × Dosa', status: 'Queued', time: 'Just now' }
];

const stockAlerts = [
  { item: 'Tomato', status: 'Critical', desc: '8 units remaining' },
  { item: 'Paneer', status: 'Low', desc: '14 units remaining' },
  { item: 'Veg Meals', status: 'Out of stock', desc: '0 units remaining', isDanger: true }
];

export default function Dashboard() {
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h3>Good Morning, Administrator</h3>
          <p className="text-secondary">Live Canteen Operations • {new Date().toLocaleDateString()}</p>
        </div>
      </div>
      
      <div className="kpi-grid grid-cols-4">
        {kpis.map((kpi, idx) => (
          <div key={idx} className="card kpi-card">
            <div className="kpi-header">
              <span className="kpi-title">{kpi.title}</span>
              <div className={`kpi-icon ${kpi.status}`}>{kpi.icon}</div>
            </div>
            <div className="kpi-value">{kpi.value}</div>
            <div className={`kpi-trend trend-${kpi.status}`}>{kpi.trend} vs previous hour</div>
          </div>
        ))}
      </div>

      <div className="dashboard-content grid-cols-3">
        <div className="card span-2">
          <h4 className="card-title">Real-Time Order Flow</h4>
          <div className="order-list">
            {liveOrders.map((order, idx) => (
              <div key={idx} className="order-row">
                <div className="order-id">{order.id}</div>
                <div className="order-items">{order.items}</div>
                <div className="order-status">
                  <span className={`badge badge-${order.status === 'Ready' ? 'success' : order.status === 'Preparing' ? 'warning' : 'info'}`}>
                    {order.status}
                  </span>
                </div>
                <div className="order-time">{order.time}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h4 className="card-title">Stock Alerts</h4>
          <div className="alert-list">
            {stockAlerts.map((alert, idx) => (
              <div key={idx} className={`alert-item ${alert.isDanger ? 'alert-danger' : 'alert-warning'}`}>
                <div className="alert-header">
                  <AlertTriangle size={16} />
                  <strong>{alert.item}</strong>
                  <span className="alert-status">{alert.status}</span>
                </div>
                <p className="alert-desc">{alert.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
