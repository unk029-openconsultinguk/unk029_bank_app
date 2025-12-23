import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  accountNumber: string;
  sortCode: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  login: (accountNumber: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored user on mount
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (loginId: string, password: string) => {
    try {
      // Determine if loginId is an email or account number
      const isEmail = loginId.includes('@');
      const payload = isEmail
        ? { email: loginId, password }
        : { account_no: parseInt(loginId), password };
      const response = await fetch('/api/account/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let errorMsg = 'Invalid account number or password';
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            if (errorData.detail === 'Invalid password') {
              errorMsg = 'Incorrect password. Please try again.';
            } else if (errorData.detail.includes('not found')) {
              errorMsg = 'Account number not found.';
            } else {
              errorMsg = errorData.detail;
            }
          }
        } catch {}
        throw new Error(errorMsg);
      }

      const accountData = await response.json();

      const user: User = {
        id: accountData.account_no.toString(),
        accountNumber: accountData.account_no.toString(),
        sortCode: accountData.sortcode || '00-00-00',
        name: accountData.account_name || accountData.name || 'User',
      };

      // Store authentication info
      setUser(user);
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('account_number', accountData.account_no.toString());
      localStorage.setItem('password', password);
      localStorage.setItem('auth_token', `token_${accountData.account_no}`);
    } catch (error: any) {
      console.error('Login failed:', error);
      throw new Error(error.message || 'Authentication failed. Please check your credentials.');
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
