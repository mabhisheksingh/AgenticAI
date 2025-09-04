import React, { useState, useEffect } from 'react';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import { theme } from './theme/theme';

// Components
import TopBar from './components/layout/TopBar';
import Sidebar from './components/sidebar/Sidebar';
import ChatArea from './components/chat/ChatArea';
import ChatInput from './components/chat/ChatInput';
import Footer from './components/layout/Footer';
import ErrorBoundary from './components/ui/ErrorBoundary';

// Hooks
import useThreads from './hooks/useThreads';
import useChat from './hooks/useChat';

export default function App() {
  // User state
  const [userId, setUserId] = useState(() =>
    localStorage.getItem('userId') || `user-${Math.random().toString(36).slice(2, 8)}`
  );
  
  // UI state
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [threadId, setThreadId] = useState(() => localStorage.getItem('threadId'));

  // Custom hooks
  const {
    threads,
    loading: loadingThreads,
    error: threadsError,
    loadThreads,
    deleteThread,
    renameThread,
    loadThreadDetails,
  } = useThreads(userId);

  const {
    messages,
    loading: chatLoading,
    error: chatError,
    sendMessage,
    loadMessages,
    clearMessages,
  } = useChat(userId, threadId, setThreadId);

  // Persist user data
  useEffect(() => {
    localStorage.setItem('userId', userId);
  }, [userId]);

  useEffect(() => {
    if (threadId) {
      localStorage.setItem('threadId', threadId);
    } else {
      localStorage.removeItem('threadId');
    }
  }, [threadId]);

  // Handlers
  const handleSelectThread = async (thread) => {
    const id = thread.thread_id || thread.id;
    
    if (id !== threadId) {
      clearMessages();
      setThreadId(id);
      
      try {
        const threadMessages = await loadThreadDetails(id);
        if (threadMessages.length > 0) {
          loadMessages(threadMessages);
        }
      } catch (err) {
        console.error('Error loading thread details:', err);
      }
    }
  };

  const handleDeleteThread = async (id) => {
    const success = await deleteThread(id);
    if (success && threadId === id) {
      setThreadId(null);
      clearMessages();
    }
  };

  const handleRenameThread = async (thread, newLabel) => {
    await renameThread(thread, newLabel);
  };

  const handleNewThread = () => {
    setThreadId(null);
    clearMessages();
  };

  const handleToggleSidebar = () => {
    setSidebarOpen((prev) => !prev);
  };

  const handleSendMessage = async (text) => {
    await sendMessage(text);
    // Refresh threads list after sending a message (especially for new threads)
    if (!loadingThreads) {
      await loadThreads();
    }
  };

  // Get current thread title
  const currentThread = threads.find((t) => (t.thread_id || t.id) === threadId);
  const threadTitle = currentThread?.thread_label || currentThread?.title || null;

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
          {/* Top Bar */}
          <TopBar
            sidebarOpen={sidebarOpen}
            onToggleSidebar={handleToggleSidebar}
            userId={userId}
            onUserIdChange={setUserId}
            onLoadThreads={loadThreads}
            onNewThread={handleNewThread}
          />

          {/* Main Layout */}
          <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
            {/* Sidebar */}
            <ErrorBoundary>
              <Sidebar
                open={sidebarOpen}
                threads={threads}
                activeThreadId={threadId}
                loadingThreads={loadingThreads}
                onSelectThread={handleSelectThread}
                onDeleteThread={handleDeleteThread}
                onRenameThread={handleRenameThread}
              />
            </ErrorBoundary>

            {/* Chat Area */}
            <Box
              sx={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                backgroundColor: 'background.default',
              }}
            >
              <ErrorBoundary>
                <ChatArea
                  messages={messages}
                  loading={chatLoading}
                  threadTitle={threadTitle}
                  isNewThread={!threadId}
                />
              </ErrorBoundary>
              
              <ErrorBoundary>
                <ChatInput
                  onSendMessage={handleSendMessage}
                  loading={chatLoading}
                  disabled={!userId}
                  isNewThread={!threadId}
                />
              </ErrorBoundary>
            </Box>
          </Box>

          {/* Footer */}
          <Footer />
        </Box>
      </ErrorBoundary>
    </ThemeProvider>
  );
}
