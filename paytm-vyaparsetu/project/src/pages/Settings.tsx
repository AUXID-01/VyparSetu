import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Store, User, Phone, MapPin, CheckCircle2, LogOut } from 'lucide-react';

export const Settings: React.FC = () => {
  const { auth, logout } = useAuth();
  const navigate = useNavigate();
  const [isSaved, setIsSaved] = useState(false);
  const [formData, setFormData] = useState({
    owner_name: auth.ownerName || '',
    shop_name: auth.shopName || '',
    phone: auth.phone || '',
    address: 'Sector 4, Main Market, City',
  });

  useEffect(() => {
    setFormData(prev => ({
      ...prev,
      owner_name: auth.ownerName || prev.owner_name,
      shop_name: auth.shopName || prev.shop_name,
      phone: auth.phone || prev.phone,
    }));
  }, [auth.ownerName, auth.shopName, auth.phone]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-ink-800">Merchant Profile</h1>
        <p className="text-ink-500 mt-1">Manage your personal information and shop details.</p>
      </div>

      <Card>
        <form onSubmit={handleSave} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-ink-700 flex items-center gap-2">
                <User className="w-4 h-4 text-ink-400" /> Owner Name
              </label>
              <input 
                type="text" 
                name="owner_name"
                value={formData.owner_name}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-cream-50 border border-cream-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sage-500/20 focus:border-sage-300 transition-all text-ink-800"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-ink-700 flex items-center gap-2">
                <Store className="w-4 h-4 text-ink-400" /> Shop Name
              </label>
              <input 
                type="text" 
                name="shop_name"
                value={formData.shop_name}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-cream-50 border border-cream-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sage-500/20 focus:border-sage-300 transition-all text-ink-800"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-ink-700 flex items-center gap-2">
                <Phone className="w-4 h-4 text-ink-400" /> Phone Number
              </label>
              <input 
                type="text" 
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-cream-50 border border-cream-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sage-500/20 focus:border-sage-300 transition-all text-ink-800"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-ink-700 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-ink-400" /> Address
              </label>
              <input 
                type="text" 
                name="address"
                value={formData.address}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-cream-50 border border-cream-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sage-500/20 focus:border-sage-300 transition-all text-ink-800"
              />
            </div>
          </div>

          <div className="pt-6 border-t border-cream-100 flex items-center justify-end gap-4">
            {isSaved && (
              <span className="text-positive text-sm font-medium flex items-center gap-2 animate-fade-in">
                <CheckCircle2 className="w-4 h-4" /> Profile Updated
              </span>
            )}
            <Button type="submit">Save Changes</Button>
          </div>
        </form>
      </Card>

      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-ink-800">Account Session</h2>
            <p className="text-sm text-ink-400">Sign out of your merchant session on this browser.</p>
          </div>
          <button
            type="button"
            onClick={() => {
              logout();
              navigate('/');
            }}
            className="flex items-center gap-2 px-4 py-2 bg-danger/10 text-danger hover:bg-danger/20 font-medium rounded-xl text-sm transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </Card>
    </div>
  );
};
