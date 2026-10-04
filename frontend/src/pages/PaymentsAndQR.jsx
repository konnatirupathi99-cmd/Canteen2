import React, { useState, useEffect } from 'react';
import { QrCode, Settings, RefreshCw, Download, PlayCircle, ShieldCheck, CheckCircle2, Clock, AlertTriangle, XCircle, CreditCard, Search } from 'lucide-react';
import { paymentService } from '../services/paymentService';

export default function PaymentsAndQR() {
  const [config, setConfig] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    const [cfg, data] = await Promise.all([
      paymentService.getPaymentConfig(),
      paymentService.getPaymentsAnalytics()
    ]);
    setConfig(cfg);
    setEditForm(cfg || {});
    setAnalytics(data);
    setLoading(false);
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    const updated = await paymentService.updatePaymentConfig(editForm);
    setConfig(updated);
    setIsEditing(false);
  };

  if (loading) return <div className="p-8 text-center">Loading Payment Config...</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold">Payments & QR Configuration</h1>
          <p className="text-secondary">Manage official canteen payment methods, QR codes, and digital transactions.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setIsEditing(true)}>
          <Settings size={16} /> CONFIGURE PAYMENT METHOD
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Col: QR Display & Config */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card text-center border-2 border-primary">
            <h3 className="section-title text-primary mb-4">CANTEEN PAYMENT QR</h3>
            
            <div className="bg-white p-4 rounded-xl shadow-sm inline-block mb-4 border border-border relative">
              <img src={config?.qrImageUrl} alt="Payment QR" className="w-48 h-48 object-contain mx-auto" />
              {config?.status !== 'ACTIVE' && (
                <div className="absolute inset-0 bg-white bg-opacity-80 flex items-center justify-center font-bold text-danger">
                  DISABLED
                </div>
              )}
            </div>
            
            <div className="mb-4">
              <h4 className="font-bold text-lg">{config?.displayName || 'Main Campus Canteen'}</h4>
              <p className="text-secondary text-sm">ABC Institute of Technology</p>
              <p className="text-xs text-primary font-bold mt-1">Canteen ID: {config?.canteenId}</p>
            </div>

            <div className="flex items-center justify-center gap-2 mb-6">
              <span className="text-sm font-bold text-secondary">Status:</span>
              <span className={`status-badge ${config?.status === 'ACTIVE' ? 'bg-success-light text-success' : 'bg-danger-light text-danger'}`}>
                {config?.status === 'ACTIVE' ? '● ACTIVE' : '○ INACTIVE'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button className="btn btn-outline text-xs p-2 flex flex-col items-center justify-center"><RefreshCw size={16} className="mb-1"/> Replace QR</button>
              <button className="btn btn-outline text-xs p-2 flex flex-col items-center justify-center"><Download size={16} className="mb-1"/> Download</button>
              <button className="btn btn-outline text-xs p-2 flex flex-col items-center justify-center"><PlayCircle size={16} className="mb-1"/> Test Payment</button>
              <button 
                className="btn btn-outline text-xs p-2 flex flex-col items-center justify-center text-danger border-danger hover:bg-danger-light"
                onClick={async () => {
                  const s = config.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
                  const updated = await paymentService.updatePaymentConfig({ status: s });
                  setConfig(updated);
                }}
              >
                <XCircle size={16} className="mb-1"/> {config?.status === 'ACTIVE' ? 'Disable' : 'Enable'}
              </button>
            </div>
          </div>
          
          <div className="card bg-success-light border border-success flex gap-4 items-start">
            <ShieldCheck className="text-success mt-1" size={24}/>
            <div>
              <h4 className="font-bold text-success text-sm mb-1">Payment Security Active</h4>
              <p className="text-xs text-success">End-to-end webhook verification is enabled. Transactions are atomic and idempotency keys are enforced.</p>
            </div>
          </div>
        </div>

        {/* Right Col: Analytics & Transactions */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Summary Cards */}
          <div className="grid grid-cols-4 gap-4">
            <div className="card p-4 border-l-4 border-primary">
              <h4 className="text-xs text-secondary uppercase font-bold mb-1">Today's Revenue</h4>
              <h2 className="text-2xl m-0">₹{analytics?.totalRevenue.toLocaleString()}</h2>
            </div>
            <div className="card p-4 border-l-4 border-success">
              <h4 className="text-xs text-secondary uppercase font-bold mb-1">Successful</h4>
              <h2 className="text-2xl m-0 text-success">{analytics?.successfulCount}</h2>
            </div>
            <div className="card p-4 border-l-4 border-warning">
              <h4 className="text-xs text-secondary uppercase font-bold mb-1">Pending</h4>
              <h2 className="text-2xl m-0 text-warning">{analytics?.pendingCount}</h2>
            </div>
            <div className="card p-4 border-l-4 border-danger">
              <h4 className="text-xs text-secondary uppercase font-bold mb-1">Failed</h4>
              <h2 className="text-2xl m-0 text-danger">{analytics?.failedCount}</h2>
            </div>
          </div>

          {/* Transactions List */}
          <div className="card table-card flex-1 min-h-[400px]">
            <div className="p-4 border-b border-border flex justify-between items-center">
              <h3 className="section-title m-0">Recent Digital Payments</h3>
              <div className="flex gap-2">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-2.5 text-secondary" />
                  <input type="text" className="input-field text-sm pl-8 py-1 h-9" placeholder="Search Order ID..." />
                </div>
              </div>
            </div>
            
            <table className="manager-table w-full">
              <thead>
                <tr>
                  <th>PAYMENT ID</th>
                  <th>ORDER ID</th>
                  <th>CUSTOMER</th>
                  <th>METHOD</th>
                  <th className="text-right">AMOUNT</th>
                  <th className="text-right">STATUS</th>
                </tr>
              </thead>
              <tbody>
                {analytics?.recentPayments.length === 0 && (
                  <tr><td colSpan="6" className="text-center p-8 text-secondary">No digital payments recorded today.</td></tr>
                )}
                {analytics?.recentPayments.map(p => (
                  <tr key={p.id}>
                    <td className="font-mono text-xs">{p.id}</td>
                    <td className="font-bold text-primary">{p.orderId || '-'}</td>
                    <td>{p.userName}</td>
                    <td>
                      <span className="flex items-center gap-1 text-xs bg-surface px-2 py-1 rounded border border-border inline-flex">
                        {p.method === 'UPI' ? <QrCode size={12}/> : <CreditCard size={12}/>}
                        {p.method}
                      </span>
                    </td>
                    <td className="text-right font-bold">₹{p.amount}</td>
                    <td className="text-right">
                      {p.status === 'SUCCESS' && <span className="status-badge bg-success-light text-success"><CheckCircle2 size={12}/> SUCCESS</span>}
                      {p.status === 'PENDING' && <span className="status-badge bg-warning-light text-warning"><Clock size={12}/> PENDING</span>}
                      {p.status === 'FAILED' && <span className="status-badge bg-danger-light text-danger"><AlertTriangle size={12}/> FAILED</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

        </div>
      </div>

      {/* Edit Config Modal */}
      {isEditing && (
        <div className="modal-overlay">
          <div className="modal card w-full max-w-lg">
            <h2 className="text-xl font-bold mb-4">Configure Payment Method</h2>
            <form onSubmit={handleSaveConfig}>
              <div className="space-y-4">
                <div className="form-group">
                  <label>Provider (e.g., UPI, Razorpay, PhonePe)</label>
                  <input type="text" className="input-field" value={editForm.provider} onChange={e => setEditForm({...editForm, provider: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Display Name (Visible to Customers)</label>
                  <input type="text" className="input-field" value={editForm.displayName} onChange={e => setEditForm({...editForm, displayName: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Merchant Reference / UPI ID</label>
                  <input type="text" className="input-field" value={editForm.merchantReference} onChange={e => setEditForm({...editForm, merchantReference: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>QR Image URL</label>
                  <input type="text" className="input-field" value={editForm.qrImageUrl} onChange={e => setEditForm({...editForm, qrImageUrl: e.target.value})} />
                </div>
                
                <div className="bg-warning-light border border-warning p-3 rounded-lg text-sm text-dark mt-4">
                  <strong>Security Note:</strong> Never store sensitive API secrets (like webhook secrets or client secrets) here. Configure those in the backend `.env`.
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-border">
                <button type="button" className="btn btn-outline" onClick={() => setIsEditing(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save Configuration</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
