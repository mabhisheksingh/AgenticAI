import React, { useEffect, useRef } from 'react';
import { Box, Typography, Paper, Chip } from '@mui/material';
import { Add, Forum } from '@mui/icons-material';
import MessageBubble from './MessageBubble';

const ChatArea = ({ messages, loading, threadTitle, isNewThread = false }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages, loading]);

  const displayTitle = isNewThread 
    ? 'New Conversation' 
    : (threadTitle || 'Chat');

  return (
    <Box
      sx={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          backgroundColor: 'background.paper',
          flexShrink: 0,
        }}
      >
        <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
          {isNewThread && (
            <Chip
              icon={<Add fontSize="small" />}
              label="New"
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
          <Typography variant="h6" textAlign="center" color="text.primary">
            {displayTitle}
          </Typography>
          {!isNewThread && (
            <Forum fontSize="small" color="action" />
          )}
        </Box>
        {isNewThread && (
          <Typography
            variant="caption"
            color="text.secondary"
            textAlign="center"
            display="block"
            mt={0.5}
          >
            Your first message will create the thread name
          </Typography>
        )}
      </Paper>

      {/* Messages */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          p: 3,
          maxWidth: 800,
          mx: 'auto',
          width: '100%',
          scrollBehavior: 'smooth',
          '&::-webkit-scrollbar': {
            width: 8,
          },
          '&::-webkit-scrollbar-track': {
            background: 'transparent',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#e1e5e9',
            borderRadius: 1,
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: '#cbd5e1',
          },
        }}
      >
        {Array.isArray(messages) && messages
          .filter((message) => {
            // Comprehensive message validation
            if (!message || typeof message !== 'object') {
              console.warn('ChatArea: Filtering out invalid message:', message);
              return false;
            }
            if (!message.hasOwnProperty('role')) {
              console.warn('ChatArea: Filtering out message without role:', message);
              return false;
            }
            if (!message.text && !message.content) {
              console.warn('ChatArea: Filtering out message without content:', message);
              return false;
            }
            return true;
          })
          .map((message, index) => (
            <MessageBubble key={message.id || `msg-${index}`} message={message} />
          ))
        }
        {loading && <MessageBubble isLoading />}
        <div ref={messagesEndRef} />
      </Box>
    </Box>
  );
};

export default ChatArea;