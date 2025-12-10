import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CheckCircle2, Plus, CreditCard, Building2 } from 'lucide-react';

interface AddMoneyDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (amount: number, method: string) => void;
}

const EXCHANGE_RATES: Record<string, number> = {
  GBP: 1,
  USD: 1.27,
  EUR: 1.17,
  JPY: 188.50,
};

const AddMoneyDialog = ({ isOpen, onClose, onAdd }: AddMoneyDialogProps) => {
  const [step, setStep] = useState<'form' | 'success'>('form');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('GBP');
  const [method, setMethod] = useState<'card' | 'bank'>('card');

  const amountInGBP = parseFloat(amount) / EXCHANGE_RATES[currency] || 0;

  const handleSubmit = () => {
    if (!amount || amountInGBP <= 0) return;
    onAdd(amountInGBP, method === 'card' ? 'Card Deposit' : 'Bank Transfer');
    setStep('success');
  };

  const handleClose = () => {
    setStep('form');
    setAmount('');
    setCurrency('GBP');
    setMethod('card');
    onClose();
  };

  const quickAmounts = [50, 100, 250, 500];

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        {step === 'form' && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Plus className="w-5 h-5 text-primary" />
                Add Money
              </DialogTitle>
              <DialogDescription>
                Add funds to your account
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Select Method</Label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setMethod('card')}
                    className={`flex items-center gap-3 p-4 rounded-lg border-2 transition-colors ${
                      method === 'card' 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border hover:border-muted-foreground'
                    }`}
                  >
                    <CreditCard className="w-5 h-5" />
                    <span className="font-medium">Debit Card</span>
                  </button>
                  <button
                    onClick={() => setMethod('bank')}
                    className={`flex items-center gap-3 p-4 rounded-lg border-2 transition-colors ${
                      method === 'bank' 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border hover:border-muted-foreground'
                    }`}
                  >
                    <Building2 className="w-5 h-5" />
                    <span className="font-medium">Bank Transfer</span>
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Quick Amount</Label>
                <div className="grid grid-cols-4 gap-2">
                  {quickAmounts.map((qa) => (
                    <Button
                      key={qa}
                      variant={amount === qa.toString() ? 'default' : 'outline'}
                      onClick={() => setAmount(qa.toString())}
                      className="w-full"
                    >
                      £{qa}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Custom Amount</Label>
                  <Input
                    type="number"
                    placeholder="0.00"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Currency</Label>
                  <Select value={currency} onValueChange={setCurrency}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="GBP">£ GBP</SelectItem>
                      <SelectItem value="USD">$ USD</SelectItem>
                      <SelectItem value="EUR">€ EUR</SelectItem>
                      <SelectItem value="JPY">¥ JPY</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {currency !== 'GBP' && amount && (
                <p className="text-sm text-muted-foreground">
                  ≈ £{amountInGBP.toFixed(2)} GBP (Rate: 1 GBP = {EXCHANGE_RATES[currency]} {currency})
                </p>
              )}

              <Button 
                onClick={handleSubmit} 
                className="w-full gap-2"
                disabled={!amount || amountInGBP <= 0}
              >
                Add £{amountInGBP.toFixed(2)}
              </Button>
            </div>
          </>
        )}

        {step === 'success' && (
          <div className="py-8 text-center space-y-4">
            <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h3 className="text-xl font-semibold">Money Added!</h3>
              <p className="text-muted-foreground mt-1">
                £{amountInGBP.toFixed(2)} has been added to your account
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

export default AddMoneyDialog;
