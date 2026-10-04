import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import CustomerLayout from './components/CustomerLayout';
import Auth from './pages/Auth';
import Dashboard from './pages/Dashboard';
import POS from './pages/POS';
import KDS from './pages/KDS';
import FoodCatalog from './pages/FoodCatalog';
import FoodFeedback from './pages/FoodFeedback';
import PaymentsAndQR from './pages/PaymentsAndQR';
import DigitalTwin from './pages/DigitalTwin';
import Ordering from './pages/Ordering';
import CheckoutPayment from './pages/CheckoutPayment';
import OrderTracking from './pages/OrderTracking';
import { authService } from './services/authService';
import './App.css';

// Placeholder components for routes we haven't built yet
const Placeholder = ({ title }) => (
  <div className="card m-6">
    <h3>{title}</h3>
    <p>This module is currently under development or pending backend integration.</p>
  </div>
);

// Protected Route Wrapper
const ProtectedRoute = ({ children, allowedRoles }) => {
  const user = authService.getCurrentUser();
  if (!user) return <Navigate to="/auth" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/auth" replace />;
  }
  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/auth" element={<Auth />} />
        
        {/* Manager Routes */}
        <Route path="/" element={<ProtectedRoute allowedRoles={['MANAGER']}><Layout /></ProtectedRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="pos" element={<POS />} />
          <Route path="orders" element={<Placeholder title="Active Orders" />} />
          <Route path="kds" element={<KDS />} />
          <Route path="inventory" element={<FoodCatalog />} />
          <Route path="feedback" element={<FoodFeedback />} />
          <Route path="payments" element={<PaymentsAndQR />} />
          <Route path="digital-twin" element={<DigitalTwin />} />
          <Route path="automation" element={<Placeholder title="Automation Center" />} />
          <Route path="incidents" element={<Placeholder title="Incident Center" />} />
          <Route path="health" element={<Placeholder title="System Health" />} />
          <Route path="settings" element={<Placeholder title="Administration Settings" />} />
        </Route>

        {/* Customer Routes (Student & Faculty) */}
        <Route path="/customer" element={<ProtectedRoute allowedRoles={['STUDENT', 'FACULTY']}><CustomerLayout /></ProtectedRoute>}>
          <Route index element={<Navigate to="ordering" replace />} />
          <Route path="ordering" element={<Ordering />} />
          <Route path="checkout" element={<CheckoutPayment />} />
          <Route path="orders/:id" element={<OrderTracking />} />
          <Route path="orders" element={<Placeholder title="My Orders History" />} />
          <Route path="favorites" element={<Placeholder title="My Favorites" />} />
        </Route>

      </Routes>
    </BrowserRouter>
  );
}

export default App;
