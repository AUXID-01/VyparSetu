import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { CURRENT_MERCHANT } from '../data/merchants';
import { Store, User, Phone, MapPin, CheckCircle2 } from 'lucide-react';

export const Settings: React.FC = () => {
  const [isSaved, setIsSaved] = useState(false);
  const [formData, setFormData] = useState({
    owner_name: CURRENT_MERCHANT.owner_name,
    shop_name: CURRENT_MERCHANT.shop_name,
    phone: '9876543210',
    address: 'Sector 4, Main Market, City',
  });

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
    </div>
  );
};
