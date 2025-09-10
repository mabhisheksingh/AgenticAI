import { useState, useCallback } from 'react';
import { api } from '../api/controller';
import { generateThreadLabel, validateThreadLabel } from '../utils/threadUtils';

const useChat = (user_id, thread_id, setThread_id) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Format content properly - handle objects with type/text structure
  const formatContent = (content) => {
    if (typeof content === 'string') {
      return content;
    }
    
    if (Array.isArray(content)) {
      // Handle array of content parts
      return content.map(part => {
        if (typeof part === 'string') {
          return part;
        } else if (part && typeof part === 'object') {
          if (part.type === 'text') {
            return part.text || '';
          }
          // Handle other types of content parts
          return JSON.stringify(part);
        }
        return String(part);
      }).join('\n');
    }
    
    if (content && typeof content === 'object') {
      // Handle single object with type/text structure
      if (content.type === 'text') {
        return content.text || '';
      }
      // Handle other object structures
      if (content.text) {
        return content.text;
      }
      return JSON.stringify(content);
    }
    
    return String(content);
  };

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
    let isProcessing = false; // Track if we're in processing mode

    try {
      // Normalize thread_id - ensure it's null for invalid values
      const normalizedThreadId = thread_id && thread_id !== 'null' && thread_id !== 'undefined' && thread_id !== 'None' ? thread_id : null;
      
      await api.chatStream({
        user_id,
        thread_id: normalizedThreadId,
        message: text,
        threadLabel: generatedThreadLabel, // ALWAYS send thread label (mandatory)
        signal: controller.signal,
        onEvent: (payload) => {
          try {
            const obj = JSON.parse(payload);
            
            // Handle thread ID update
            if (obj?.threadId && !normalizedThreadId) {
              setThread_id(obj.threadId);
              return;
            }
            
            // Handle processing state
            if (obj?.type === 'processing') {
              isProcessing = true;
              // Update assistant message to show processing state
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantId ? { ...msg, text: 'Processing your request...', isProcessing: true } : msg
                )
              );
              return;
            }
            
            // Handle tool call events
            if (obj?.type === 'tool_call' && obj?.content) {
              // Update assistant message to show tool call info
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantId ? { ...msg, text: obj.content, isProcessing: true } : msg
                )
              );
              return;
            }
            
            // Handle token streaming
            if ( (obj?.type === 'token'|| obj?.type === 'user' ) && obj?.content) {
              // Hide "Thinking..." on first token and exit processing mode
              if (!firstTokenReceived) {
                firstTokenReceived = true;
                isProcessing = false;
                console.log('First token received, hiding "Thinking..."');
                setLoading(false);
              }
              
              aggregated += obj.content;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantId ? { ...msg, text: aggregated, isProcessing: false } : msg
                )
              );
            } else if (obj?.type === 'error') {
              setError(obj.content || 'Streaming error occurred');
              setLoading(false);
              isProcessing = false;
              // Update message to show error
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantId ? { ...msg, text: `Error: ${obj.content || 'Unknown error'}`, isProcessing: false } : msg
                )
              );
            } else {
              // Handle any other unknown event types
              console.log('Unknown event type received:', obj);
            }
          } catch {
            // Handle plain text fallback
            if (!firstTokenReceived) {
              firstTokenReceived = true;
              isProcessing = false;
              console.log('First content received (plain text), hiding "Thinking..."');
              setLoading(false);
            }
            
            aggregated += payload;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantId ? { ...msg, text: aggregated, isProcessing: false } : msg
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
          isProcessing = false;
          setError(err.message || 'Failed to send message');
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId
                ? { ...msg, text: `Error: ${err.message || 'Unknown error'}`, isProcessing: false }
                : msg
            )
          );
        },
      });
    } catch (err) {
      setLoading(false);
      isProcessing = false;
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
  }, [user_id, thread_id, setThread_id, loading]);

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
        text: formatContent(msg.content || msg.text || ''),
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