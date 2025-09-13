# UI (Frontend)

## Stack
- Vite + React
- Material-UI components
- SSE streaming for real-time responses

## Development
```bash
cd ui
npm install
npm run dev  # http://localhost:5173
```

## Structure (ui/src/)
```
components/
  chat/
    ChatArea.jsx
    ChatInput.jsx
    MessageBubble.jsx
    index.js
  sidebar/
    Sidebar.jsx
    ThreadItem.jsx
    ThreadList.jsx
    index.js
  layout/
    TopBar.jsx
    Footer.jsx
    index.js
  ui/
    UserSelector.jsx
    ThemeToggle.jsx
    ErrorBoundary.jsx
    index.js
hooks/
  useChat.js
  useThreads.js
  index.js
api/
  config.js
  controller.js
  endpoints.js
  http.js
utils/
  threadUtils.js
  index.js
contexts/
  ThemeContext.jsx
App.jsx
main.jsx
```

## Features
- Thread management (create, rename, delete, select)
- Real-time streaming display for model responses
- Theme toggle (dark/light)

## Backend Connection
- Default backend URL: `http://localhost:8080`
- Set CORS in backend `.env` accordingly:
  - `CORS_ORIGINS=http://localhost:5173`
