import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Search, LogOut } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { useAuth } from '../../contexts/AuthContext';

export const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { language, setLanguage, t } = useLanguage();
  const { auth, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="flex min-h-screen bg-cream-100">
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <header className="h-16 flex items-center justify-between px-8 bg-white/50 backdrop-blur-md border-b border-cream-200 sticky top-0 z-10">
          <div className="text-xl font-medium text-ink-800">
            {t('header.greeting')}, {auth.ownerName || 'Merchant'}
            <span className="block text-xs font-normal text-ink-400">{auth.shopName || t('header.subtitle')}</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-300" />
              <input 
                type="text" 
                placeholder={t('header.search')} 
                className="pl-9 pr-4 py-2 bg-cream-50 border border-cream-200 rounded-xl text-sm w-64 focus:outline-none focus:ring-2 focus:ring-sage-500/20 focus:border-sage-300 transition-all placeholder:text-ink-300"
              />
            </div>
            
            <select 
              value={language}
              onChange={(e) => setLanguage(e.target.value as any)}
              className="bg-cream-50 border border-cream-200 text-ink-700 text-sm rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sage-500/20 focus:border-sage-300 cursor-pointer"
            >
              <option value="en">English</option>
              <option value="hi">हिंदी (Hindi)</option>
              <option value="mr">मराठी (Marathi)</option>
              <option value="gu">ગુજરાતી (Gujarati)</option>
              <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
              <option value="bn">বাংলা (Bengali)</option>
              <option value="or">ଓଡ଼ିଆ (Odia)</option>
              <option value="ta">தமிழ் (Tamil)</option>
              <option value="te">తెలుగు (Telugu)</option>
              <option value="kn">ಕನ್ನಡ (Kannada)</option>
            </select>

            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-danger bg-danger/10 hover:bg-danger/20 rounded-xl transition-colors cursor-pointer"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-8 scrollbar-hide">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
