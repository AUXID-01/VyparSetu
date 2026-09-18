import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { Challans } from './pages/Challans';
import { Insights } from './pages/Insights';
import { Automation } from './pages/Automation';
import { LandingPage } from './pages/LandingPage';
import { Settings } from './pages/Settings';
import { LanguageProvider } from './contexts/LanguageContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/" replace />;
  return <>{children}</>;
};

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="customers" element={<div className="p-8 text-center text-ink-500">Customers (Coming soon)</div>} />
            <Route path="transactions" element={<div className="p-8 text-center text-ink-500">Transactions (Coming soon)</div>} />
            <Route path="challans" element={<Challans />} />
            <Route path="settlements" element={<div className="p-8 text-center text-ink-500">Settlements (Coming soon)</div>} />
            <Route path="insights" element={<Insights />} />
            <Route path="automation" element={<Automation />} />
            <Route path="notifications" element={<div className="p-8 text-center text-ink-500">Notifications (Coming soon)</div>} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
