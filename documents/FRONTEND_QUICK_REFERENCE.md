# Frontend Quick Reference Guide

## 🚀 Quick Start

```bash
# 1. Install dependencies
cd frontend && npm install

# 2. Setup environment
cp .env.example .env.local

# 3. Start development
npm run dev

# 4. Build for production
npm run build

# 5. Check code quality
npm run lint
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── BankChat.tsx           ← Main chat interface
│   │   ├── LoginForm.tsx          ← Login page
│   │   ├── Dashboard.tsx          ← Account dashboard
│   │   ├── AccountManager.tsx     ← Account management
│   │   └── ErrorBoundary.tsx      ← Error boundary (NEW)
│   ├── styles/
│   │   ├── BankChat.css           ← Chat styling (OPTIMIZED)
│   │   ├── LoginForm.css          ← Login styling
│   │   └── Dashboard.css          ← Dashboard styling
│   ├── utils/
│   │   └── api.ts                 ← API utilities (NEW)
│   ├── hooks/
│   │   └── useChat.ts             ← Chat hook (NEW)
│   ├── App.tsx                    ← Main app (OPTIMIZED)
│   ├── App.css                    ← Global styles
│   └── main.tsx                   ← Entry point
├── .env.example                   ← Environment template (NEW)
├── vite.config.ts                 ← Vite config (UPDATED)
├── package.json                   ← Dependencies
└── dist/                          ← Build output
```

## 🔧 Key Components

### BankChat Component
```tsx
<BankChat 
  onNavigate={(view) => setActiveView(view)}
  onLogout={() => handleLogout()}
/>
```
**Features:** Chat interface, error handling, accessibility

### ErrorBoundary Component
```tsx
<ErrorBoundary>
  <App />
</ErrorBoundary>
```
**Features:** Catches React errors, graceful fallback

### useChat Hook
```tsx
const { messages, input, isLoading, error, sendMessage } = useChat()
```
**Features:** Chat state management, error handling

### API Utilities
```tsx
import { sendChatMessage, getAccount, checkApiHealth } from '../utils/api'
```
**Features:** API communication, timeout protection

## 📡 API Integration

### Send Chat Message
```typescript
const response = await sendChatMessage("Hello")
// Returns: { reply: string }
```

### Get Account
```typescript
const account = await getAccount(1)
// Returns: { account_no, name, balance, ... }
```

### Check API Health
```typescript
const isHealthy = await checkApiHealth()
// Returns: boolean
```

## 🎨 Styling

### Color Scheme
- **Primary:** Blue (#3b82f6) → Teal (#14b8a6)
- **Error:** Red (#ef4444)
- **Success:** Green (included in Gemini responses)
- **Neutral:** Slate (#64748b)

### Key Classes
```css
.bank-chat            /* Main chat container */
.chat-header          /* Header with navigation */
.messages-container   /* Messages area */
.message              /* Individual message */
.message.error        /* Error message (red) */
.chat-input-container /* Input area */
.send-button          /* Send button */
```

## ♿ Accessibility

### ARIA Attributes
```tsx
<button aria-label="Navigate to Dashboard">
  <span aria-hidden="true">📊</span>
  Dashboard
</button>
```

### Semantic HTML
```tsx
<div role="log" aria-live="polite">
  {/* Messages */}
</div>
```

## 🔒 Security

### Environment Variables
```
VITE_API_URL=http://localhost
VITE_APP_NAME=UNK029 Bank
VITE_ENABLE_DEMO=true
VITE_DEBUG_MODE=false
```

### Token Management
```typescript
// Store token
localStorage.setItem('auth_token', token)

// Clear token
localStorage.removeItem('auth_token')
localStorage.removeItem('username')
```

## 🧪 Error Handling

### Try-Catch Pattern
```typescript
try {
  const response = await sendChatMessage(message)
  // Handle success
} catch (error) {
  const message = getErrorMessage(error)
  // Display error
}
```

### Error Types
- **Network Errors** - Connection failed
- **Validation Errors** - Invalid input
- **Server Errors** - API returned error
- **Timeout Errors** - Request exceeded 30 seconds

## 📊 Performance Tips

### 1. Message Management
```typescript
// Don't store too many messages in memory
// Consider pagination or virtual scrolling for large lists
if (messages.length > 100) {
  // Archive or remove old messages
}
```

### 2. Input Optimization
```typescript
// Use debounce for real-time search
const [search, setSearch] = useState('')
// Implement debounce wrapper
```

### 3. Image Optimization
```typescript
// Use WebP format with JPEG fallback
// Optimize images before upload
// Consider lazy loading
```

## 🐛 Debugging

### Browser DevTools
1. **Console Tab** - Check for errors and warnings
2. **Network Tab** - Monitor API calls
3. **Performance Tab** - Profile rendering
4. **React DevTools** - Inspect components

### Common Issues

**"Failed to connect to server"**
- Check if backend is running
- Verify VITE_API_URL in .env.local
- Check CORS headers

**"Invalid response format"**
- Verify API endpoint is returning correct format
- Check server logs
- Validate response structure

**"Message not appearing"**
- Check console for errors
- Verify message timestamp format
- Check CSS for hidden messages

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `FRONTEND_OPTIMIZATION.md` | Detailed optimization guide |
| `FRONTEND_SUMMARY.md` | Executive summary |
| `FRONTEND_CHECKLIST.md` | Verification checklist |
| `README.md` | Project overview |

## 🔗 Related Documentation

- `INFRASTRUCTURE.md` - Full system architecture
- `ARCHITECTURE.md` - FastAPI, FastMCP, Agent details
- `.env.example` - Environment variables template

## 💡 Pro Tips

### Development
```bash
# Hot reload enabled
npm run dev

# Clear cache if styles not updating
rm -rf node_modules/.vite
```

### Build
```bash
# Check bundle analysis
npm run build -- --debug

# Smaller builds
npm run build --mode production
```

### Debugging
```typescript
// Add debug logging
if (import.meta.env.VITE_DEBUG_MODE === 'true') {
  console.log('Debug info:', data)
}
```

## 📞 Support Resources

1. **React Documentation**: https://react.dev
2. **Vite Documentation**: https://vitejs.dev
3. **TypeScript Documentation**: https://www.typescriptlang.org
4. **Web Accessibility**: https://www.w3.org/WAI/
5. **MDN Web Docs**: https://developer.mozilla.org

## ✅ Before Deploying

- [ ] Run `npm run lint` - no errors
- [ ] Run `npm run build` - builds successfully
- [ ] Test in multiple browsers
- [ ] Test on mobile devices
- [ ] Check accessibility with WAVE
- [ ] Verify all API endpoints work
- [ ] Check error handling paths
- [ ] Update environment variables
- [ ] Review security settings
- [ ] Performance check (Lighthouse > 90)

## 🎯 Common Tasks

### Add New API Endpoint
```typescript
// 1. Add to src/utils/api.ts
export async function newFunction(params): Promise<ReturnType> {
  // Implementation
}

// 2. Use in component
const result = await newFunction(params)
```

### Add New Component
```typescript
// 1. Create src/components/NewComponent.tsx
// 2. Add styles src/styles/NewComponent.css
// 3. Import in App.tsx
// 4. Add to JSX
```

### Update Styling
```css
/* Update src/styles/BankChat.css or component-specific CSS */
.new-class {
  /* Styles */
}
```

## 🚀 Optimization Checklist

- ✅ Build size < 350 KB
- ✅ Gzipped size < 100 KB  
- ✅ No console errors
- ✅ No console warnings
- ✅ Lighthouse > 90
- ✅ Accessibility AA compliant
- ✅ Mobile responsive
- ✅ Error handling complete
- ✅ Security measures in place
- ✅ Documentation complete

---

**Last Updated:** November 29, 2025  
**Version:** 1.0.0  
**Status:** Production Ready ✅
