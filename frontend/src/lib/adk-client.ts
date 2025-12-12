// Simple ADK client - Frontend → ADK → MCP → FastAPI → DB

export async function createSession(userId: string) {
  const res = await fetch(`/apps/bank_agent/users/${userId}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  });
  if (!res.ok) throw new Error('Failed to create session');
  return res.json();
}

export async function sendMessage(
  userId: string,
  sessionId: string,
  message: string
): Promise<string> {
  const res = await fetch('/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      app_name: 'bank_agent',
      user_id: userId,
      session_id: sessionId,
      new_message: { role: 'user', parts: [{ text: message }] },
    }),
  });

  if (!res.ok) throw new Error('Failed to send message');

  const events = await res.json();
  
  // Extract last assistant message (response is array of events)
  for (let i = events.length - 1; i >= 0; i--) {
    const event = events[i];
    // Check author is not 'user' and has text content
    if (event.content?.parts && event.author !== 'user') {
      const text = event.content.parts.map((p: any) => p.text || '').join('');
      if (text) return text;
    }
  }

  return 'No response from assistant';
}
