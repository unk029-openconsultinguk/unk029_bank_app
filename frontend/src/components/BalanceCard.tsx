import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from '@/hooks/use-toast';

interface BalanceCardProps {
  balance: number;
  accountNumber: string;
  sortCode: string;
}

const BalanceCard = ({ balance, accountNumber, sortCode }: BalanceCardProps) => {
  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: `${label} copied to clipboard.`,
    });
  };

  return (
    <Card className="bg-gradient-to-br from-primary to-primary/80 text-primary-foreground border-0 shadow-xl">
      <CardHeader>
        <div className="space-y-2">
          <CardTitle className="text-lg font-medium opacity-90">Spend & Save Account</CardTitle>
          <div className="flex items-center gap-3 opacity-90">
            <button 
              onClick={() => copyToClipboard(sortCode, 'Sort code')}
              className="hover:opacity-100 transition-opacity font-mono font-semibold text-sm"
            >
              {sortCode}
            </button>
            <span className="opacity-75">|</span>
            <button 
              onClick={() => copyToClipboard(accountNumber, 'Account number')}
              className="hover:opacity-100 transition-opacity font-mono font-semibold text-sm"
            >
              {accountNumber}
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div>
          <p className="text-5xl font-bold">£{balance.toFixed(2)}</p>
        </div>
      </CardContent>
    </Card>
  );
};

export default BalanceCard;
