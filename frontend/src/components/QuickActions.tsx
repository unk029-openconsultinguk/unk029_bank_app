import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Send, Plus, Receipt, UserPlus } from 'lucide-react';

interface QuickActionsProps {
  onSendMoney?: () => void;
  onAddMoney?: () => void;
  onPayBill?: () => void;
  onNewPayee?: () => void;
}

const QuickActions = ({ onSendMoney, onAddMoney, onPayBill, onNewPayee }: QuickActionsProps) => {
  const actions = [
    { 
      icon: Send, 
      label: 'Send Money', 
      onClick: onSendMoney,
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
      iconColor: 'text-blue-600 dark:text-blue-400'
    },
    { 
      icon: Plus, 
      label: 'Add Money', 
      onClick: onAddMoney,
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      iconColor: 'text-green-600 dark:text-green-400'
    },
    { 
      icon: Receipt, 
      label: 'Pay Bill', 
      onClick: onPayBill,
      bgColor: 'bg-amber-100 dark:bg-amber-900/30',
      iconColor: 'text-amber-600 dark:text-amber-400'
    },
    { 
      icon: UserPlus, 
      label: 'New Payee', 
      onClick: onNewPayee,
      bgColor: 'bg-orange-100 dark:bg-orange-900/30',
      iconColor: 'text-orange-600 dark:text-orange-400'
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {actions.map((action) => (
            <button
              key={action.label}
              onClick={action.onClick}
              className="flex flex-col items-center gap-3 p-4 rounded-xl border border-border hover:bg-muted/50 transition-colors"
            >
              <div className={`w-12 h-12 rounded-full ${action.bgColor} flex items-center justify-center`}>
                <action.icon className={`w-5 h-5 ${action.iconColor}`} />
              </div>
              <span className="text-sm font-medium text-foreground">{action.label}</span>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default QuickActions;
