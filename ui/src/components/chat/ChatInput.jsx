import React, { useState, useMemo } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  InputAdornment,
  Typography,
  Chip,
} from '@mui/material';
import { Send, Label } from '@mui/icons-material';
import { generateThreadLabel } from '../../utils/threadUtils';

const ChatInput = ({ onSendMessage, loading, disabled, isNewThread = false }) => {
  const [input, setInput] = useState('');

  // Generate thread label preview - always show for any input
  const threadLabelPreview = useMemo(() => {
    if (!input.trim()) return null;
    return generateThreadLabel(input);
  }, [input]);
  
  // Count words in thread label for display
  const threadLabelWordCount = useMemo(() => {
    if (!threadLabelPreview) return 0;
    return threadLabelPreview.replace('...', '').trim().split(/\s+/).length;
  }, [threadLabelPreview]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading || disabled) return;
    
    onSendMessage(text);
    setInput('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.5,
        borderTop: 1,
        borderColor: 'divider',
        backgroundColor: 'background.paper',
        flexShrink: 0,
        maxWidth: 800,
        mx: 'auto',
        width: '100%',
      }}
    >
      {/* Thread Label Preview - always show when typing */}
      {threadLabelPreview && (
        <Box mb={1.5}>
          <Chip
            icon={<Label fontSize="small" />}
            label={isNewThread ? `New Thread: "${threadLabelPreview}"` : `Thread Label: "${threadLabelPreview}"`}
            variant="outlined"
            size="small"
            sx={{
              fontSize: '0.75rem',
              color: 'primary.main',
              borderColor: 'primary.main',
              backgroundColor: (theme) => 
                `${theme.palette.primary.main}08`,
            }}
          />
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ ml: 1 }}
          >
            {isNewThread ? 'This will be your thread name' : 'Thread label for this message'}
            {threadLabelWordCount > 0 && (
              <span style={{ marginLeft: 8, fontSize: '0.7rem', color: threadLabelWordCount >= 10 ? '#f57c00' : 'inherit' }}>
                ({threadLabelWordCount}/10 words)
              </span>
            )}
          </Typography>
        </Box>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <Box display="flex" gap={1.5} alignItems="end">
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={disabled ? "Please select a user first..." : "Ask something..."}
            disabled={loading || disabled}
            variant="outlined"
            size="medium"
            sx={{
              '& .MuiOutlinedInput-root': {
                backgroundColor: 'background.paper',
              },
            }}
            InputProps={{
              endAdornment: input.trim() && (
                <InputAdornment position="end">
                  <Button
                    type="submit"
                    variant="contained"
                    size="small"
                    disabled={loading || disabled || !input.trim()}
                    sx={{
                      minWidth: 40,
                      p: 1,
                      borderRadius: 2,
                    }}
                  >
                    <Send fontSize="small" />
                  </Button>
                </InputAdornment>
              ),
            }}
          />
          {!input.trim() && (
            <Button
              type="submit"
              variant="contained"
              disabled={loading || disabled || !input.trim()}
              sx={{
                minWidth: 56,
                height: 56,
                borderRadius: 2,
              }}
            >
              <Send />
            </Button>
          )}
        </Box>
      </Box>
    </Paper>
  );
};

export default ChatInput;