import { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { apiClient } from '../services/apiClient';

interface AuthState {
  merchantId: string | null;
  sessionToken: string | null;
  shopName: string | null;
  ownerName: string | null;
  phone: string | null;
}

export interface LoginParams {
  merchantId: string;
  sessionToken: string;
  shopName?: string;
  ownerName?: string;
  phone?: string;
}

interface AuthContextType {
  auth: AuthState;
  login: (params: LoginParams) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [auth, setAuth] = useState<AuthState>({
    merchantId: localStorage.getItem('merchantId'),
    sessionToken: localStorage.getItem('sessionToken'),
    shopName: localStorage.getItem('shopName'),
    ownerName: localStorage.getItem('ownerName'),
    phone: localStorage.getItem('phone'),
  });

  const login = ({ merchantId, sessionToken, shopName = '', ownerName = '', phone = '' }: LoginParams) => {
    localStorage.setItem('merchantId', merchantId);
    localStorage.setItem('sessionToken', sessionToken);
    if (shopName) localStorage.setItem('shopName', shopName);
    if (ownerName) localStorage.setItem('ownerName', ownerName);
    if (phone) localStorage.setItem('phone', phone);

    setAuth({
      merchantId,
      sessionToken,
      shopName: shopName || localStorage.getItem('shopName'),
      ownerName: ownerName || localStorage.getItem('ownerName'),
      phone: phone || localStorage.getItem('phone'),
    });
  };

  const logout = () => {
    localStorage.removeItem('merchantId');
    localStorage.removeItem('sessionToken');
    localStorage.removeItem('shopName');
    localStorage.removeItem('ownerName');
    localStorage.removeItem('phone');
    setAuth({
      merchantId: null,
      sessionToken: null,
      shopName: null,
      ownerName: null,
      phone: null,
    });
  };

  useEffect(() => {
    // If logged in but ownerName/shopName missing in state, hydrate from backend
    if (auth.merchantId && (!auth.ownerName || !auth.shopName)) {
      apiClient.get(`/merchants/${auth.merchantId}`)
        .then(res => {
          if (res.data) {
            const { shop_name, owner_name, phone } = res.data;
            localStorage.setItem('shopName', shop_name || '');
            localStorage.setItem('ownerName', owner_name || '');
            localStorage.setItem('phone', phone || '');
            setAuth(prev => ({
              ...prev,
              shopName: shop_name,
              ownerName: owner_name,
              phone: phone,
            }));
          }
        })
        .catch(err => console.error("Failed to hydrate merchant profile", err));
    }
  }, [auth.merchantId]);

  return (
    <AuthContext.Provider value={{ auth, login, logout, isAuthenticated: !!auth.sessionToken }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
