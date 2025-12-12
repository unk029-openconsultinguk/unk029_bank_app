import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpRight, ArrowDownRight, Receipt } from 'lucide-react';

interface Transaction {
  id: string;
  type: 'deposit' | 'withdraw';
  amount: number;
  date: string;
  description: string;
  status?: string;
  related_account_no?: string | number | null;
  from_account_no?: string | number | null;
  from_name?: string;
  to_account_no?: string | number | null;
  to_name?: string;
}

interface TransactionListProps {
  transactions: Transaction[];
}

const TransactionList = ({ transactions }: TransactionListProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Receipt className="w-5 h-5 text-primary" />
          Recent Transactions
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {transactions.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No transactions yet
            </p>
          ) : (
            transactions.map((transaction) => (
              <div
                key={transaction.id}
                className="flex items-center justify-between p-4 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      transaction.type === 'deposit'
                        ? 'bg-success/10'
                        : 'bg-destructive/10'
                    }`}
                  >
                    {transaction.type === 'deposit' ? (
                      <ArrowDownRight className="w-5 h-5 text-success" />
                    ) : (
                      <ArrowUpRight className="w-5 h-5 text-destructive" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium">
                      {transaction.from_account_no && transaction.to_account_no
                        ? `From: ${transaction.from_account_no}${transaction.from_name ? ' (' + transaction.from_name + ')' : ''} → To: ${transaction.to_account_no}${transaction.to_name ? ' (' + transaction.to_name + ')' : ''}`
                        : transaction.description}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {transaction.date ? new Date(transaction.date).toLocaleString() : ''}
                      {transaction.status ? ` | Status: ${transaction.status}` : ''}
                      {transaction.related_account_no ? ` | Related: ${transaction.related_account_no}` : ''}
                    </p>
                  </div>
                </div>
                <p
                  className={`font-semibold ${
                    transaction.type === 'deposit'
                      ? 'text-success'
                      : 'text-destructive'
                  }`}
                >
                  {transaction.type === 'deposit' ? `+${transaction.amount.toFixed(2)}` : `-${transaction.amount.toFixed(2)}`}
                </p>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default TransactionList;
