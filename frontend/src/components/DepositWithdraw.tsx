import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowDownRight, ArrowUpRight } from 'lucide-react';
import { toast } from '@/hooks/use-toast';

interface DepositWithdrawProps {
  onDeposit: (amount: number, description: string) => void;
  onWithdraw: (amount: number, description: string) => boolean;
  currentBalance: number;
}

const DepositWithdraw = ({ onDeposit, onWithdraw, currentBalance }: DepositWithdrawProps) => {
  const [depositAmount, setDepositAmount] = useState('');
  const [depositDesc, setDepositDesc] = useState('');
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [withdrawDesc, setWithdrawDesc] = useState('');

  const handleDeposit = () => {
    const amount = parseFloat(depositAmount);
    if (isNaN(amount) || amount <= 0) {
      toast({
        title: "Invalid amount",
        description: "Please enter a valid amount greater than 0",
        variant: "destructive",
      });
      return;
    }

    onDeposit(amount, depositDesc || 'Deposit');
    setDepositAmount('');
    setDepositDesc('');
    toast({
      title: "Deposit successful!",
      description: `£${amount.toFixed(2)} has been added to your account.`,
    });
  };

  const handleWithdraw = () => {
    const amount = parseFloat(withdrawAmount);
    if (isNaN(amount) || amount <= 0) {
      toast({
        title: "Invalid amount",
        description: "Please enter a valid amount greater than 0",
        variant: "destructive",
      });
      return;
    }

    const success = onWithdraw(amount, withdrawDesc || 'Withdrawal');
    if (success) {
      setWithdrawAmount('');
      setWithdrawDesc('');
      toast({
        title: "Withdrawal successful!",
        description: `£${amount.toFixed(2)} has been withdrawn from your account.`,
      });
    } else {
      toast({
        title: "Insufficient funds",
        description: "You don't have enough balance for this withdrawal.",
        variant: "destructive",
      });
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Deposit & Withdraw</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="deposit" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="deposit" className="gap-2">
              <ArrowDownRight className="w-4 h-4" />
              Deposit
            </TabsTrigger>
            <TabsTrigger value="withdraw" className="gap-2">
              <ArrowUpRight className="w-4 h-4" />
              Withdraw
            </TabsTrigger>
          </TabsList>

          <TabsContent value="deposit" className="space-y-4 pt-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Amount</label>
              <Input
                type="number"
                placeholder="0.00"
                value={depositAmount}
                onChange={(e) => setDepositAmount(e.target.value)}
                className="h-12 text-lg"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Description (optional)</label>
              <Input
                placeholder="e.g., Salary"
                value={depositDesc}
                onChange={(e) => setDepositDesc(e.target.value)}
              />
            </div>
            <Button onClick={handleDeposit} className="w-full h-11" size="lg">
              Deposit Funds
            </Button>
          </TabsContent>

          <TabsContent value="withdraw" className="space-y-4 pt-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Amount</label>
              <Input
                type="number"
                placeholder="0.00"
                value={withdrawAmount}
                onChange={(e) => setWithdrawAmount(e.target.value)}
                className="h-12 text-lg"
              />
              <p className="text-xs text-muted-foreground">
                Available: £{currentBalance.toFixed(2)}
              </p>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Description (optional)</label>
              <Input
                placeholder="e.g., Shopping"
                value={withdrawDesc}
                onChange={(e) => setWithdrawDesc(e.target.value)}
              />
            </div>
            <Button onClick={handleWithdraw} className="w-full h-11" size="lg" variant="secondary">
              Withdraw Funds
            </Button>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default DepositWithdraw;
