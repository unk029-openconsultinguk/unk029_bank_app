import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from '@/hooks/use-toast';
const Login = () => {
  const [loginId, setLoginId] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!loginId.trim() || !password.trim()) {
      toast({
        title: "Missing information",
        description: "Please enter your account number or email and password.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      await login(loginId, password);
      toast({
        title: "Welcome back!",
        description: "You've successfully logged in.",
      });
      navigate('/dashboard');
    } catch (error: any) {
      toast({
        title: "Login failed",
        description: error.message || "Please check your credentials and try again.",
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
            <div className="w-12 h-12 bg-sky-400 flex items-center justify-center text-white font-bold text-lg" style={{clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'}}>U</div>
            <div className="w-12 h-12 bg-sky-600 flex items-center justify-center text-white font-bold text-lg" style={{marginLeft: '-12px', clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'}}>N</div>
            <div className="w-12 h-12 bg-blue-900 flex items-center justify-center text-white font-bold text-lg" style={{marginLeft: '-12px', clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'}}>K</div>
          </div>
          <CardTitle className="text-3xl font-bold">Welcome Back</CardTitle>
          <CardDescription className="text-base">
            Sign in to access your bank account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="loginId" className="text-sm font-medium">
                Account Number or Email
              </label>
              <Input
                id="loginId"
                type="text"
                placeholder="Enter your account number or email"
                value={loginId}
                onChange={(e) => setLoginId(e.target.value)}
                required
                className="h-12"
                maxLength={50}
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Password
              </label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="h-12 pr-10"
                />
                <button
                  type="button"
                  tabIndex={-1}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700"
                  onClick={() => setShowPassword((v) => !v)}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
            <Button
              type="submit"
              className="w-full h-12 text-base font-semibold"
              disabled={isLoading}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <span className="text-sm text-gray-600">Don't have an account? </span>
            <button
              type="button"
              className="text-blue-700 underline text-sm font-medium hover:text-blue-900"
              onClick={() => {
                // Open create account modal on Index page
                navigate('/');
                setTimeout(() => {
                  const evt = new CustomEvent('openCreateAccount');
                  window.dispatchEvent(evt);
                }, 100);
              }}
            >
              Create Account
            </button>
          </div>
          <div className="mt-6 text-center space-y-1">
            <p className="text-sm font-medium text-foreground">Account details:</p>
            <p className="text-sm text-muted-foreground">1.Account Number: <span className="font-mono text-foreground">12345001</span> Password: <span className="font-mono text-foreground">Acc@2025</span></p>
            <p className="text-sm text-muted-foreground">2.Account Number: <span className="font-mono text-foreground">12345002</span> Password: <span className="font-mono text-foreground">User@2025</span></p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
