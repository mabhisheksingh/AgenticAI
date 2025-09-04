import React from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Chip,
  alpha,
} from '@mui/material';
import { ChatBubbleOutline } from '@mui/icons-material';
import ThreadItem from './ThreadItem';

const ThreadList = ({
  threads,
  activeThreadId,
  loading,
  onSelectThread,
  onDeleteThread,
  onRenameThread,
}) => {
  if (loading) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        py={4}
        gap={2}
      >
        <CircularProgress size={32} />
        <Typography variant="body2" color="text.secondary">
          Loading threads...
        </Typography>
      </Box>
    );
  }

  if (threads.length === 0) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        py={6}
        px={3}
        textAlign="center"
      >
        <ChatBubbleOutline
          sx={{
            fontSize: 48,
            color: 'text.disabled',
            mb: 2,
          }}
        />
        <Typography variant="body1" color="text.secondary" mb={1}>
          No conversations yet
        </Typography>
        <Typography variant="body2" color="text.disabled" sx={{ fontSize: '0.8rem' }}>
          Start a new chat to see your conversations here
        </Typography>
      </Box>
    );
  }

  return (
    <Box className="thread-list">
      {threads.map((thread) => (
        <ThreadItem
          key={thread.thread_id || thread.id}
          thread={thread}
          isActive={(thread.thread_id || thread.id) === activeThreadId}
          onSelect={onSelectThread}
          onDelete={onDeleteThread}
          onRename={onRenameThread}
        />
      ))}
    </Box>
  );
};

export default ThreadList;