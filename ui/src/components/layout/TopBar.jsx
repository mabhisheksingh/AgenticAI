import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  TextField,
  Box,
  IconButton,
  Chip,
  alpha,
} from '@mui/material';
import {
  Menu,
  MenuOpen,
  Add,
  Refresh,
} from '@mui/icons-material';

const TopBar = ({
  sidebarOpen,
  onToggleSidebar,
  userId,
  onUserIdChange,
  onLoadThreads,
  onNewThread,
}) => {
  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        backgroundColor: 'background.paper',
        borderBottom: 1,
        borderColor: 'divider',
        color: 'text.primary',
      }}
    >
      <Toolbar sx={{ gap: 2 }}>
        <IconButton
          edge="start"
          onClick={onToggleSidebar}
          aria-label="toggle sidebar"
          sx={{
            mr: 1,
            color: 'primary.main',
            backgroundColor: (theme) => alpha(theme.palette.primary.main, 0.1),
            '&:hover': {
              backgroundColor: (theme) => alpha(theme.palette.primary.main, 0.2),
            },
          }}
        >
          {sidebarOpen ? <MenuOpen /> : <Menu />}
        </IconButton>

        <Typography
          variant="h6"
          component="div"
          sx={{
            fontWeight: 600,
            letterSpacing: 0.4,
            color: 'text.primary',
          }}
        >
          AgenticAI
        </Typography>

        <Box sx={{ flexGrow: 1 }} />

        {/* Controls */}
        <Box display="flex" alignItems="center" gap={1.5}>
          <Box display="flex" alignItems="center" gap={1}>
            <Chip
              label="User ID"
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.75rem' }}
            />
            <TextField
              size="small"
              value={userId}
              onChange={(e) => onUserIdChange(e.target.value)}
              placeholder="user-123"
              sx={{
                width: 160,
                '& .MuiOutlinedInput-root': {
                  height: 32,
                  fontSize: '0.875rem',
                },
              }}
            />
          </Box>

          <Button
            variant="outlined"
            size="small"
            startIcon={<Refresh />}
            onClick={onLoadThreads}
            sx={{ textTransform: 'none' }}
          >
            Refresh
          </Button>

          <Button
            variant="contained"
            size="small"
            startIcon={<Add />}
            onClick={onNewThread}
            sx={{ textTransform: 'none' }}
          >
            New Chat
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default TopBar;