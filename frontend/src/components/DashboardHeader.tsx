import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { 
  Wallet, 
  LogOut, 
  Menu, 
  LayoutDashboard, 
  ArrowLeftRight, 
  Settings,
  MessageSquare,
  User
} from 'lucide-react';

interface DashboardHeaderProps {
  userName: string;
  onLogout: () => void;
  onOpenChat: () => void;
  onOpenAccounts: () => void;
  onOpenTransfer: () => void;
  onOpenSettings: () => void;
}

const DashboardHeader = ({ userName, onLogout, onOpenChat, onOpenAccounts, onOpenTransfer, onOpenSettings }: DashboardHeaderProps) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeMenu, setActiveMenu] = useState<string | null>(null);

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const navItems = [
    { icon: LayoutDashboard, label: 'Accounts' },
    { icon: ArrowLeftRight, label: 'Transfer' },
    { icon: Settings, label: 'Settings' },
  ];

  const handleNavItemClick = (label: string) => {
    setActiveMenu(label);
    if (label === 'Accounts') {
      onOpenAccounts();
    } else if (label === 'Transfer') {
      onOpenTransfer();
    } else if (label === 'Settings') {
      onOpenSettings();
    }
  };

  return (
    <header className="bg-card border-b border-border sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        {/* Left Side - Logo */}
        <div className="flex items-center gap-3">
          {/* Mobile Menu */}
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild className="lg:hidden">
              <Button variant="ghost" size="icon">
                <Menu className="w-5 h-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64">
              <div className="flex items-center gap-3 mb-8">
                <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                  <Wallet className="w-5 h-5 text-primary-foreground" />
                </div>
                <span className="text-xl font-bold">MyBank</span>
              </div>
              <nav className="space-y-2">
                {navItems.map((item) => (
                  <button
                    key={item.label}
                    className="flex items-center gap-3 w-full px-4 py-3 rounded-lg hover:bg-muted transition-colors text-left"
                  >
                    <item.icon className="w-5 h-5 text-muted-foreground" />
                    <span className="font-medium">{item.label}</span>
                  </button>
                ))}
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onOpenChat();
                  }}
                  className="flex items-center gap-3 w-full px-4 py-3 rounded-lg hover:bg-muted transition-colors text-left"
                >
                  <MessageSquare className="w-5 h-5 text-muted-foreground" />
                  <span className="font-medium">AI Assistant</span>
                </button>
              </nav>
              <div className="absolute bottom-6 left-6 right-6">
                <Button variant="outline" className="w-full gap-2" onClick={onLogout}>
                  <LogOut className="w-4 h-4" />
                  Logout
                </Button>
              </div>
            </SheetContent>
          </Sheet>

          {/* TSB-Style Logo */}
          <div className="flex items-center gap-0 ml-1">
            <div className="w-9 h-9 bg-sky-400 flex items-center justify-center text-white font-bold text-sm font-sans" style={{marginLeft: '0', clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'}}>
              U
            </div>
            <div className="w-9 h-9 bg-sky-600 flex items-center justify-center text-white font-bold text-sm font-sans" style={{marginLeft: '-10px', clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'}}>
              N
            </div>
            <div className="w-9 h-9 bg-blue-900 flex items-center justify-center text-white font-bold text-sm font-sans" style={{marginLeft: '-10px', clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'}}>
              K
            </div>
          </div>
          <span className="text-lg font-bold hidden sm:block ml-2 text-foreground"></span>
        </div>

        {/* Right Side - Nav Icons, Avatar, Name, Logout */}
        <div className="flex items-center gap-2">
          {/* Desktop Nav Icons */}
          <nav className="hidden lg:flex items-center gap-2">
            {navItems.map((item) => (
              <button 
                key={item.label} 
                onClick={() => handleNavItemClick(item.label)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontWeight: '600',
                  borderRadius: '0.5rem',
                  border: '2px solid',
                  padding: '0.375rem 0.75rem',
                  height: '2.25rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  backgroundColor: activeMenu === item.label ? '#2563eb' : 'transparent',
                  color: activeMenu === item.label ? 'white' : 'inherit',
                  borderColor: activeMenu === item.label ? '#2563eb' : 'transparent',
                }}
                onMouseEnter={(e) => {
                  if (activeMenu !== item.label) {
                    e.currentTarget.style.boxShadow = 'inset 0 0 0 2px rgba(37, 99, 235, 0.5)';
                    e.currentTarget.style.borderColor = '#2563eb';
                  }
                }}
                onMouseLeave={(e) => {
                  if (activeMenu !== item.label) {
                    e.currentTarget.style.boxShadow = 'none';
                    e.currentTarget.style.borderColor = 'transparent';
                  }
                }}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </button>
            ))}
          </nav>

          {/* AI Chat Button */}
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onOpenChat} 
            className="hidden lg:flex px-2 hover:bg-transparent"
            title="AI Assistant"
          >
            <MessageSquare className="w-10 h-10 text-primary" />
          </Button>

          {/* User Avatar and Name */}
          <div className="flex items-center gap-3 ml-2">
            <Avatar className="h-10 w-10 bg-primary flex items-center justify-center border-2 border-primary rounded-full">
              <AvatarFallback className="bg-primary text-primary-foreground flex items-center justify-center">
                <User className="w-5 h-5" />
              </AvatarFallback>
            </Avatar>
            <span className="text-sm font-semibold hidden sm:inline text-foreground">{userName}</span>
          </div>

          {/* Logout */}
          <button 
            onClick={onLogout} 
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '0.375rem 0.75rem',
              borderRadius: '0.5rem',
              transition: 'all 0.2s',
              color: 'inherit',
            }}
            className="hidden sm:flex"
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(200, 200, 200, 0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden md:inline">Logout</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default DashboardHeader;
