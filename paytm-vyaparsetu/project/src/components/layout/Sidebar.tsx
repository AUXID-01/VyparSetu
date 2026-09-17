import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { LayoutDashboard, Users, Receipt, ListChecks, ArrowLeftRight, Activity, Zap, Settings, Bell } from 'lucide-react';
import { CURRENT_MERCHANT } from '../../data/merchants';
import { useLanguage } from '../../contexts/LanguageContext';

export const Sidebar: React.FC = () => {
  const { t } = useLanguage();

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
        
        {/* Merchant Profile */}
        <Link to="/dashboard/settings" className="mt-4 flex items-center gap-3 px-3 py-3 bg-cream-50 hover:bg-cream-100 rounded-xl transition-colors cursor-pointer">
          <div className="w-10 h-10 rounded-full bg-teal-100 flex items-center justify-center text-sage-700 font-semibold">
            {CURRENT_MERCHANT.owner_name.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-semibold text-ink-700 truncate">{CURRENT_MERCHANT.shop_name}</div>
            <div className="text-xs text-ink-400 truncate">{CURRENT_MERCHANT.owner_name}</div>
          </div>
        </Link>
      </div>
    </aside>
  );
};
