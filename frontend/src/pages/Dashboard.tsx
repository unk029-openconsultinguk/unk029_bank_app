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

interface Transaction {
  id: string;
  type: 'deposit' | 'withdraw';
  amount: number;
  date: string;
  description: string;
  status?: string;
  related_account_no?: string | number | null;
}

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [accountNumber, setAccountNumber] = useState<number | null>(null);

  // Dialog states
  const [chatOpen, setChatOpen] = useState(false);
  const [sendMoneyOpen, setSendMoneyOpen] = useState(false);
  const [addMoneyOpen, setAddMoneyOpen] = useState(false);
  const [payBillOpen, setPayBillOpen] = useState(false);
  const [newPayeeOpen, setNewPayeeOpen] = useState(false);
  const [accountsOpen, setAccountsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Fetch account data and transactions on mount
  useEffect(() => {
    const fetchAccountData = async () => {
      try {
        const accountNumber = localStorage.getItem('account_number');
        if (!accountNumber) {
          navigate('/login');
          return;
        }

        setAccountNumber(parseInt(accountNumber));

        // Fetch account balance
        const response = await fetch(`/api/account/${accountNumber}`);
        if (!response.ok) {
          throw new Error('Failed to fetch account data');
        }
        const accountData = await response.json();
        setBalance(accountData.balance || 0);

        // Fetch transactions
        const txResp = await fetch(`/api/account/${accountNumber}/transactions`);
        if (txResp.ok) {
          const txData = await txResp.json();
          // Map backend transactions to frontend Transaction type
          setTransactions(
            (txData.transactions || []).map((t: any) => ({
              id: t.id?.toString() ?? '',
              type: t.type,
              amount: t.amount,
              date: t.created_at,
              description: t.description,
              status: t.status,
              related_account_no: t.related_account_no,
            }))
          );
        }
      } catch (error) {
        console.error('Error fetching account data:', error);
        setError('Failed to load account data. Please login again.');
        logout();
      } finally {
        setLoading(false);
      }
    };

    fetchAccountData();
  }, [navigate, logout]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-secondary/5 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold mb-4">Loading your account...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Session Expired</h2>
            <p className="text-gray-600 mb-6">{error}</p>
          </div>
          <button
            onClick={() => {
              navigate('/login');
            }}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-colors"
          >
            Return to Login
          </button>
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
        accountNo={accountNumber}
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
