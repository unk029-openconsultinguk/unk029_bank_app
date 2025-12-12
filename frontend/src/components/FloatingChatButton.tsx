import { Button } from '@/components/ui/button';
import { MessageCircle } from 'lucide-react';

interface FloatingChatButtonProps {
  onClick: () => void;
}

const FloatingChatButton = ({ onClick }: FloatingChatButtonProps) => {
  return (
    <Button
      onClick={onClick}
      size="lg"
      className="fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg hover:shadow-xl transition-all hover:scale-105 z-50"
    >
      <MessageCircle className="w-6 h-6" />
    </Button>
  );
};

export default FloatingChatButton;
