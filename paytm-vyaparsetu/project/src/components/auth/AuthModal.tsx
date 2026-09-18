import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { apiClient } from '../../services/apiClient';
import { Button } from '../ui/Button';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [shopName, setShopName] = useState('');
  const [ownerName, setOwnerName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        const res = await apiClient.post('/merchants/login', { phone, password });
        login({
          merchantId: res.data.merchant_id,
          sessionToken: res.data.session_token,
          shopName: res.data.shop_name,
          ownerName: res.data.owner_name,
          phone: res.data.phone || phone,
        });
        navigate('/dashboard');
      } else {
        const res = await apiClient.post('/merchants', { shop_name: shopName, owner_name: ownerName, phone, password });
        login({
          merchantId: res.data.merchant_id,
          sessionToken: res.data.session_token,
          shopName: res.data.shop_name || shopName,
          ownerName: res.data.owner_name || ownerName,
          phone: res.data.phone || phone,
        });
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/50 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden"
          >
            <div className="p-6 border-b border-cream-200 flex justify-between items-center bg-cream-50">
              <h2 className="text-xl font-bold text-ink-800">
                {isLogin ? 'Welcome Back' : 'Create Merchant Account'}
              </h2>
              <button onClick={onClose} className="text-ink-400 hover:text-ink-600">&times;</button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {error && <div className="p-3 text-sm text-danger bg-danger/10 rounded-lg">{error}</div>}
              
              {!isLogin && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-ink-600 mb-1">Shop Name</label>
                    <input type="text" required value={shopName} onChange={e => setShopName(e.target.value)} className="w-full px-3 py-2 border border-cream-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500" placeholder="Gupta Provision Store" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-ink-600 mb-1">Owner Name</label>
                    <input type="text" required value={ownerName} onChange={e => setOwnerName(e.target.value)} className="w-full px-3 py-2 border border-cream-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500" placeholder="Ramesh Gupta" />
                  </div>
                </>
              )}
              
              <div>
                <label className="block text-sm font-medium text-ink-600 mb-1">Phone Number</label>
                <input type="tel" required value={phone} onChange={e => setPhone(e.target.value)} className="w-full px-3 py-2 border border-cream-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500" placeholder="+919876543210" />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-ink-600 mb-1">Password</label>
                <input type="password" required value={password} onChange={e => setPassword(e.target.value)} className="w-full px-3 py-2 border border-cream-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500" placeholder="••••••••" />
              </div>

              <Button type="submit" variant="primary" className="w-full mt-4" disabled={loading}>
                {loading ? 'Please wait...' : (isLogin ? 'Login' : 'Create Account')}
              </Button>
            </form>
            
            <div className="p-4 text-center border-t border-cream-200 bg-cream-50 text-sm text-ink-500">
              {isLogin ? "Don't have an account? " : "Already have an account? "}
              <button type="button" onClick={() => setIsLogin(!isLogin)} className="text-sage-600 font-semibold hover:underline">
                {isLogin ? 'Sign up' : 'Login'}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
