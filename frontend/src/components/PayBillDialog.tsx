import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { CheckCircle2, Receipt, Zap, Wifi, Phone, Home } from 'lucide-react';

interface PayBillDialogProps {
  isOpen: boolean;
  onClose: () => void;
  currentBalance: number;
  onPay: (amount: number, billType: string) => boolean;
}

const billTypes = [
  { id: 'electricity', label: 'Electricity', icon: Zap, color: 'text-yellow-500' },
  { id: 'internet', label: 'Internet', icon: Wifi, color: 'text-blue-500' },
  { id: 'phone', label: 'Phone', icon: Phone, color: 'text-green-500' },
  { id: 'rent', label: 'Rent/Mortgage', icon: Home, color: 'text-amber-500' },
];

const PayBillDialog = ({ isOpen, onClose, currentBalance, onPay }: PayBillDialogProps) => {
  const [step, setStep] = useState<'select' | 'form' | 'success'>('select');
  const [selectedBill, setSelectedBill] = useState<typeof billTypes[0] | null>(null);
  const [amount, setAmount] = useState('');
  const [accountRef, setAccountRef] = useState('');

  const handleSelectBill = (bill: typeof billTypes[0]) => {
    setSelectedBill(bill);
    setStep('form');
  };

  const handleSubmit = () => {
    if (!amount || !selectedBill) return;
    const success = onPay(parseFloat(amount), selectedBill.label);
    if (success) {
      setStep('success');
    }
  };

  const handleClose = () => {
    setStep('select');
    setSelectedBill(null);
    setAmount('');
    setAccountRef('');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        {step === 'select' && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Receipt className="w-5 h-5 text-primary" />
                Pay a Bill
              </DialogTitle>
              <DialogDescription>
                Select the type of bill you want to pay
              </DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-3 py-4">
              {billTypes.map((bill) => (
                <button
                  key={bill.id}
                  onClick={() => handleSelectBill(bill)}
                  className="flex flex-col items-center gap-3 p-6 rounded-xl border border-border hover:border-primary hover:bg-primary/5 transition-colors"
                >
                  <bill.icon className={`w-8 h-8 ${bill.color}`} />
                  <span className="font-medium">{bill.label}</span>
                </button>
              ))}
            </div>
          </>
        )}

        {step === 'form' && selectedBill && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <selectedBill.icon className={`w-5 h-5 ${selectedBill.color}`} />
                Pay {selectedBill.label} Bill
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Account/Reference Number</Label>
                <Input
                  placeholder="Enter your account number"
                  value={accountRef}
                  onChange={(e) => setAccountRef(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Amount (£)</Label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
              </div>
              <p className="text-sm text-muted-foreground">
                Available balance: £{currentBalance.toFixed(2)}
              </p>
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep('select')} className="flex-1">
                  Back
                </Button>
                <Button 
                  onClick={handleSubmit} 
                  className="flex-1"
                  disabled={!amount || parseFloat(amount) > currentBalance || parseFloat(amount) <= 0}
                >
                  Pay £{parseFloat(amount || '0').toFixed(2)}
                </Button>
              </div>
            </div>
          </>
        )}

        {step === 'success' && selectedBill && (
          <div className="py-8 text-center space-y-4">
            <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h3 className="text-xl font-semibold">Payment Successful!</h3>
              <p className="text-muted-foreground mt-1">
                £{parseFloat(amount).toFixed(2)} paid to {selectedBill.label}
              </p>
            </div>
            <Button onClick={handleClose} className="w-full">
              Done
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default PayBillDialog;
