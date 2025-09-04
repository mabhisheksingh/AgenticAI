import React, { useState } from 'react';
import {
  Box,
  Typography,
  IconButton,
  TextField,
  Chip,
  Tooltip,
  alpha,
} from '@mui/material';
import {
  Delete,
  Edit,
  Check,
  Close,
} from '@mui/icons-material';
import { getThreadDisplayName } from '../../utils/threadUtils';

const ThreadItem = ({
  thread,
  isActive,
  onSelect,
  onDelete,
  onRename,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState('');

  const threadId = thread.thread_id || thread.id;
  const threadLabel = thread.thread_label || thread.title;
  const displayTitle = getThreadDisplayName(thread);
  const isShowingThreadId = !threadLabel || !threadLabel.trim(); // Check if showing ID as fallback

  const handleEdit = () => {
    // Use the actual thread label for editing, or empty string if showing thread ID
    setEditValue(threadLabel && threadLabel.trim() ? threadLabel : '');
    setIsEditing(true);
  };

  const handleSave = () => {
    if (editValue.trim()) {
      onRename(thread, editValue.trim());
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditValue('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  const handleDelete = () => {
    const confirmText = isShowingThreadId 
      ? `Delete thread ${displayTitle}?` 
      : `Delete "${displayTitle}"?`;
    if (window.confirm(confirmText)) {
      onDelete(threadId);
    }
  };

  return (
    <Box
      onClick={() => !isEditing && onSelect(thread)}
      sx={{
        p: 1.5,
        borderRadius: 1.5,
        cursor: isEditing ? 'default' : 'pointer',
        transition: 'all 0.2s ease',
        border: '1px solid transparent',
        backgroundColor: isActive
          ? (theme) => alpha(theme.palette.primary.main, 0.08)
          : 'transparent',
        borderColor: isActive ? 'primary.main' : 'transparent',
        '&:hover': !isEditing && {
          backgroundColor: (theme) => alpha(theme.palette.action.hover, 0.1),
          borderColor: 'divider',
          transform: 'translateY(-1px)',
        },
        mb: 0.5,
      }}
    >
      <Box display="flex" alignItems="center" gap={1}>
        {isEditing ? (
          <TextField
            fullWidth
            size="small"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyPress={handleKeyPress}
            onBlur={handleSave}
            autoFocus
            onClick={(e) => e.stopPropagation()}
            sx={{
              '& .MuiOutlinedInput-root': {
                height: 32,
                fontSize: '0.875rem',
              },
            }}
          />
        ) : (
          <Box sx={{ flex: 1, overflow: 'hidden' }}>
            <Typography
              variant="body2"
              sx={{
                fontWeight: isActive ? 600 : 500,
                color: isActive ? 'primary.main' : 'text.primary',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                lineHeight: 1.4,
                fontStyle: isShowingThreadId ? 'italic' : 'normal',
                opacity: isShowingThreadId ? 0.7 : 1,
              }}
              onDoubleClick={handleEdit}
              title={isShowingThreadId ? `Thread ID: ${displayTitle}` : `Thread: ${displayTitle}`}
            >
              {displayTitle}
            </Typography>
            {isShowingThreadId && (
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  fontSize: '0.7rem',
                  lineHeight: 1,
                  display: 'block',
                }}
              >
                No label - showing ID
              </Typography>
            )}
          </Box>
        )}

        {isEditing ? (
          <Box display="flex" gap={0.5}>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleSave();
              }}
              sx={{ p: 0.5 }}
            >
              <Check fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleCancel();
              }}
              sx={{ p: 0.5 }}
            >
              <Close fontSize="small" />
            </IconButton>
          </Box>
        ) : (
          <Box
            display="flex"
            gap={0.5}
            sx={{
              opacity: isActive ? 1 : 0,
              transition: 'opacity 0.2s ease',
              '.thread-item:hover &': {
                opacity: 1,
              },
            }}
          >
            <Tooltip title="Rename">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleEdit();
                }}
                sx={{
                  p: 0.5,
                  color: 'text.secondary',
                  '&:hover': {
                    color: 'primary.main',
                    backgroundColor: (theme) => alpha(theme.palette.primary.main, 0.1),
                  },
                }}
              >
                <Edit fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Delete">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete();
                }}
                sx={{
                  p: 0.5,
                  color: 'text.secondary',
                  '&:hover': {
                    color: 'error.main',
                    backgroundColor: (theme) => alpha(theme.palette.error.main, 0.1),
                    transform: 'scale(1.1)',
                  },
                }}
              >
                <Delete fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default ThreadItem;