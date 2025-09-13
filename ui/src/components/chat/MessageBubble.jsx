import React from 'react';
import {
  Box,
  Typography,
  Avatar,
  Paper,
  CircularProgress,
  Chip,
} from '@mui/material';
import { Person, SmartToy, Build } from '@mui/icons-material';

const MessageBubble = ({ message, isLoading = false }) => {
  // Handle loading state
  if (isLoading) {
    return (
      <Box display="flex" gap={1.5} mb={3}>
        <Avatar 
          sx={{ 
            width: 32, 
            height: 32,
            background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
          }}
        >
          <SmartToy fontSize="small" />
        </Avatar>
        <Box flex={1}>
          <Typography variant="body2" fontWeight={600} mb={1}>
            Assistant
          </Typography>
          <Paper
            elevation={0}
            sx={{
              p: 2,
              backgroundColor: (theme) => 
                theme.palette.mode === 'dark' 
                  ? 'rgba(255, 255, 255, 0.05)'
                  : 'grey.50',
              border: '1px solid',
              borderColor: 'divider',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <CircularProgress size={16} />
            <Typography variant="body2" color="text.secondary">
              Thinking...
            </Typography>
          </Paper>
        </Box>
      </Box>
    );
  }

  // Handle invalid message object - comprehensive validation
  if (!message || typeof message !== 'object') {
    console.warn('MessageBubble: Invalid message prop received:', message);
    return null;
  }

  // Validate that message has required properties
  if (!message.hasOwnProperty('role')) {
    console.warn('MessageBubble: Message missing role property:', message);
    return null;
  }

  const isUser = message.role === 'user';
  const messageContent = message.text || message.content || '';
  const isProcessing = message.isProcessing || false;
  const toolCall = message.toolCall || '';
  
  // Don't render if there's no content and not loading
  if (!messageContent && !isLoading) {
    console.warn('MessageBubble: Message has no content:', message);
    return null;
  }

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

  const formattedContent = formatContent(messageContent);

  return (
    <Box display="flex" gap={1.5} mb={3}>
      <Avatar 
        sx={{ 
          width: 32, 
          height: 32,
          background: isUser 
            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        }}
      >
        {isUser ? <Person fontSize="small" /> : <SmartToy fontSize="small" />}
      </Avatar>
      <Box flex={1}>
        <Typography variant="body2" fontWeight={600} mb={1}>
          {isUser ? 'You' : 'Assistant'}
        </Typography>
        {toolCall && (
          <Box mb={1}>
            <Chip
              icon={<Build fontSize="small" />}
              label={toolCall}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Box>
        )}
        <Paper
          elevation={0}
          sx={{
            p: 2,
            backgroundColor: isUser ? 'primary.50' : 'grey.50',
            border: '1px solid',
            borderColor: isUser ? 'primary.200' : 'divider',
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
            ...(isUser && {
              backgroundColor: (theme) => 
                theme.palette.mode === 'dark' 
                  ? 'rgba(26, 115, 232, 0.15)'
                  : 'rgba(26, 115, 232, 0.08)',
            }),
            ...(!isUser && {
              backgroundColor: (theme) => 
                theme.palette.mode === 'dark' 
                  ? 'rgba(255, 255, 255, 0.05)'
                  : 'rgba(0, 0, 0, 0.02)',
            }),
          }}
        >
          {isProcessing ? (
            <Box display="flex" alignItems="center" gap={1}>
              <CircularProgress size={16} />
              <Typography variant="body1" color="text.secondary">
                {formattedContent || 'Processing your request...'}
              </Typography>
            </Box>
          ) : (
            <Typography variant="body1">
              {formattedContent}
            </Typography>
          )}
        </Paper>
      </Box>
    </Box>
  );
};

export default MessageBubble;