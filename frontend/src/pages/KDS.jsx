import React, { useState } from 'react';
import { Clock, CheckCircle, ChefHat } from 'lucide-react';
import './KDS.css';

const INITIAL_ORDERS = [
  { id: '#1024', status: 'NEW', items: ['2 × Veg Meals', '1 × Tea'], receivedAt: new Date(Date.now() - 60000) },
  { id: '#1025', status: 'PREPARING', items: ['1 × Chicken Rice', '1 × Fresh Lime'], receivedAt: new Date(Date.now() - 300000) },
  { id: '#1026', status: 'NEW', items: ['3 × Samosa'], receivedAt: new Date(Date.now() - 20000) },
  { id: '#1027', status: 'READY', items: ['2 × Dosa'], receivedAt: new Date(Date.now() - 600000) },
];

export default function KDS() {
  const [orders, setOrders] = useState(INITIAL_ORDERS);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Simple clock updater
  React.useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const updateStatus = (id, newStatus) => {
    setOrders(prev => prev.map(o => {
      if (o.id === id) {
        return { ...o, status: newStatus };
      }
      return o;
    }));
  };

  const getElapsed = (startTime) => {
    const diff = Math.floor((currentTime - startTime) / 1000);
    const m = Math.floor(diff / 60).toString().padStart(2, '0');
    const s = (diff % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="kds-container">
      <div className="kds-columns">
        
        {/* NEW ORDERS */}
        <div className="kds-column">
          <h3 className="kds-col-title new">NEW <span className="count">{orders.filter(o => o.status === 'NEW').length}</span></h3>
          <div className="kds-order-list">
            {orders.filter(o => o.status === 'NEW').map(order => (
              <div key={order.id} className="kds-card card">
                <div className="kds-card-header">
                  <span className="order-num">{order.id}</span>
                  <span className="elapsed-time"><Clock size={14}/> {getElapsed(order.receivedAt)}</span>
                </div>
                <ul className="kds-items">
                  {order.items.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
                <div className="kds-actions">
                  <button className="btn btn-primary" onClick={() => updateStatus(order.id, 'PREPARING')}>
                    START PREPARING
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* PREPARING */}
        <div className="kds-column">
          <h3 className="kds-col-title preparing">PREPARING <span className="count">{orders.filter(o => o.status === 'PREPARING').length}</span></h3>
          <div className="kds-order-list">
            {orders.filter(o => o.status === 'PREPARING').map(order => (
              <div key={order.id} className="kds-card card preparing-card">
                <div className="kds-card-header">
                  <span className="order-num">{order.id}</span>
                  <span className="elapsed-time warning"><Clock size={14}/> {getElapsed(order.receivedAt)}</span>
                </div>
                <ul className="kds-items">
                  {order.items.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
                <div className="kds-actions">
                  <button className="btn btn-success" onClick={() => updateStatus(order.id, 'READY')}>
                    <CheckCircle size={16}/> MARK READY
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* READY */}
        <div className="kds-column">
          <h3 className="kds-col-title ready">READY <span className="count">{orders.filter(o => o.status === 'READY').length}</span></h3>
          <div className="kds-order-list">
            {orders.filter(o => o.status === 'READY').map(order => (
              <div key={order.id} className="kds-card card ready-card">
                <div className="kds-card-header">
                  <span className="order-num">{order.id}</span>
                  <span className="elapsed-time success"><ChefHat size={14}/> Ready</span>
                </div>
                <ul className="kds-items">
                  {order.items.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
                <div className="kds-actions">
                  <button className="btn btn-outline" onClick={() => updateStatus(order.id, 'FULFILLED')}>
                    FULFILL
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
