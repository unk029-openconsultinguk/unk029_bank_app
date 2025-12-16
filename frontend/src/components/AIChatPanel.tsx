import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Bot, Send, Mic, MicOff, Volume2, VolumeX, Loader } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface AIChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  accountNo?: number;
}

const AIChatPanel = ({ isOpen, onClose, accountNo }: AIChatPanelProps) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: '👋 Hello! I\'m your UNK029 Banking Assistant. I can help you check your balance, make transfers, and manage your account. How can I help you today?',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [textToSpeechEnabled, setTextToSpeechEnabled] = useState(true);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);
  const userId = accountNo?.toString() || 'guest';

    useEffect(() => {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-GB';

        recognition.onstart = () => setIsListening(true);
        recognition.onresult = (event: any) => {
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              setInput(prev => (prev + ' ' + transcript).trim());
            }
          }
        };
        recognition.onerror = () => setIsListening(false);
        recognition.onend = () => setIsListening(false);
        recognitionRef.current = recognition;
      }
    }, []);

    const toggleVoiceInput = () => {
      if (!recognitionRef.current) {
        alert('Speech recognition not supported');
        return;
      }
      if (isListening) {
        recognitionRef.current.stop();
        setIsListening(false);
      } else {
        recognitionRef.current.start();
      }
    };

    const speakText = (text: string) => {
      if (!textToSpeechEnabled || !('speechSynthesis' in window)) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'en-GB';
      utterance.rate = 0.95;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    };

    async function createAdkSession(uid: string): Promise<string> {
      try {
        console.log('[ADK] Creating session for user:', uid);
        const res = await fetch(`/apps/bank_agent/users/${encodeURIComponent(uid)}/sessions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({}),
        });
        if (!res.ok) {
          const err = await res.text();
          throw new Error(`Session creation failed (${res.status}): ${err}`);
        }
        const data = await res.json();
        if (!data?.id) throw new Error('No session id from ADK');
        console.log('[ADK] Session created:', data.id);
        return data.id as string;
      } catch (e) {
        console.error('[ADK] Session creation error:', e);
        throw e;
      }
    }

    async function sendToAdk(uid: string, sid: string, text: string): Promise<string> {
      console.log('[ADK] Reading session baseline:', sid);
      const beforeRes = await fetch(`/apps/bank_agent/users/${encodeURIComponent(uid)}/sessions/${sid}`, {
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(10000),
      });
      if (!beforeRes.ok) {
        const err = await beforeRes.text();
        throw new Error(`Failed to read session (${beforeRes.status}): ${err}`);
      }
      const before = await beforeRes.json();
      const baseline = Array.isArray(before.events) ? before.events.length : 0;
      console.log('[ADK] Baseline events:', baseline);

      console.log('[ADK] Patching session with message:', text);
      const patchRes = await fetch(`/apps/bank_agent/users/${encodeURIComponent(uid)}/sessions/${sid}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stateDelta: { userMessage: { role: 'user', parts: [{ text }] } } }),
        signal: AbortSignal.timeout(10000),
      });
      if (!patchRes.ok) {
        const err = await patchRes.text();
        throw new Error(`ADK PATCH failed (${patchRes.status}): ${err}`);
      }
      console.log('[ADK] Session patched successfully');

      // NEW: Call /run to actually execute the agent
      console.log('[ADK] Calling /run to execute agent');
      const runRes = await fetch('/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({
          appName: 'bank_agent',
          userId: uid,
          sessionId: sid,
          newMessage: { role: 'user', parts: [{ text }] },
        }),
        signal: AbortSignal.timeout(60000), // 60s timeout for agent execution
      });

      if (!runRes.ok) {
        const err = await runRes.text();
        console.warn(`[ADK] /run returned ${runRes.status}:`, err);
        // Even if /run fails, try to get response from session polling
      } else {
        try {
          const events = await runRes.json();
          console.log('[ADK] /run returned events:', events);
          // Parse events for assistant response
          if (Array.isArray(events)) {
            for (const ev of events) {
              const author = (ev?.author || ev?.event?.message?.role || '').toLowerCase?.() || '';
              const content = ev?.content || ev?.event?.message || {};
              const parts = content?.parts || [];
              
              if (['assistant', 'bank_agent', 'agent', 'bank_assistant', 'model'].includes(author)) {
                // Check for text response
                for (const part of parts) {
                  if (part?.text) {
                    console.log('[ADK] Got text response:', part.text);
                    return part.text;
                  }
                }
              }
              
              // Check for functionResponse
              for (const part of parts) {
                const fr = part?.functionResponse;
                const text = fr?.response?.content?.[0]?.text;
                if (typeof text === 'string' && text.trim()) {
                  try {
                    const obj = JSON.parse(text);
                    if (obj?.success && obj?.message) {
                      console.log('[ADK] Got JSON response:', obj.message);
                      return String(obj.message);
                    }
                  } catch {}
                  console.log('[ADK] Got functionResponse text:', text);
                  return text.trim();
                }
              }
            }
          }
        } catch (e) {
          console.debug('[ADK] Failed to parse /run response:', e);
        }
      }

      // Fallback: Poll session for response
      console.log('[ADK] Polling session for response');
      const maxAttempts = 120; // 60s max at 500ms interval
      let delayMs = 500;
      const maxDelayMs = 5000;

      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        await new Promise(r => setTimeout(r, delayMs));
        try {
          const pollRes = await fetch(`/apps/bank_agent/users/${encodeURIComponent(uid)}/sessions/${sid}`, {
            headers: { 'Content-Type': 'application/json' },
            signal: AbortSignal.timeout(10000),
          });
          if (!pollRes.ok) {
            console.warn(`[ADK] Poll attempt ${attempt + 1} returned ${pollRes.status}`);
            if (pollRes.status === 429 || (pollRes.status >= 500 && pollRes.status < 600)) {
              delayMs = Math.min(delayMs * 2, maxDelayMs);
            }
            continue;
          }
          const sess = await pollRes.json();
          const events = Array.isArray(sess.events) ? sess.events.slice(baseline) : [];
          
          for (const ev of events) {
            const author = (ev?.author || ev?.event?.message?.role || '').toLowerCase?.() || '';
            const content = ev?.content || ev?.event?.message || {};
            const parts = content?.parts || [];
            
            if (['assistant', 'bank_agent', 'agent', 'bank_assistant', 'model'].includes(author)) {
              for (const part of parts) {
                if (part?.text) {
                  console.log('[ADK] Got polled text response:', part.text);
                  return part.text;
                }
              }
            }
            
            for (const part of parts) {
              const fr = part?.functionResponse;
              const text = fr?.response?.content?.[0]?.text;
              if (typeof text === 'string' && text.trim()) {
                try {
                  const obj = JSON.parse(text);
                  if (obj?.success && obj?.message) {
                    console.log('[ADK] Got polled JSON response:', obj.message);
                    return String(obj.message);
                  }
                } catch {}
                console.log('[ADK] Got polled functionResponse text:', text);
                return text.trim();
              }
            }
          }
        } catch (e) {
          console.warn(`[ADK] Poll error at attempt ${attempt + 1}:`, e);
        }
      }

      console.warn('[ADK] No response after polling');
      return 'No response from ADK. Please try again.';
    }

    const handleSend = async () => {
      if (!input.trim()) return;

      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: input,
      };

      setMessages(prev => [...prev, userMessage]);
      const userInput = input;
      setInput('');
      setIsLoading(true);

      try {
        let sid = sessionId;
        if (!sid) {
          console.log('[Chat] Creating new session for user:', userId);
          sid = await createAdkSession(userId);
          setSessionId(sid);
        }

        console.log('[Chat] Sending message to ADK via session:', sid);
        const messageWithContext = accountNo ? `[Account: ${accountNo}] ${userInput}` : userInput;
        const reply = await sendToAdk(userId, sid, messageWithContext);
        console.log('[Chat] Got reply:', reply);
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: reply,
        };
        setMessages(prev => [...prev, assistantMessage]);
        speakText(reply);
      } catch (error) {
        console.error('[Chat] Full error object:', error);
        console.error('[Chat] Error message:', error instanceof Error ? error.message : String(error));
        const errorMessage: Message = {
          id: (Date.now() + 2).toString(),
          role: 'assistant',
          content: `❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        };
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    };

    return (
      <Sheet open={isOpen} onOpenChange={onClose}>
        <SheetContent side="right" className="w-full sm:w-[500px] p-0 flex flex-col shadow-lg border-l border-gray-200">
          <SheetHeader className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-blue-100">
            <SheetTitle className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <span className="text-lg font-bold text-blue-900">Banking Assistant</span>
            </SheetTitle>
            {accountNo && (
              <p className="text-sm text-blue-700 mt-2">Account: {accountNo}</p>
            )}
          </SheetHeader>

          <ScrollArea className="flex-1 p-4 bg-gray-50">
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <div
                    className={`rounded-lg px-4 py-2 max-w-[75%] ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white rounded-br-none'
                        : 'bg-white text-gray-900 shadow-sm border border-gray-200 rounded-bl-none'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-3 items-end">
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                    <Loader className="w-4 h-4 text-white animate-spin" />
                  </div>
                  <div className="bg-white px-4 py-2 rounded-lg shadow-sm border border-gray-200">
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

          <div className="p-4 border-t border-gray-200 bg-white space-y-3">
            {isListening && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 text-center">
                <p className="text-xs text-blue-700 font-medium">🎤 Listening...</p>
              </div>
            )}
            {isSpeaking && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-2 text-center">
                <p className="text-xs text-green-700 font-medium">🔊 Speaking...</p>
              </div>
            )}

            <div className="flex gap-2">
              <Input
                placeholder={isListening ? "Listening..." : "Type your request..."}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                disabled={isLoading || isListening}
                className="flex-1 text-sm"
              />
              <Button
                onClick={toggleVoiceInput}
                size="icon"
                variant={isListening ? "destructive" : "outline"}
                className="flex-shrink-0"
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </Button>
              <Button
                onClick={() => setTextToSpeechEnabled(!textToSpeechEnabled)}
                size="icon"
                variant={textToSpeechEnabled ? "default" : "outline"}
                className="flex-shrink-0 bg-green-600 hover:bg-green-700"
              >
                {textToSpeechEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
              </Button>
              <Button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                size="icon"
                className="flex-shrink-0"
              >
                {isLoading ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    );
  };

  export default AIChatPanel;
