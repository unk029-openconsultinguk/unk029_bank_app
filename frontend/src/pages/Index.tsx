import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Wallet, Shield, Zap, Bot } from 'lucide-react';

const Index = () => {
  const { user, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && user) {
      navigate('/dashboard');
    }
  }, [user, isLoading, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/10 via-background to-secondary/10">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-primary rounded-2xl flex items-center justify-center">
              <Wallet className="w-6 h-6 text-primary-foreground" />
            </div>
            <h1 className="text-2xl font-bold">MyBank</h1>
          </div>
          <Button onClick={() => navigate('/login')} size="lg">
            Sign In
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <h2 className="text-5xl md:text-6xl font-bold leading-tight">
            Banking Made Simple
            <span className="block text-primary mt-2">With AI Power</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Experience modern banking with intelligent features that help you manage your finances effortlessly.
          </p>
          <div className="flex flex-wrap gap-4 justify-center pt-4">
            <Button onClick={() => navigate('/login')} size="lg" className="text-lg px-8">
              Get Started
            </Button>
            <Button variant="outline" size="lg" className="text-lg px-8">
              Learn More
            </Button>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mt-24 max-w-5xl mx-auto">
          <div className="bg-card p-8 rounded-2xl border shadow-sm">
            <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
              <Bot className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">AI Assistant</h3>
            <p className="text-muted-foreground">
              Get personalized financial insights and advice from your AI banking assistant.
            </p>
          </div>

          <div className="bg-card p-8 rounded-2xl border shadow-sm">
            <div className="w-12 h-12 bg-secondary/10 rounded-xl flex items-center justify-center mb-4">
              <Zap className="w-6 h-6 text-secondary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Instant Transfers</h3>
            <p className="text-muted-foreground">
              Deposit and withdraw funds instantly with real-time balance updates.
            </p>
          </div>

          <div className="bg-card p-8 rounded-2xl border shadow-sm">
            <div className="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center mb-4">
              <Shield className="w-6 h-6 text-accent" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Secure & Safe</h3>
            <p className="text-muted-foreground">
              Your data is protected with enterprise-grade security measures.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
