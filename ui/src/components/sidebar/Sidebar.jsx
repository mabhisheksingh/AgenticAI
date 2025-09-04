import React from 'react';
import {
  Box,
  Typography,
  Drawer,
  Chip,
  Divider,
  alpha,
} from '@mui/material';
import ThreadList from './ThreadList';

const Sidebar = ({
  open,
  threads,
  activeThreadId,
  loadingThreads,
  onSelectThread,
  onDeleteThread,
  onRenameThread,
}) => {
  const drawerWidth = 280;

  const content = (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'background.paper',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2.5,
          borderBottom: 1,
          borderColor: 'divider',
          backgroundColor: 'background.paper',
          position: 'sticky',
          top: 0,
          zIndex: 1,
        }}
      >
        <Box display="flex" alignItems="center" gap={1}>
          <Typography variant="h6" color="text.primary">
            Chat History
          </Typography>
          {threads.length > 0 && (
            <Chip
              label={threads.length}
              size="small"
              sx={{
                height: 20,
                fontSize: '0.75rem',
                fontWeight: 500,
                backgroundColor: (theme) => alpha(theme.palette.text.secondary, 0.1),
                color: 'text.secondary',
              }}
            />
          )}
        </Box>
      </Box>

      {/* Thread List */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          p: 1.5,
          '&::-webkit-scrollbar': {
            width: 6,
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
        <ThreadList
          threads={threads}
          activeThreadId={activeThreadId}
          loading={loadingThreads}
          onSelectThread={onSelectThread}
          onDeleteThread={onDeleteThread}
          onRenameThread={onRenameThread}
        />
      </Box>
    </Box>
  );

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: open ? drawerWidth : 0,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          border: 'none',
          borderRight: 1,
          borderColor: 'divider',
          position: 'relative',
        },
      }}
    >
      {content}
    </Drawer>
  );
};

export default Sidebar;