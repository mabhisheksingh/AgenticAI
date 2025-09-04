import React, { useState, useEffect } from 'react';
import { Box } from '@mui/material';
import { ThemeContextProvider } from './contexts/ThemeContext';

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
  const [user_id, setUser_id] = useState(() =>
    localStorage.getItem('user_id') || `user-${Math.random().toString(36).slice(2, 8)}`
  );
  
  // UI state
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [thread_id, setThread_id] = useState(() => {
    const stored = localStorage.getItem('thread_id');
    // Ensure we return null for invalid/empty values
    return stored && stored !== 'null' && stored !== 'undefined' ? stored : null;
  });

  // Custom hooks
  const {
    threads,
    loading: loadingThreads,
    error: threadsError,
    loadThreads,
    deleteThread,
    renameThread,
    loadThreadDetails,
  } = useThreads(user_id);

  const {
    messages,
    loading: chatLoading,
    error: chatError,
    sendMessage,
    loadMessages,
    clearMessages,
  } = useChat(user_id, thread_id, setThread_id);

  // Persist user data
  useEffect(() => {
    localStorage.setItem('user_id', user_id);
  }, [user_id]);

  useEffect(() => {
    if (thread_id) {
      localStorage.setItem('thread_id', thread_id);
    } else {
      localStorage.removeItem('thread_id');
    }
  }, [thread_id]);

  // Handlers
  const handleSelectThread = async (thread) => {
    const id = thread.thread_id || thread.id;
    
    if (id !== thread_id) {
      clearMessages();
      setThread_id(id);
      
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
    if (success && thread_id === id) {
      setThread_id(null);
      clearMessages();
    }
  };

  const handleRenameThread = async (thread, newLabel) => {
    await renameThread(thread, newLabel);
  };

  const handleNewThread = () => {
    setThread_id(null);
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

  const handleUserSelect = async (selectedUser_id) => {
    if (selectedUser_id && selectedUser_id !== user_id) {
      // Clear current chat state
      setThread_id(null);
      clearMessages();
      
      // Update user ID
      setUser_id(selectedUser_id);
      
      // Load threads for the new user will be handled by useThreads hook
      // when user_id changes, it will automatically reload
    }
  };

  // Get current thread title
  const currentThread = threads.find((t) => (t.thread_id || t.id) === thread_id);
  const threadTitle = currentThread?.thread_label || currentThread?.title || null;

  return (
    <ThemeContextProvider>
      <ErrorBoundary>
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
          {/* Top Bar */}
          <TopBar
            sidebarOpen={sidebarOpen}
            onToggleSidebar={handleToggleSidebar}
            user_id={user_id}
            onUser_idChange={setUser_id}
            onUserSelect={handleUserSelect}
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
                activeThreadId={thread_id}
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
                  isNewThread={!thread_id}
                />
              </ErrorBoundary>
              
              <ErrorBoundary>
                <ChatInput
                  onSendMessage={handleSendMessage}
                  loading={chatLoading}
                  disabled={!user_id}
                  isNewThread={!thread_id}
                />
              </ErrorBoundary>
            </Box>
          </Box>

          {/* Footer */}
          <Footer />
        </Box>
      </ErrorBoundary>
    </ThemeContextProvider>
  );
}
