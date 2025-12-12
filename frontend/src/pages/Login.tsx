import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from '@/hooks/use-toast';
const Login = () => {
  const [accountNumber, setAccountNumber] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!accountNumber.trim() || !password.trim()) {
      toast({
        title: "Missing information",
        description: "Please enter both account number and password.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      await login(accountNumber, password);
      toast({
        title: "Welcome back!",
        description: "You've successfully logged in.",
      });
      navigate('/dashboard');
    } catch (error) {
      toast({
        title: "Login failed",
        description: "Please check your credentials and try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-background to-secondary/10 p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="space-y-4 text-center">
          <div className="mx-auto flex items-center justify-center gap-0">
            <div className="w-12 h-12 bg-sky-400 rounded-full flex items-center justify-center text-white font-bold text-lg">U</div>
            <div className="w-12 h-12 bg-sky-600 rounded-full flex items-center justify-center text-white font-bold text-lg" style={{marginLeft: '-12px'}}>N</div>
            <div className="w-12 h-12 bg-blue-900 rounded-full flex items-center justify-center text-white font-bold text-lg" style={{marginLeft: '-12px'}}>K</div>
          </div>
          <CardTitle className="text-3xl font-bold">Welcome Back</CardTitle>
          <CardDescription className="text-base">
            Sign in to access your bank account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="accountNumber" className="text-sm font-medium">
                Account Number / Username
              </label>
              <Input
                id="accountNumber"
                type="text"
                placeholder="Enter your account number"
                value={accountNumber}
                onChange={(e) => setAccountNumber(e.target.value)}
                required
                className="h-12"
                maxLength={50}
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Password
              </label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="h-12"
              />
            </div>
            <Button
              type="submit"
              className="w-full h-12 text-base font-semibold"
              disabled={isLoading}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
          <div className="mt-6 text-center space-y-1">
            <p className="text-sm font-medium text-foreground">Account details:</p>
            <p className="text-sm text-muted-foreground">1.Account Number: <span className="font-mono text-foreground">11111111</span> Password: <span className="font-mono text-foreground">Nithya</span></p>
            <p className="text-sm text-muted-foreground">2.Account Number: <span className="font-mono text-foreground">22222222</span> Password: <span className="font-mono text-foreground">User</span></p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
