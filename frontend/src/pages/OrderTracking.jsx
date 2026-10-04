import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle2, Clock, MapPin, ChefHat, PackageCheck, ArrowLeft } from 'lucide-react';
import { orderService } from '../services/orderService';
import './OrderTracking.css';

export default function OrderTracking() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrder();
    // Simulate real-time polling
    const interval = setInterval(fetchOrder, 3000);
    return () => clearInterval(interval);
  }, [id]);

  const fetchOrder = async () => {
    const data = await orderService.getOrder(id);
    if (data) setOrder(data);
    setLoading(false);
  };

  if (loading) return <div className="tracking-page flex items-center justify-center min-h-screen">Loading...</div>;
  if (!order) return <div className="tracking-page p-6">Order not found.</div>;

  const stages = [
    { id: 'QUEUED', label: 'Order Placed', icon: <CheckCircle2 size={24}/> },
    { id: 'PREPARING', label: 'Preparing', icon: <ChefHat size={24}/> },
    { id: 'READY', label: 'Ready for Pickup', icon: <PackageCheck size={24}/> }
  ];

  const currentStageIndex = stages.findIndex(s => s.id === order.status);

  return (
    <div className="tracking-page">
      <div className="tracking-container">
        
        <button className="btn-back mb-6" onClick={() => navigate('/customer/ordering')}>
          <ArrowLeft size={16}/> Back to Menu
        </button>

        <div className="status-header">
          <div className="status-badge-large">
            {order.status === 'READY' ? (
              <><span className="live-dot-green"></span> ORDER READY</>
            ) : (
              <><span className="live-dot"></span> LIVE TRACKING</>
            )}
          </div>
          <h1 className="order-id">{order.id}</h1>
          <p className="order-date">{new Date(order.createdAt).toLocaleString()}</p>
        </div>

        <div className="tracking-card">
          <div className="timeline">
            {stages.map((stage, index) => {
              const isCompleted = index <= currentStageIndex;
              const isCurrent = index === currentStageIndex;
              return (
                <div key={stage.id} className={`timeline-stage ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''}`}>
                  <div className="stage-icon">
                    {stage.icon}
                  </div>
                  <div className="stage-content">
                    <h3>{stage.label}</h3>
                    {isCurrent && stage.id === 'PREPARING' && <p>Kitchen has started preparing your order.</p>}
                    {isCurrent && stage.id === 'READY' && <p className="text-success font-bold">Please collect your order!</p>}
                  </div>
                  {index < stages.length - 1 && <div className="stage-connector"></div>}
                </div>
              );
            })}
          </div>

          <div className="order-info-grid">
            <div className="info-box">
              <Clock className="text-primary mb-2" />
              <h4>Estimated Ready</h4>
              <p>{new Date(order.estimatedReadyTime).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
            </div>
            <div className="info-box">
              <MapPin className="text-primary mb-2" />
              <h4>Pickup Stall</h4>
              <p>{order.pickupStall}</p>
            </div>
          </div>
        </div>

        <div className="order-details-card mt-6">
          <h3 className="mb-4">Order Details</h3>
          <div className="details-list">
            {order.items.map(item => (
              <div key={item.id} className="detail-item">
                <span className="qty">{item.quantity} ×</span>
                <span className="name">{item.name}</span>
                <span className="price">₹{item.price * item.quantity}</span>
              </div>
            ))}
          </div>
          <div className="details-total">
            <span>Total Paid</span>
            <span>₹{order.totalAmount}</span>
          </div>
        </div>

      </div>
    </div>
  );
}
