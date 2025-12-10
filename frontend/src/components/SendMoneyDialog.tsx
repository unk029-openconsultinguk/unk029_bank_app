import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CheckCircle2, Send, ArrowRight, AlertCircle } from 'lucide-react';

interface SendMoneyDialogProps {
  isOpen: boolean;
  onClose: () => void;
  currentBalance: number;
  onSend: (amount: number, recipient: string, currency: string) => boolean;
}

const EXCHANGE_RATES: Record<string, number> = {
  GBP: 1,
  USD: 1.27,
  EUR: 1.17,
  JPY: 188.50,
};

// Helper function to convert technical errors to user-friendly messages
const getErrorMessage = (errorResponse: any): string => {
  const detail = errorResponse?.detail || '';
  
  if (detail.includes('not found') || detail.includes('does not exist')) {
    return 'The recipient account does not exist. Please check the sort code and account number.';
  }
  if (detail.includes('Insufficient funds') || detail.includes('insufficient')) {
    return 'You do not have sufficient funds for this transfer.';
  }
  if (detail.includes('Invalid') || detail.includes('invalid')) {
    return 'Invalid account details. Please check the sort code and account number format.';
  }
  if (detail.includes('same account')) {
    return 'You cannot transfer to the same account.';
  }
  
  // Fallback message
  return 'Transfer failed. Please check your details and try again.';
};

const SendMoneyDialog = ({ isOpen, onClose, currentBalance, onSend }: SendMoneyDialogProps) => {
  const [step, setStep] = useState<'form' | 'confirm' | 'success'>('form');
  const [recipient, setRecipient] = useState('');
  const [sortCode, setSortCode] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('GBP');
  const [reference, setReference] = useState('');
  const [error, setError] = useState('');
  const [validating, setValidating] = useState(false);

  const amountInGBP = parseFloat(amount) / EXCHANGE_RATES[currency] || 0;

  // Validation helper function
  const validateForm = async (): Promise<string | null> => {
    // Recipient Name validation
    if (!recipient.trim()) {
      return 'Recipient name is required.';
    }
    if (recipient.length < 2) {
      return 'Recipient name must be at least 2 characters.';
    }
    if (!/^[a-zA-Z\s'-]+$/.test(recipient)) {
      return 'Recipient name should only contain letters, spaces, hyphens, and apostrophes.';
    }

    // Sort Code validation (6 digits without formatting)
    const cleanSortCode = sortCode.replace(/\D/g, '');
    if (!cleanSortCode) {
      return 'Sort code is required.';
    }
    if (cleanSortCode.length !== 6) {
      return 'Enter valid sort code (e.g., 20-00-00). Requires exactly 6 digits.';
    }

    // Account Number validation (8-10 digits)
    if (!accountNumber.trim()) {
      return 'Account number is required.';
    }
    if (!/^\d{8,10}$/.test(accountNumber)) {
      return 'Account number must be 8 to 10 digits.';
    }

    // Amount validation
    if (!amount.trim()) {
      return 'Amount is required.';
    }
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      return 'Amount must be a valid positive number.';
    }
    if (amountInGBP > currentBalance) {
      return `Insufficient funds. You have £${currentBalance.toFixed(2)} available.`;
    }

    // Validate that the recipient account exists
    try {
      const response = await fetch(`/account/${accountNumber}`);
      if (!response.ok) {
        return `Account number ${accountNumber} does not exist. Please check and try again.`;
      }
    } catch (err) {
      return 'Unable to verify account. Please try again.';
    }

    return null;
  };

  const handleSubmit = async () => {
    const validationError = await validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError('');
    setStep('confirm');
  };

  const handleConfirm = async () => {
    try {
      const fromAccount = localStorage.getItem('account_number');
      if (!fromAccount || !accountNumber) {
        setError('Account information is missing. Please try again.');
        return;
      }

      const response = await fetch('/account/transfer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from_account_no: parseInt(fromAccount),
          to_account_no: parseInt(accountNumber),
          amount: amountInGBP,
        }),
      });

      if (response.ok) {
        setError('');
        setStep('success');
        // Call the parent callback for local state update
        onSend(amountInGBP, recipient, currency);
      } else {
        const errorResponse = await response.json();
        const userFriendlyError = getErrorMessage(errorResponse);
        setError(userFriendlyError);
        setStep('form');
      }
    } catch (error) {
      console.error('Transfer error:', error);
      setError('Unable to process transfer. Please check your connection and try again.');
      setStep('form');
    }
  };

  const handleClose = () => {
    setStep('form');
    setRecipient('');
    setSortCode('');
    setAccountNumber('');
    setAmount('');
    setCurrency('GBP');
    setReference('');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        {step === 'form' && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Send className="w-5 h-5 text-primary" />
                Send Money
              </DialogTitle>
              <DialogDescription>
                Transfer money to another account
              </DialogDescription>
            </DialogHeader>
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex gap-2">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Recipient Name</Label>
                <Input
                  placeholder="John Smith"
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value.replace(/[^a-zA-Z\s'-]/g, ''))}
                  maxLength={50}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Sort Code</Label>
                  <Input
                    placeholder="20-00-00"
                    value={sortCode}
                    onChange={(e) => {
                      // Extract only digits
                      const digits = e.target.value.replace(/\D/g, '').slice(0, 6);
                      
                      // Auto-format as XX-XX-XX
                      if (digits.length === 0) {
                        setSortCode('');
                      } else if (digits.length <= 2) {
                        setSortCode(digits);
                      } else if (digits.length <= 4) {
                        setSortCode(digits.slice(0, 2) + '-' + digits.slice(2));
                      } else {
                        setSortCode(digits.slice(0, 2) + '-' + digits.slice(2, 4) + '-' + digits.slice(4, 6));
                      }
                    }}
                    maxLength={8}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Account Number</Label>
                  <Input
                    placeholder="12345678"
                    value={accountNumber}
                    onChange={(e) => setAccountNumber(e.target.value.replace(/\D/g, '').slice(0, 10))}
                    maxLength={10}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Amount</Label>
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
              <div className="space-y-2">
                <Label>Reference (optional)</Label>
                <Input
                  placeholder="Payment for..."
                  value={reference}
                  onChange={(e) => setReference(e.target.value)}
                />
              </div>
              <p className="text-sm text-muted-foreground">
                Available balance: £{currentBalance.toFixed(2)}
              </p>
              <Button 
                onClick={handleSubmit} 
                className="w-full gap-2"
              >
                Continue <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </>
        )}

        {step === 'confirm' && (
          <>
            <DialogHeader>
              <DialogTitle>Confirm Transfer</DialogTitle>
              <DialogDescription>
                Please review your transfer details
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="bg-muted rounded-lg p-4 space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">To</span>
                  <span className="font-medium">{recipient}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Sort Code</span>
                  <span className="font-mono">{sortCode}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Account</span>
                  <span className="font-mono">{accountNumber}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Amount</span>
                  <span className="font-bold text-lg">£{amountInGBP.toFixed(2)}</span>
                </div>
                {reference && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Reference</span>
                    <span>{reference}</span>
                  </div>
                )}
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep('form')} className="flex-1">
                  Back
                </Button>
                <Button onClick={handleConfirm} className="flex-1">
                  Confirm & Send
                </Button>
              </div>
            </div>
          </>
        )}

        {step === 'success' && (
          <div className="py-8 text-center space-y-4">
            <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h3 className="text-xl font-semibold">Transfer Complete!</h3>
              <p className="text-muted-foreground mt-1">
                £{amountInGBP.toFixed(2)} sent to {recipient}
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

export default SendMoneyDialog;
