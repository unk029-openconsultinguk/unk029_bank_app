import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import BalanceCard from '@/components/BalanceCard';
import TransactionList from '@/components/TransactionList';
import QuickActions from '@/components/QuickActions';
import DashboardHeader from '@/components/DashboardHeader';
import FloatingChatButton from '@/components/FloatingChatButton';
import AIChatPanel from '@/components/AIChatPanel';
import SendMoneyDialog from '@/components/SendMoneyDialog';
import AddMoneyDialog from '@/components/AddMoneyDialog';
import PayBillDialog from '@/components/PayBillDialog';
import NewPayeeDialog from '@/components/NewPayeeDialog';
import AccountsDialog from '@/components/AccountsDialog';
import SettingsDialog from '@/components/SettingsDialog';
import { toast } from '@/hooks/use-toast';

interface Transaction {
  id: string;
  type: 'deposit' | 'withdraw';
  amount: number;
  date: Date;
  description: string;
}

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  // Dialog states
  const [chatOpen, setChatOpen] = useState(false);
  const [sendMoneyOpen, setSendMoneyOpen] = useState(false);
  const [addMoneyOpen, setAddMoneyOpen] = useState(false);
  const [payBillOpen, setPayBillOpen] = useState(false);
  const [newPayeeOpen, setNewPayeeOpen] = useState(false);
  const [accountsOpen, setAccountsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Fetch account data on mount
  useEffect(() => {
    const fetchAccountData = async () => {
      try {
        const accountNumber = localStorage.getItem('account_number');
        if (!accountNumber) {
          navigate('/login');
          return;
        }

        const response = await fetch(`/account/${accountNumber}`);
        if (!response.ok) {
          throw new Error('Failed to fetch account data');
        }

        const accountData = await response.json();
        setBalance(accountData.balance || 0);
      } catch (error) {
        console.error('Error fetching account data:', error);
        toast({
          title: 'Error',
          description: 'Failed to load account data',
          variant: 'destructive',
        });
      } finally {
        setLoading(false);
      }
    };

    fetchAccountData();
  }, [navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-secondary/5 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold mb-4">Loading your account...</h2>
        </div>
      </div>
    );
  }

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleDeposit = (amount: number, description: string) => {
    setBalance(prev => prev + amount);
    setTransactions(prev => [
      { 
        id: Date.now().toString(), 
        type: 'deposit', 
        amount, 
        date: new Date(), 
        description 
      },
      ...prev
    ]);
  };

  const handleWithdraw = (amount: number, description: string) => {
    if (amount > balance) {
      return false;
    }
    setBalance(prev => prev - amount);
    setTransactions(prev => [
      { 
        id: Date.now().toString(), 
        type: 'withdraw', 
        amount, 
        date: new Date(), 
        description 
      },
      ...prev
    ]);
    return true;
  };

  const handleSendMoney = (amount: number, recipient: string) => {
    if (amount > balance) {
      toast({
        title: "Insufficient Funds",
        description: "You don't have enough balance for this transfer.",
        variant: "destructive",
      });
      return false;
    }
    setBalance(prev => prev - amount);
    setTransactions(prev => [
      { 
        id: Date.now().toString(), 
        type: 'withdraw', 
        amount, 
        date: new Date(), 
        description: `Transfer to ${recipient}` 
      },
      ...prev
    ]);
    return true;
  };

  const handleAddMoney = (amount: number, method: string) => {
    setBalance(prev => prev + amount);
    setTransactions(prev => [
      { 
        id: Date.now().toString(), 
        type: 'deposit', 
        amount, 
        date: new Date(), 
        description: method 
      },
      ...prev
    ]);
  };

  const handlePayBill = (amount: number, billType: string) => {
    if (amount > balance) {
      toast({
        title: "Insufficient Funds",
        description: "You don't have enough balance for this payment.",
        variant: "destructive",
      });
      return false;
    }
    setBalance(prev => prev - amount);
    setTransactions(prev => [
      { 
        id: Date.now().toString(), 
        type: 'withdraw', 
        amount, 
        date: new Date(), 
        description: `${billType} Bill Payment` 
      },
      ...prev
    ]);
    return true;
  };

  const handleAddPayee = (payee: { name: string; sortCode: string; accountNumber: string }) => {
    toast({
      title: "Payee Added",
      description: `${payee.name} has been saved to your payees.`,
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-secondary/5">
      <DashboardHeader 
        userName={user?.name || 'User'} 
        onLogout={handleLogout}
        onOpenChat={() => setChatOpen(true)}
        onOpenAccounts={() => setAccountsOpen(true)}
        onOpenTransfer={() => setSendMoneyOpen(true)}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <BalanceCard 
            balance={balance} 
            accountNumber={user?.accountNumber || '00000000'}
            sortCode={user?.sortCode || '00-00-00'}
          />
          <QuickActions 
            onSendMoney={() => setSendMoneyOpen(true)}
            onAddMoney={() => setAddMoneyOpen(true)}
            onPayBill={() => setPayBillOpen(true)}
            onNewPayee={() => setNewPayeeOpen(true)}
          />
          <TransactionList transactions={transactions} />
        </div>
      </main>

      {/* Floating Chat Button */}
      <FloatingChatButton onClick={() => setChatOpen(true)} />

      {/* AI Chat Panel */}
      <AIChatPanel 
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        balance={balance}
        transactions={transactions}
      />

      {/* Header Dialogs */}
      <AccountsDialog
        isOpen={accountsOpen}
        onOpenChange={setAccountsOpen}
        userName={user?.name || 'User'}
      />
      <SettingsDialog
        isOpen={settingsOpen}
        onOpenChange={setSettingsOpen}
      />

      {/* Action Dialogs */}
      <SendMoneyDialog
        isOpen={sendMoneyOpen}
        onClose={() => setSendMoneyOpen(false)}
        currentBalance={balance}
        onSend={handleSendMoney}
      />
      <AddMoneyDialog
        isOpen={addMoneyOpen}
        onClose={() => setAddMoneyOpen(false)}
        onAdd={handleAddMoney}
      />
      <PayBillDialog
        isOpen={payBillOpen}
        onClose={() => setPayBillOpen(false)}
        currentBalance={balance}
        onPay={handlePayBill}
      />
      <NewPayeeDialog
        isOpen={newPayeeOpen}
        onClose={() => setNewPayeeOpen(false)}
        onAdd={handleAddPayee}
      />
    </div>
  );
};

export default Dashboard;
