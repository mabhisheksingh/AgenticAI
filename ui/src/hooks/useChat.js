import { useState, useCallback } from 'react';
import { api } from '../api/controller';
import { generateThreadLabel, validateThreadLabel } from '../utils/threadUtils';

const useChat = (userId, threadId, setThreadId) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = useCallback(async (text, threadLabel = null) => {
    if (!text.trim() || loading) return;

    // Generate thread label from first 10 words - ALWAYS REQUIRED
    let generatedThreadLabel = threadLabel;
    if (!generatedThreadLabel) {
      generatedThreadLabel = generateThreadLabel(text);
    }
    
    // Ensure thread label is limited to 10 words
    generatedThreadLabel = validateThreadLabel(generatedThreadLabel);

    // Add user message immediately
    const userMessage = {
      id: `user-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      role: 'user',
      text: text.trim()
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    // Create assistant message placeholder
    const assistantId = `assistant-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const assistantPlaceholder = {
      id: assistantId,
      role: 'assistant',
      text: ''
    };
    setMessages((prev) => [...prev, assistantPlaceholder]);

    const controller = new AbortController();
    let aggregated = '';
    let firstTokenReceived = false; // Track if we've received the first token

    try {
      await api.chatStream({
        userId,
        threadId,
        message: text,
        threadLabel: generatedThreadLabel, // ALWAYS send thread label (mandatory)
        signal: controller.signal,
        onEvent: (payload) => {
          try {
            const obj = JSON.parse(payload);
            
            // Handle thread ID update
            if (obj?.threadId && !threadId) {
              setThreadId(obj.threadId);
              return;
            }
            
            // Handle token streaming
            if (obj?.type === 'token' && obj?.content) {
              // Hide "Thinking..." on first token
              if (!firstTokenReceived) {
                firstTokenReceived = true;
                console.log('First token received, hiding "Thinking..."');
                setLoading(false);
              }
              
              aggregated += obj.content;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantId ? { ...msg, text: aggregated } : msg
                )
              );
            } else if (obj?.type === 'error') {
              setError(obj.content || 'Streaming error occurred');
              setLoading(false);
            }
          } catch {
            // Handle plain text fallback
            if (!firstTokenReceived) {
              firstTokenReceived = true;
              console.log('First content received (plain text), hiding "Thinking..."');
              setLoading(false);
            }
            
            aggregated += payload;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantId ? { ...msg, text: aggregated } : msg
              )
            );
          }
        },
        onDone: () => {
          // Ensure loading is false when streaming is complete
          setLoading(false);
        },
        onError: (err) => {
          setLoading(false);
          setError(err.message || 'Failed to send message');
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId
                ? { ...msg, text: `Error: ${err.message || 'Unknown error'}` }
                : msg
            )
          );
        },
      });
    } catch (err) {
      setLoading(false);
      setError(err.message || 'Failed to send message');
      // Remove the placeholder assistant message and show error message
      setMessages((prev) => [
        ...prev.filter(msg => msg.id !== assistantId),
        {
          id: `error-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          role: 'assistant',
          text: `Error: ${err.message || 'Unknown error'}`
        }
      ]);
    }
  }, [userId, threadId, setThreadId, loading]);

  const loadMessages = useCallback((threadMessages) => {
    if (!Array.isArray(threadMessages)) {
      console.warn('loadMessages: Invalid threadMessages, expected array:', threadMessages);
      setMessages([]);
      return;
    }
    
    const formattedMessages = threadMessages
      .filter((msg) => {
        // Comprehensive validation
        if (!msg || typeof msg !== 'object') {
          console.warn('loadMessages: Filtering invalid message:', msg);
          return false;
        }
        if (!msg.role) {
          console.warn('loadMessages: Filtering message without role:', msg);
          return false;
        }
        if (!msg.content && !msg.text) {
          console.warn('loadMessages: Filtering message without content:', msg);
          return false;
        }
        return true;
      })
      .map((msg) => ({
        role: msg.role,
        text: msg.content || msg.text || '',
        id: msg.id || `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      }));
    
    console.log('loadMessages: Setting formatted messages:', formattedMessages);
    setMessages(formattedMessages);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    loading,
    error,
    sendMessage,
    loadMessages,
    clearMessages,
  };
};

export default useChat;