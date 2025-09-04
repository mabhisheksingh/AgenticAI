/**
 * ThemeToggle Component
 * 
 * A flexible theme toggle component that supports multiple variants:
 * - 'switch': A toggle switch with light/dark icons (default)
 * - 'button': A simple icon button
 * - 'icon-only': A small icon button for compact spaces
 * 
 * Usage:
 * <ThemeToggle variant="switch" />    // Full switch with icons
 * <ThemeToggle variant="button" />    // Icon button
 * <ThemeToggle variant="icon-only" /> // Small icon button
 */

import React from 'react';
import {
  IconButton,
  Switch,
  FormControlLabel,
  Box,
  Tooltip,
  useTheme as useMUITheme,
} from '@mui/material';
import {
  Brightness4,
  Brightness7,
  DarkMode,
  LightMode,
} from '@mui/icons-material';
import { useTheme } from '../../contexts/ThemeContext';

const ThemeToggle = ({ variant = 'switch' }) => {
  const { mode, toggleTheme, isDark } = useTheme();
  const muiTheme = useMUITheme();

  if (variant === 'button') {
    return (
      <Tooltip title={`Switch to ${isDark ? 'light' : 'dark'} mode`}>
        <IconButton
          onClick={toggleTheme}
          sx={{
            color: 'text.primary',
            '&:hover': {
              backgroundColor: 'action.hover',
            },
          }}
        >
          {isDark ? <LightMode /> : <DarkMode />}
        </IconButton>
      </Tooltip>
    );
  }

  if (variant === 'icon-only') {
    return (
      <Tooltip title={`Switch to ${isDark ? 'light' : 'dark'} mode`}>
        <IconButton
          onClick={toggleTheme}
          size="small"
          sx={{
            p: 1,
            color: 'text.secondary',
            '&:hover': {
              color: 'primary.main',
              backgroundColor: 'action.hover',
            },
          }}
        >
          {isDark ? <Brightness7 fontSize="small" /> : <Brightness4 fontSize="small" />}
        </IconButton>
      </Tooltip>
    );
  }

  // Default switch variant
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        py: 1,
        px: 1.5,
        borderRadius: 1,
        backgroundColor: 'background.paper',
        border: 1,
        borderColor: 'divider',
      }}
    >
      <LightMode
        fontSize="small"
        sx={{
          color: isDark ? 'text.disabled' : 'primary.main',
          transition: 'color 0.2s ease',
        }}
      />
      <Switch
        checked={isDark}
        onChange={toggleTheme}
        size="small"
        sx={{
          '& .MuiSwitch-switchBase.Mui-checked': {
            color: 'primary.main',
          },
          '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
            backgroundColor: 'primary.main',
          },
        }}
      />
      <DarkMode
        fontSize="small"
        sx={{
          color: isDark ? 'primary.main' : 'text.disabled',
          transition: 'color 0.2s ease',
        }}
      />
    </Box>
  );
};

export default ThemeToggle;