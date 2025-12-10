import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Bot, Send, User, X } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface AIChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  balance: number;
  transactions: any[];
}

const AIChatPanel = ({ isOpen, onClose, balance, transactions }: AIChatPanelProps) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hi! I\'m your AI banking assistant. I can help you with your account balance, recent transactions, and financial advice. How can I help you today?',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const generateMockResponse = (userMessage: string): string => {
    const lowerMessage = userMessage.toLowerCase();
    
    if (lowerMessage.includes('balance')) {
      return `Your current balance is £${balance.toFixed(2)}. You're doing great! 💰`;
    }
    
    if (lowerMessage.includes('transaction') || lowerMessage.includes('recent')) {
      const recentCount = Math.min(3, transactions.length);
      return `You have ${transactions.length} transactions in total. Your ${recentCount} most recent transactions show a ${transactions[0]?.type === 'deposit' ? 'deposit' : 'withdrawal'} of £${transactions[0]?.amount.toFixed(2)}.`;
    }
    
    if (lowerMessage.includes('save') || lowerMessage.includes('saving')) {
      return `Based on your transaction history, I recommend setting aside 20% of your deposits. That would be about £${(balance * 0.2).toFixed(2)} from your current balance. Would you like help creating a savings goal?`;
    }
    
    if (lowerMessage.includes('spend')) {
      const totalSpent = transactions
        .filter(t => t.type === 'withdraw')
        .reduce((sum, t) => sum + t.amount, 0);
      return `You've spent £${totalSpent.toFixed(2)} in tracked withdrawals. Your spending looks healthy relative to your balance!`;
    }

    if (lowerMessage.includes('convert') || lowerMessage.includes('exchange')) {
      return `I can help with currency conversion. Current rates: 1 GBP = 1.27 USD, 1 GBP = 1.17 EUR, 1 GBP = 188.50 JPY. What would you like to convert?`;
    }
    
    return `I understand you're asking about "${userMessage}". I can help you with banking operations. What would you like to do?`;
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Call the AI agent endpoint with MCP tool support enabled
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          account_number: localStorage.getItem('account_number'),
          balance: balance,
          transactions: transactions,
          use_tools: true,  // Enable MCP tool calling
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Handle tool results if present
        let assistantContent = data.reply || data.message || generateMockResponse(input);
        
        // If there are tool results, append them to the response
        if (data.tool_results) {
          assistantContent += '\n\nOperation completed: ' + JSON.stringify(data.tool_results);
        }
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: assistantContent,
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // Fallback to mock response if API fails
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: generateMockResponse(input),
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Error calling AI agent:', error);
      // Fallback to mock response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateMockResponse(input),
      };
      setMessages(prev => [...prev, assistantMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent side="right" className="w-full sm:w-[500px] p-0 flex flex-col shadow-lg border-l border-gray-200">
        <SheetHeader className="p-4 border-b border-gray-200 shadow-sm">
          <SheetTitle className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center">
              <Bot className="w-4 h-4 text-blue-600" />
            </div>
            AI Assistant
          </SheetTitle>
        </SheetHeader>
        
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-blue-600" />
                  </div>
                )}
                <div
                  className={`rounded-2xl px-4 py-3 max-w-[80%] ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-gray-100 text-gray-900 shadow-sm'
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
                </div>
                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-blue-600 animate-pulse" />
                </div>
                <div className="rounded-2xl px-4 py-3 bg-gray-100 shadow-sm">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="p-4 border-t border-gray-200 shadow-sm">
          <div className="flex gap-2">
            <Input
              placeholder="Ask me anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              disabled={isLoading}
              className="flex-1"
            />
            <Button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              size="icon"
              className="flex-shrink-0"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default AIChatPanel;
