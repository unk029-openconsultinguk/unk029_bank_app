// Simple ADK client - Frontend → ADK → MCP → FastAPI → DB

export async function createSession(userId: string) {
  const res = await fetch('/apps/bank_assistant/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!res.ok) throw new Error('Session failed');
  return res.json();
}

export async function sendMessage(
  userId: string,
  sessionId: string,
  text: string
): Promise<string> {
  const res = await fetch('/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      app_name: 'bank_assistant',
      user_id: userId,
      session_id: sessionId,
      messages: [{ role: 'user', parts: [{ text }] }],
    }),
  });

  if (!res.ok) throw new Error('Run failed');

  const data = await res.json();
  const events = Array.isArray(data) ? data : [data];

  for (let i = events.length - 1; i >= 0; i--) {
    const e = events[i];
    if (e.author !== 'user' && e.content?.parts) {
      return e.content.parts.map((p: any) => p.text).join('');
    }
  }

  return 'No response';
}
