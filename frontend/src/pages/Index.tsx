import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Shield, Zap, Bot } from 'lucide-react';

const Index = () => {
  const { user, isLoading } = useAuth();
  const navigate = useNavigate();

  // All hooks and handlers at the top
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: '',
    password: '',
    email: '',
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    if (name === 'name') {
      // Only allow letters and spaces
      const filteredValue = value.replace(/[^a-zA-Z\s]/g, '');
      setForm({ ...form, [name]: filteredValue });
    } else {
      setForm({ ...form, [name]: value });
    }
  }

  const validatePassword = (password: string) => {
    // At least 8 chars, one letter, one number, one special char (@,&,!)
    return /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@&!])[A-Za-z\d@&!]{8,}$/.test(password);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validatePassword(form.password)) {
      setError('Password must be at least 8 characters and include a letter, a number, and a special character (@, &, !).');
      return;
    }
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const res = await fetch('/api/account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.name,
          password: form.password,
          email: form.email,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccess('Account created successfully! You can now sign in.');
      setForm({ name: '', password: '', email: '' });
    } catch (err: any) {
      setError(err.message || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isLoading && user) {
      navigate('/dashboard');
    }
  }, [user, isLoading, navigate]);

    return (
      <>
        <div className="min-h-screen bg-gradient-to-br from-primary/10 via-background to-secondary/10">
          {/* Header */}
          <header className="container mx-auto px-4 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {/* UNK Logo - Consistent with Login/Dashboard */}
                <div className="flex items-center gap-0">
                  <div className="w-10 h-10 bg-sky-400 flex items-center justify-center text-white font-bold text-base shadow-md" style={{clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'}}>U</div>
                  <div className="w-10 h-10 bg-sky-600 flex items-center justify-center text-white font-bold text-base shadow-md" style={{marginLeft: '-10px', clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'}}>N</div>
                  <div className="w-10 h-10 bg-blue-900 flex items-center justify-center text-white font-bold text-base shadow-md" style={{marginLeft: '-10px', clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'}}>K</div>
                </div>
                {/* Removed 'UNK Bank' text for cleaner look */}
              </div>
              <div className="flex gap-3">
                <Button onClick={() => navigate('/login')} size="lg">
                  Sign In
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => setShowCreate(true)}
                  className="border-2 border-blue-600 text-blue-700 hover:border-blue-800 hover:text-blue-900"
                >
                  Create Account
                </Button>
              </div>
              {/* Create Account Modal */}
              {showCreate && (
                <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
                  <div className="bg-white rounded-xl shadow-xl p-8 w-full max-w-md">
                    <div className="flex justify-between items-center mb-4">
                      <h2 className="text-xl font-bold">Create Account</h2>
                      <button onClick={() => setShowCreate(false)} className="text-gray-500 hover:text-black">&times;</button>
                    </div>
                    <form onSubmit={handleSubmit} className="space-y-4">
                      <input name="name" value={form.name} onChange={handleChange} required placeholder="Full Name" className="w-full border rounded px-3 py-2" />
                      <input name="email" value={form.email} onChange={handleChange} required type="email" placeholder="Email" className="w-full border rounded px-3 py-2" />
                      <input name="password" value={form.password} onChange={handleChange} required type="password" placeholder="Password" className="w-full border rounded px-3 py-2" />
                      <button type="submit" className="w-full bg-primary text-white py-2 rounded font-semibold" disabled={loading}>{loading ? 'Creating...' : 'Create Account'}</button>
                      {success && (
                        <div className="text-green-600 text-center mt-2">
                          {success} <button className="underline text-blue-700 ml-2" type="button" onClick={() => { setShowCreate(false); navigate('/login'); }}>Login</button>
                        </div>
                      )}
                      {error && <div className="text-red-600 text-center mt-2">{error}</div>}
                    </form>
                  </div>
                </div>
              )}
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

            {/* TSB-style Feature Cards */}
            <div className="grid md:grid-cols-4 gap-8 mt-24 max-w-6xl mx-auto">
              <div className="bg-white p-8 rounded-2xl border shadow-md flex flex-col items-center hover:shadow-lg transition">
                <Bot className="w-10 h-10 text-sky-500 mb-3" />
                <h3 className="text-lg font-semibold mb-2">AI Banking Assistant</h3>
                <p className="text-muted-foreground text-center">Chat with your AI assistant for help, advice, and quick actions 24/7.</p>
              </div>
              <div className="bg-white p-8 rounded-2xl border shadow-md flex flex-col items-center hover:shadow-lg transition">
                <Zap className="w-10 h-10 text-blue-500 mb-3" />
                <h3 className="text-lg font-semibold mb-2">Instant Payments</h3>
                <p className="text-muted-foreground text-center">Send and receive money instantly, with real-time notifications and balance updates.</p>
              </div>
              <div className="bg-white p-8 rounded-2xl border shadow-md flex flex-col items-center hover:shadow-lg transition">
                <Shield className="w-10 h-10 text-green-600 mb-3" />
                <h3 className="text-lg font-semibold mb-2">Security & Protection</h3>
                <p className="text-muted-foreground text-center">Your money and data are protected by advanced security and fraud monitoring.</p>
              </div>
              <div className="bg-white p-8 rounded-2xl border shadow-md flex flex-col items-center hover:shadow-lg transition">
                <span className="w-10 h-10 flex items-center justify-center mb-3">
                  <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="10" cy="20" r="10" fill="#38bdf8" />
                    <circle cx="20" cy="20" r="10" fill="#0ea5e9" />
                    <circle cx="30" cy="20" r="10" fill="#1e3a8a" />
                    <text x="7" y="25" fontSize="12" fill="white" fontWeight="bold">U</text>
                    <text x="17" y="25" fontSize="12" fill="white" fontWeight="bold">N</text>
                    <text x="27" y="25" fontSize="12" fill="white" fontWeight="bold">K</text>
                  </svg>
                </span>
                <h3 className="text-lg font-semibold mb-2">Modern Digital Banking</h3>
                <p className="text-muted-foreground text-center">Enjoy a seamless, mobile-first experience with all the features you expect from a leading bank.</p>
              </div>
            </div>
          </main>
        </div>
        <footer className="w-full text-center text-xs text-gray-400 py-2 bg-white border-t border-gray-200 fixed bottom-0 left-0 z-50">
          © {new Date().getFullYear()} UNK Bank. All rights reserved.
        </footer>
      </>
    );
};

export default Index;
