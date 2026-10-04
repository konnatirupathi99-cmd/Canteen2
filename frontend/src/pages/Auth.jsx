import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { GraduationCap, BookOpen, Building2, Eye, EyeOff, CheckCircle2, ArrowLeft, Loader2, ShieldAlert } from 'lucide-react';
import { authService } from '../services/authService';
import './Auth.css';

export default function Auth() {
  const navigate = useNavigate();
  const [view, setView] = useState('INITIAL'); // INITIAL, ROLE_SELECTION, FORM, SUCCESS
  const [authType, setAuthType] = useState('LOGIN'); // LOGIN, SIGNUP
  const [role, setRole] = useState(null); // STUDENT, FACULTY, MANAGER
  const [facultyMethod, setFacultyMethod] = useState('ID'); // ID, EMAIL
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({});

  useEffect(() => {
    // If already logged in, redirect based on role
    const user = authService.getCurrentUser();
    if (user) {
      handleRoleRedirection(user.role);
    }
  }, []);

  const handleRoleRedirection = (userRole) => {
    if (userRole === 'STUDENT' || userRole === 'FACULTY') {
      navigate('/customer/ordering'); // Customer Ordering Module
    } else {
      navigate('/'); // Manager dashboard
    }
  };

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError(null);
  };

  const validatePassword = (pwd) => {
    if (!pwd) return { score: 0, text: 'Weak', color: 'var(--danger)' };
    let score = 0;
    if (pwd.length > 7) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;
    
    if (score <= 1) return { score, text: 'Weak', color: 'var(--danger)' };
    if (score === 2) return { score, text: 'Medium', color: 'var(--warning)' };
    return { score, text: 'Strong', color: 'var(--success)' };
  };

  const submitLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const creds = { ...formData, role };
      if (creds.email) creds.email = creds.email.trim();
      if (creds.password) creds.password = creds.password.trim();
      if (creds.mobile && !creds.mobile.startsWith('+91')) {
        creds.mobile = '+91' + creds.mobile.replace(/\s+/g, '');
      }
      
      console.log(`[Auth] Attempting login for role: ${role}`);
      const res = await authService.login(creds);
      
      if (res.success) {
        console.log(`[Auth] Login successful. Redirecting to home...`);
        handleRoleRedirection(res.user.role);
      }
    } catch (err) {
      console.error(`[Auth] Login failed:`, err.message);
      const msg = err.message || 'Unable to authenticate with the provided credentials.';
      if (msg.includes('Failed to fetch') || msg.includes('Network Error')) {
        setError('Unable to connect to CanteenOS. Please try again.');
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const submitSignup = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const dataToSubmit = { ...formData, role };
      if (dataToSubmit.email) dataToSubmit.email = dataToSubmit.email.trim();
      if (dataToSubmit.password) dataToSubmit.password = dataToSubmit.password.trim();
      if (dataToSubmit.mobile && !dataToSubmit.mobile.startsWith('+91')) {
        dataToSubmit.mobile = '+91' + dataToSubmit.mobile.replace(/\s+/g, '');
      }
      if (role === 'MANAGER') {
         dataToSubmit.personalEmail = dataToSubmit.email;
      } else {
         dataToSubmit.collegeEmail = dataToSubmit.email;
      }

      console.log(`[Auth] Attempting signup for role: ${role}`);
      const res = await authService.register(dataToSubmit);
      if (res.success) {
        // Auto-login immediately after signup
        const loginRes = await authService.login({
           role,
           email: dataToSubmit.email,
           mobile: dataToSubmit.mobile,
           password: dataToSubmit.password,
           facultyId: dataToSubmit.facultyId
        });
        if (loginRes.success) {
           console.log(`[Auth] Auto-login successful after signup. Redirecting...`);
           handleRoleRedirection(loginRes.user.role);
        }
      }
    } catch (err) {
      console.error(`[Auth] Signup failed:`, err.message);
      const msg = err.message || 'Registration failed.';
      if (msg.includes('Failed to fetch') || msg.includes('Network Error')) {
        setError('Unable to connect to CanteenOS. Please try again.');
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const goBack = () => {
    setError(null);
    if (view === 'FORM') setView('ROLE_SELECTION');
    else if (view === 'ROLE_SELECTION') setView('INITIAL');
  };

  const toggleAuthType = () => {
    setAuthType(prev => prev === 'LOGIN' ? 'SIGNUP' : 'LOGIN');
    setView('ROLE_SELECTION');
    setFormData({});
    setError(null);
  };

  // ---------------------------------------------------------------------------
  // RENDER: INITIAL (LOGIN vs SIGNUP)
  // ---------------------------------------------------------------------------
  if (view === 'INITIAL') {
    return (
      <div className="auth-layout split-screen">
        <div className="auth-brand-panel">
          <div className="brand-content">
            <h1 className="brand-logo">CANTEEN<span className="text-primary">OS</span></h1>
            <h2 className="brand-subtitle">Real-Time Canteen Operations Platform</h2>
            <div className="brand-features mt-12">
              <p>✓ Smart Canteen</p>
              <p>✓ Faster Service</p>
              <p>✓ Real-Time Ops</p>
            </div>
          </div>
        </div>
        <div className="auth-main-panel">
          <div className="auth-card">
            <div className="text-center mb-8">
              <h2 className="auth-title">Welcome to CanteenOS</h2>
              <p className="auth-subtitle">Order smarter. Manage faster. Stay connected.</p>
            </div>
            
            <div className="initial-options">
              <div className="option-card" onClick={() => { setAuthType('LOGIN'); setView('ROLE_SELECTION'); }}>
                <h3>LOGIN</h3>
                <p>Already have an account? Sign in.</p>
              </div>
              <div className="option-card" onClick={() => { setAuthType('SIGNUP'); setView('ROLE_SELECTION'); }}>
                <h3>SIGN UP</h3>
                <p>Create your CanteenOS account.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // RENDER: ROLE SELECTION
  // ---------------------------------------------------------------------------
  if (view === 'ROLE_SELECTION') {
    return (
      <div className="auth-layout split-screen">
        <div className="auth-brand-panel">
          <div className="brand-content">
            <h1 className="brand-logo">CANTEEN<span className="text-primary">OS</span></h1>
            <h2 className="brand-subtitle">Real-Time Canteen Operations Platform</h2>
          </div>
        </div>
        <div className="auth-main-panel">
          <div className="auth-card">
            <button className="btn-back" onClick={goBack}><ArrowLeft size={16}/> Back</button>
            <div className="text-center mb-8">
              <h2 className="auth-title">{authType === 'LOGIN' ? 'Login' : 'Create your CanteenOS Account'}</h2>
              <p className="auth-subtitle">Select your account type to {authType === 'LOGIN' ? 'continue' : 'get started'}.</p>
            </div>

            <div className="role-options">
              <div className={`role-card ${role === 'STUDENT' ? 'selected' : ''}`} onClick={() => setRole('STUDENT')}>
                <div className="role-icon"><GraduationCap size={24}/></div>
                <div className="role-info">
                  <h4>STUDENT</h4>
                  <p>Order food from the campus canteen.</p>
                </div>
                {role === 'STUDENT' && <CheckCircle2 className="check-icon" />}
              </div>
              
              <div className={`role-card ${role === 'FACULTY' ? 'selected' : ''}`} onClick={() => setRole('FACULTY')}>
                <div className="role-icon"><BookOpen size={24}/></div>
                <div className="role-info">
                  <h4>FACULTY</h4>
                  <p>Order food using your faculty account.</p>
                </div>
                {role === 'FACULTY' && <CheckCircle2 className="check-icon" />}
              </div>
              
              <div className={`role-card ${role === 'MANAGER' ? 'selected' : ''}`} onClick={() => setRole('MANAGER')}>
                <div className="role-icon"><Building2 size={24}/></div>
                <div className="role-info">
                  <h4>MANAGER</h4>
                  <p>Manage canteen operations.</p>
                </div>
                {role === 'MANAGER' && <CheckCircle2 className="check-icon" />}
              </div>
            </div>

            <button 
              className="btn btn-primary w-full mt-8 btn-large" 
              disabled={!role}
              onClick={() => { setFormData({}); setView('FORM'); }}
            >
              CONTINUE
            </button>

            <div className="auth-switch text-center mt-6">
              {authType === 'LOGIN' ? (
                <p>Don't have an account? <span className="auth-link" onClick={toggleAuthType}>Sign up</span></p>
              ) : (
                <p>Already have an account? <span className="auth-link" onClick={toggleAuthType}>Login</span></p>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // RENDER: LOGIN FORM
  // ---------------------------------------------------------------------------
  if (view === 'FORM' && authType === 'LOGIN') {
    return (
      <div className="auth-layout center-screen">
        <div className="auth-card form-card">
          <div className="flex justify-between items-center mb-6">
            <button className="btn-back" onClick={goBack}><ArrowLeft size={16}/> Change account type</button>
            <h1 className="brand-logo-small">CANTEEN<span className="text-primary">OS</span></h1>
          </div>
          
          <h2 className="auth-title capitalize">{role.toLowerCase()} Login</h2>
          <p className="auth-subtitle mb-6">
            {role === 'STUDENT' && 'Sign in using your registered college credentials.'}
            {role === 'FACULTY' && 'Sign in using your faculty credentials.'}
            {role === 'MANAGER' && 'Access your Canteen Operations Management Center.'}
          </p>

          {error && <div className="alert alert-error mb-6"><ShieldAlert size={16}/> {error}</div>}

          <form onSubmit={submitLogin}>
            {role === 'FACULTY' && (
              <div className="method-selector mb-6">
                <label className="radio-label">
                  <input type="radio" checked={facultyMethod === 'ID'} onChange={() => setFacultyMethod('ID')} />
                  Faculty ID
                </label>
                <label className="radio-label">
                  <input type="radio" checked={facultyMethod === 'EMAIL'} onChange={() => setFacultyMethod('EMAIL')} />
                  College Email
                </label>
              </div>
            )}

            {(role === 'STUDENT' || (role === 'FACULTY' && facultyMethod === 'EMAIL')) && (
              <div className="form-group">
                <label>College Email</label>
                <input type="email" name="email" className="input-field" placeholder="student@college.edu" onChange={handleInputChange} required />
              </div>
            )}

            {role === 'MANAGER' && (
              <div className="form-group">
                <label>Personal Email</label>
                <input type="email" name="email" className="input-field" placeholder="manager@example.com" onChange={handleInputChange} required />
              </div>
            )}

            {role === 'FACULTY' && facultyMethod === 'ID' && (
              <div className="form-group">
                <label>Faculty ID</label>
                <input type="text" name="facultyId" className="input-field" placeholder="FAC-XXXXXX" onChange={handleInputChange} required />
              </div>
            )}

            <div className="form-group">
              <label>Mobile Number</label>
              <div className="phone-input">
                <span className="country-code">+91</span>
                <input type="tel" name="mobile" className="input-field" placeholder="XXXXX XXXXX" onChange={handleInputChange} required pattern="[0-9]{10}" />
              </div>
            </div>

            <div className="form-group">
              <label className="flex justify-between">
                Password
                <span className="auth-link text-sm">Forgot password?</span>
              </label>
              <div className="password-input">
                <input type={showPassword ? 'text' : 'password'} name="password" className="input-field" placeholder="••••••••" onChange={handleInputChange} required />
                <button type="button" className="btn-icon password-toggle" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <EyeOff size={18}/> : <Eye size={18}/>}
                </button>
              </div>
            </div>

            <button type="submit" className="btn btn-primary w-full btn-large mt-6" disabled={loading}>
              {loading ? <><Loader2 size={18} className="spin"/> AUTHENTICATING...</> : `LOGIN AS ${role}`}
            </button>
          </form>

          <div className="auth-switch text-center mt-6">
            <p>Don't have an account? <span className="auth-link" onClick={toggleAuthType}>Sign up</span></p>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // RENDER: SIGNUP FORM
  // ---------------------------------------------------------------------------
  if (view === 'FORM' && authType === 'SIGNUP') {
    const pwdStrength = validatePassword(formData.password);
    
    return (
      <div className="auth-layout center-screen">
        <div className="auth-card form-card signup-card">
          <div className="flex justify-between items-center mb-6">
            <button className="btn-back" onClick={goBack}><ArrowLeft size={16}/> Change account type</button>
            <h1 className="brand-logo-small">CANTEEN<span className="text-primary">OS</span></h1>
          </div>
          
          <h2 className="auth-title capitalize">Create {role.toLowerCase()} Account</h2>
          
          {error && <div className="alert alert-error mb-6"><ShieldAlert size={16}/> {error}</div>}

          <form onSubmit={submitSignup}>
            <div className="form-grid grid-cols-2">
              <div className="form-group">
                <label>Full Name</label>
                <input type="text" name="name" className="input-field" placeholder="Enter full name" onChange={handleInputChange} required />
              </div>

              {role === 'STUDENT' && (
                <div className="form-group">
                  <label>Student ID</label>
                  <input type="text" name="studentId" className="input-field" placeholder="STU2026001" onChange={handleInputChange} required />
                </div>
              )}

              {role === 'FACULTY' && (
                <div className="form-group">
                  <label>Faculty ID</label>
                  <input type="text" name="facultyId" className="input-field" placeholder="FAC-1024" onChange={handleInputChange} required />
                </div>
              )}

              {role === 'MANAGER' && (
                <div className="form-group">
                  <label>Manager ID</label>
                  <input type="text" name="managerId" className="input-field" placeholder="MGR-001" onChange={handleInputChange} required />
                </div>
              )}

              <div className="form-group">
                <label>{role === 'MANAGER' ? 'Personal Email' : 'College Email'}</label>
                <input type="email" name="email" className="input-field" placeholder={role === 'MANAGER' ? "manager@example.com" : "user@college.edu"} onChange={handleInputChange} required />
              </div>

              <div className="form-group">
                <label>Mobile Number</label>
                <div className="phone-input">
                  <span className="country-code">+91</span>
                  <input type="tel" name="mobile" className="input-field" placeholder="XXXXX XXXXX" onChange={handleInputChange} required pattern="[0-9]{10}" />
                </div>
              </div>

              {role === 'MANAGER' && (
                <>
                  <div className="form-group">
                    <label>Canteen ID</label>
                    <input type="text" name="canteenId" className="input-field" placeholder="CANTEEN-001" onChange={handleInputChange} required />
                  </div>
                  <div className="form-group">
                    <label>Canteen Name</label>
                    <input type="text" name="canteenName" className="input-field" placeholder="Main Campus Canteen" onChange={handleInputChange} required />
                  </div>
                </>
              )}

              {(role === 'STUDENT' || role === 'FACULTY') && (
                <div className="form-group">
                  <label>Department (Optional)</label>
                  <select name="department" className="input-field" onChange={handleInputChange}>
                    <option value="">Select Department ▼</option>
                    <option value="CS">Computer Science</option>
                    <option value="IT">Information Technology</option>
                    <option value="MECH">Mechanical</option>
                  </select>
                </div>
              )}

              {role === 'STUDENT' && (
                <div className="form-group">
                  <label>Year (Optional)</label>
                  <select name="year" className="input-field" onChange={handleInputChange}>
                    <option value="">Select Year ▼</option>
                    <option value="1">1st Year</option>
                    <option value="2">2nd Year</option>
                    <option value="3">3rd Year</option>
                    <option value="4">4th Year</option>
                  </select>
                </div>
              )}
            </div>

            <div className="form-group mt-4">
              <label>Password</label>
              <div className="password-input">
                <input type={showPassword ? 'text' : 'password'} name="password" className="input-field" placeholder="Create password" onChange={handleInputChange} required />
                <button type="button" className="btn-icon password-toggle" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <EyeOff size={18}/> : <Eye size={18}/>}
                </button>
              </div>
              {formData.password && (
                <div className="password-strength mt-2">
                  <div className="strength-bars">
                    {[0,1,2,3].map(i => (
                      <div key={i} className="strength-bar" style={{ backgroundColor: i <= pwdStrength.score ? pwdStrength.color : 'var(--border)' }}></div>
                    ))}
                  </div>
                  <span className="strength-text" style={{ color: pwdStrength.color }}>Password Strength: {pwdStrength.text}</span>
                </div>
              )}
            </div>

            <div className="form-group mt-4">
              <label>Confirm Password</label>
              <div className="password-input">
                <input type={showPassword ? 'text' : 'password'} name="confirmPassword" className="input-field" placeholder="Confirm password" onChange={handleInputChange} required />
              </div>
            </div>

            <button type="submit" className="btn btn-primary w-full btn-large mt-8" disabled={loading}>
              {loading ? <><Loader2 size={18} className="spin"/> CREATING ACCOUNT...</> : `CREATE ${role} ACCOUNT`}
            </button>
          </form>

          <div className="auth-switch text-center mt-6">
            <p>Already have an account? <span className="auth-link" onClick={toggleAuthType}>Login</span></p>
          </div>
        </div>
      </div>
    );
  }



  // ---------------------------------------------------------------------------
  // RENDER: SUCCESS (Manager Pending included)
  // ---------------------------------------------------------------------------
  if (view === 'SUCCESS') {
    return (
      <div className="auth-layout center-screen">
        <div className="auth-card form-card text-center">
          <CheckCircle2 size={64} className="text-success mx-auto mb-6" />
          <h2 className="auth-title">Account Created</h2>
          {role === 'MANAGER' ? (
            <p className="auth-subtitle">Your manager account has been created and is awaiting approval. You will receive an email once an administrator approves your access.</p>
          ) : (
            <p className="auth-subtitle">Your account is successfully verified! Redirecting to login...</p>
          )}
        </div>
      </div>
    );
  }

  return null;
}
