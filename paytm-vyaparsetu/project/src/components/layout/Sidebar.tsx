import React from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, Receipt, ListChecks, ArrowLeftRight, Activity, Zap, Settings, Bell, LogOut } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { useAuth } from '../../contexts/AuthContext';

export const Sidebar: React.FC = () => {
  const { t } = useLanguage();
  const { auth, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const mainNav = [
    { icon: LayoutDashboard, label: t('nav.overview'), to: '/dashboard' },
    { icon: Users, label: t('nav.customers'), to: '/dashboard/customers' },
    { icon: ArrowLeftRight, label: t('nav.transactions'), to: '/dashboard/transactions' },
    { icon: Receipt, label: t('nav.challans'), to: '/dashboard/challans' },
    { icon: ListChecks, label: t('nav.settlements'), to: '/dashboard/settlements' },
  ];

  const intelligenceNav = [
    { icon: Activity, label: t('nav.insights'), to: '/dashboard/insights' },
    { icon: Zap, label: t('nav.automation'), to: '/dashboard/automation' },
  ];

  const bottomNav = [
    { icon: Bell, label: t('nav.notifications'), to: '/dashboard/notifications' },
    { icon: Settings, label: t('nav.settings'), to: '/dashboard/settings' },
  ];

  const NavItem = ({ item }: { item: any }) => (
    <NavLink
      to={item.to}
      end={item.to === '/dashboard'}
      className={({ isActive }) => 
        `flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-colors ${
          isActive 
            ? 'bg-sage-50 text-sage-600' 
            : 'text-ink-500 hover:bg-cream-100 hover:text-ink-700'
        }`
      }
    >
      <item.icon className="w-5 h-5" />
      <span>{item.label}</span>
    </NavLink>
  );

  const shopName = auth.shopName || 'Vyapar Store';
  const ownerName = auth.ownerName || 'Merchant Owner';
  const initial = ownerName.charAt(0).toUpperCase();

  return (
    <aside className="w-64 border-r border-cream-200 h-screen sticky top-0 bg-white flex flex-col p-4">
      {/* Brand */}
      <Link to="/dashboard" className="flex items-center gap-2 px-3 mb-8 hover:opacity-80 transition-opacity">
        <div className="w-8 h-8 rounded-lg bg-sage-500 flex items-center justify-center">
          <span className="text-white font-bold text-lg">V</span>
        </div>
        <span className="font-semibold text-xl tracking-tight text-ink-800">VyaparSetu</span>
      </Link>

      {/* Main Nav */}
      <nav className="flex-1 space-y-8">
        <div className="space-y-1">
          {mainNav.map(item => <NavItem key={item.to} item={item} />)}
        </div>

        <div className="space-y-1">
          <div className="px-3 mb-2 text-xs font-semibold text-ink-300 uppercase tracking-wider">{t('nav.intelligence')}</div>
          {intelligenceNav.map(item => <NavItem key={item.to} item={item} />)}
        </div>
      </nav>

      {/* Bottom Nav */}
      <div className="space-y-1 pt-4 border-t border-cream-200 mt-auto">
        {bottomNav.map(item => <NavItem key={item.to} item={item} />)}
        
        {/* Merchant Profile & Logout */}
        <div className="mt-4 p-2 bg-cream-50 rounded-xl space-y-2">
          <Link to="/dashboard/settings" className="flex items-center gap-3 px-2 py-1.5 hover:bg-cream-100 rounded-lg transition-colors cursor-pointer">
            <div className="w-9 h-9 rounded-full bg-teal-100 flex items-center justify-center text-sage-700 font-semibold">
              {initial}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-ink-700 truncate">{shopName}</div>
              <div className="text-xs text-ink-400 truncate">{ownerName}</div>
            </div>
          </Link>
          
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold text-danger hover:bg-danger/10 rounded-lg transition-colors cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </aside>
  );
};
