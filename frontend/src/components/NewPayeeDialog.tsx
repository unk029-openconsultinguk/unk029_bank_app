import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { CheckCircle2, UserPlus } from 'lucide-react';

interface NewPayeeDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (payee: { name: string; sortCode: string; accountNumber: string }) => void;
}

const NewPayeeDialog = ({ isOpen, onClose, onAdd }: NewPayeeDialogProps) => {
  const [step, setStep] = useState<'form' | 'success'>('form');
  const [name, setName] = useState('');
  const [sortCode, setSortCode] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [nickname, setNickname] = useState('');

  const handleSubmit = () => {
    if (!name || !sortCode || !accountNumber) return;
    onAdd({ name, sortCode, accountNumber });
    setStep('success');
  };

  const handleClose = () => {
    setStep('form');
    setName('');
    setSortCode('');
    setAccountNumber('');
    setNickname('');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        {step === 'form' && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-primary" />
                Add New Payee
              </DialogTitle>
              <DialogDescription>
                Save a new recipient for future payments
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Payee Name</Label>
                <Input
                  placeholder="John Smith"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Nickname (optional)</Label>
                <Input
                  placeholder="e.g., Landlord, Mum"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Sort Code</Label>
                  <Input
                    placeholder="12-34-56"
                    value={sortCode}
                    onChange={(e) => setSortCode(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Account Number</Label>
                  <Input
                    placeholder="12345678"
                    value={accountNumber}
                    onChange={(e) => setAccountNumber(e.target.value)}
                  />
                </div>
              </div>
              <Button 
                onClick={handleSubmit} 
                className="w-full"
                disabled={!name || !sortCode || !accountNumber}
              >
                Add Payee
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
              <h3 className="text-xl font-semibold">Payee Added!</h3>
              <p className="text-muted-foreground mt-1">
                {name} has been saved to your payees
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

export default NewPayeeDialog;
