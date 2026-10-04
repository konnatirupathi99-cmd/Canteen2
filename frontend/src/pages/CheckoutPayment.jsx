import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Lock, ShieldCheck, CheckCircle2, AlertTriangle, QrCode, CreditCard, ChevronLeft } from 'lucide-react';
import { paymentService } from '../services/paymentService';

export default function CheckoutPayment() {
  const navigate = useNavigate();
  const location = useLocation();
  const cart = location.state?.cart || [];
  
  const [checkoutSession, setCheckoutSession] = useState(null);
  const [paymentConfig, setPaymentConfig] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('UPI');
  const [paymentState, setPaymentState] = useState('READY'); // READY, PROCESSING, SUCCESS, FAILED
  const [errorMsg, setErrorMsg] = useState(null);
  const [successData, setSuccessData] = useState(null);
  
  useEffect(() => {
    if (cart.length === 0) {
      navigate('/customer/ordering');
      return;
    }
    initializeCheckout();
  }, [cart, navigate]);

  const initializeCheckout = async () => {
    try {
      const config = await paymentService.getPaymentConfig();
      setPaymentConfig(config);
      
      const session = await paymentService.initiateCheckout(cart);
      setCheckoutSession(session);
    } catch (err) {
      setErrorMsg(err);
      setPaymentState('FAILED');
    }
  };

  const handlePayNow = async () => {
    if (!checkoutSession) return;
    
    setPaymentState('PROCESSING');
    setErrorMsg(null);

    try {
      const result = await paymentService.processPayment(
        checkoutSession.checkoutId,
        checkoutSession.total,
        paymentMethod,
        cart
      );
      setSuccessData(result);
      setPaymentState('SUCCESS');
    } catch (err) {
      setErrorMsg(err);
      setPaymentState('FAILED');
    }
  };

  const handleCancel = async () => {
    if (paymentState === 'SUCCESS') return;
    if (checkoutSession) {
      await paymentService.cancelCheckout(cart);
    }
    navigate('/customer/ordering', { state: { cart } });
  };

  if (!checkoutSession && paymentState !== 'FAILED') {
    return (
      <div className="flex items-center justify-center min-h-[60vh] flex-col">
        <div className="spinner border-primary border-t-transparent w-8 h-8 rounded-full border-4 animate-spin mb-4"></div>
        <p className="text-secondary font-bold">Validating order and inventory...</p>
      </div>
    );
  }

  // SUCCESS STATE
  if (paymentState === 'SUCCESS') {
    return (
      <div className="max-w-2xl mx-auto mt-8">
        <div className="card text-center py-12 border-t-8 border-t-success">
          <div className="w-20 h-20 bg-success-light text-success rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 size={48} />
          </div>
          <h1 className="text-3xl font-bold mb-2">PAYMENT SUCCESSFUL</h1>
          <h3 className="text-xl text-primary font-bold mb-6">ORDER CONFIRMED</h3>
          
          <div className="bg-surface rounded-xl p-6 text-left max-w-sm mx-auto border border-border mb-8">
            <div className="flex justify-between mb-2">
              <span className="text-secondary">Pickup Token</span>
              <span className="font-bold text-xl">{successData?.token}</span>
            </div>
            <div className="flex justify-between mb-2">
              <span className="text-secondary">Amount Paid</span>
              <span className="font-bold">₹{checkoutSession.total}</span>
            </div>
            <div className="flex justify-between mb-2">
              <span className="text-secondary">Payment ID</span>
              <span className="font-mono text-sm">{successData?.paymentId}</span>
            </div>
            <div className="flex justify-between mb-4 pb-4 border-b border-border">
              <span className="text-secondary">Order ID</span>
              <span className="font-mono text-sm">{successData?.orderId}</span>
            </div>
            <p className="text-center text-sm font-bold text-dark">Estimated Ready Time: 10–15 minutes</p>
          </div>

          <button 
            className="btn btn-primary px-12"
            onClick={() => navigate(`/customer/orders/${successData?.orderId}`)}
          >
            TRACK ORDER
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto mt-6 px-4">
      <button className="btn btn-outline mb-6 border-none text-secondary hover:text-primary pl-0" onClick={handleCancel}>
        <ChevronLeft size={20}/> Back to Cart
      </button>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Order Summary */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold">Order Summary</h2>
          <div className="card bg-surface border border-border">
            <div className="space-y-4 mb-4 pb-4 border-b border-border">
              {cart.map(item => (
                <div key={item.id} className="flex justify-between">
                  <div>
                    <span className="font-bold text-dark">{item.name}</span>
                    <span className="text-secondary text-sm ml-2">× {item.quantity}</span>
                  </div>
                  <span className="font-medium">₹{item.price * item.quantity}</span>
                </div>
              ))}
            </div>
            <div className="space-y-2 mb-4 pb-4 border-b border-border text-sm">
              <div className="flex justify-between">
                <span className="text-secondary">Subtotal</span>
                <span>₹{checkoutSession?.subtotal}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary">Taxes (5%)</span>
                <span>₹{checkoutSession?.taxes}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary">Convenience Fee</span>
                <span>₹{checkoutSession?.convenienceFee}</span>
              </div>
            </div>
            <div className="flex justify-between items-center text-xl font-bold text-primary">
              <span>TOTAL</span>
              <span>₹{checkoutSession?.total}</span>
            </div>
          </div>
          
          <div className="bg-success-light border border-success rounded-lg p-3 text-sm text-success flex gap-2 items-start">
            <Lock size={16} className="mt-0.5 shrink-0" />
            <p>Your items have been reserved. Please complete payment within 5 minutes to confirm your order.</p>
          </div>
        </div>

        {/* Payment Methods */}
        <div>
          <h2 className="text-2xl font-bold mb-6">Payment</h2>
          
          {paymentState === 'FAILED' ? (
            <div className="card border-danger text-center py-8">
              <AlertTriangle size={48} className="text-danger mx-auto mb-4" />
              <h3 className="text-lg font-bold text-danger mb-2">Payment Unsuccessful</h3>
              <p className="text-secondary mb-6">{errorMsg || 'Your payment could not be confirmed.'}</p>
              <div className="flex gap-4 justify-center">
                <button className="btn btn-outline" onClick={handleCancel}>Return to Cart</button>
                <button className="btn btn-primary" onClick={() => { setPaymentState('READY'); initializeCheckout(); }}>Try Again</button>
              </div>
            </div>
          ) : paymentState === 'PROCESSING' ? (
            <div className="card text-center py-12 border-primary">
              <div className="spinner border-primary border-t-transparent w-12 h-12 rounded-full border-4 animate-spin mx-auto mb-6"></div>
              <h3 className="text-xl font-bold mb-2">PROCESSING PAYMENT</h3>
              <p className="text-secondary">Verifying payment...<br/>Please do not close this page.</p>
              
              <div className="mt-8 p-4 bg-surface rounded-lg text-left inline-block">
                <p className="text-sm"><span className="text-secondary">Session:</span> {checkoutSession.checkoutId}</p>
                <p className="text-sm font-bold mt-1"><span className="text-secondary">Amount:</span> ₹{checkoutSession.total}</p>
              </div>
            </div>
          ) : (
            <div className="card border-border">
              <h3 className="font-bold text-lg mb-4">Select Payment Method</h3>
              
              <div className="space-y-3 mb-8">
                <label className={`flex items-center p-4 border rounded-xl cursor-pointer transition-colors ${paymentMethod === 'UPI' ? 'border-primary bg-primary-light bg-opacity-10' : 'hover:bg-surface'}`}>
                  <input type="radio" name="paymentMethod" value="UPI" checked={paymentMethod === 'UPI'} onChange={() => setPaymentMethod('UPI')} className="mr-3" />
                  <QrCode size={20} className="mr-3 text-secondary"/>
                  <span className="font-bold">UPI / QR Code</span>
                </label>
                <label className={`flex items-center p-4 border rounded-xl cursor-pointer transition-colors ${paymentMethod === 'CARD' ? 'border-primary bg-primary-light bg-opacity-10' : 'hover:bg-surface'}`}>
                  <input type="radio" name="paymentMethod" value="CARD" checked={paymentMethod === 'CARD'} onChange={() => setPaymentMethod('CARD')} className="mr-3" />
                  <CreditCard size={20} className="mr-3 text-secondary"/>
                  <span className="font-bold">Debit / Credit Card</span>
                </label>
              </div>

              {paymentMethod === 'UPI' && paymentConfig?.qrImageUrl && (
                <div className="text-center p-4 bg-surface rounded-xl mb-6">
                  <p className="text-sm font-bold mb-2">SCAN TO PAY</p>
                  <img src={paymentConfig.qrImageUrl} alt="UPI QR" className="w-32 h-32 mx-auto mix-blend-multiply" />
                  <p className="text-xs text-secondary mt-2">{paymentConfig.displayName}</p>
                </div>
              )}

              <button className="btn btn-primary w-full btn-large text-lg" onClick={handlePayNow}>
                PAY NOW (₹{checkoutSession.total})
              </button>

              <div className="flex justify-center items-center gap-2 mt-4 text-xs text-secondary">
                <ShieldCheck size={14}/> <span>256-bit Encrypted Connection</span>
              </div>
            </div>
          )}
        </div>
        
      </div>
    </div>
  );
}
