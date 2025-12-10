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

  const login = async (accountNumber: string, password: string) => {
    try {
      // Call FastAPI backend to authenticate
      const response = await fetch('/account/' + accountNumber, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Invalid account number or password');
      }

      const accountData = await response.json();

      const user: User = {
        id: accountNumber,
        accountNumber: accountData.account_no.toString(),
        sortCode: accountData.sortcode || '00-00-00',
        name: accountData.account_name || accountData.name || 'User',
      };

      // Store authentication info
      setUser(user);
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('account_number', accountNumber);
      localStorage.setItem('password', password);
      localStorage.setItem('auth_token', `token_${accountNumber}`);
    } catch (error) {
      console.error('Login failed:', error);
      throw new Error('Authentication failed. Please check your credentials.');
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
