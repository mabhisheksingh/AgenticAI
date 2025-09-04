import { createTheme } from '@mui/material/styles';

// Create theme function that accepts mode parameter
export const createAppTheme = (mode = 'light') => createTheme({
  palette: {
    mode,
    primary: {
      main: '#1a73e8',
      light: '#4285f4',
      dark: '#1557b0',
    },
    secondary: {
      main: '#f093fb',
      light: '#f5576c',
      dark: '#c2185b',
    },
    background: {
      default: mode === 'light' ? '#f6f8fc' : '#121212',
      paper: mode === 'light' ? '#ffffff' : '#1e1e1e',
    },
    text: {
      primary: mode === 'light' ? '#1f2937' : '#ffffff',
      secondary: mode === 'light' ? '#5f6368' : '#b3b3b3',
    },
    divider: mode === 'light' ? '#e5e7eb' : '#333333',
    action: {
      hover: mode === 'light' ? 'rgba(0, 0, 0, 0.04)' : 'rgba(255, 255, 255, 0.08)',
    },
    // Custom colors for message bubbles
    grey: {
      50: mode === 'light' ? '#f9fafb' : '#18181b',
      100: mode === 'light' ? '#f3f4f6' : '#27272a',
      200: mode === 'light' ? '#e5e7eb' : '#3f3f46',
    },
  },
  typography: {
    fontFamily: 'ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Helvetica Neue, Arial, "Apple Color Emoji", "Segoe UI Emoji"',
    h6: {
      fontWeight: 600,
      fontSize: '1.125rem',
    },
    body1: {
      fontSize: '0.9375rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          fontWeight: 600,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            backgroundColor: mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: mode === 'dark' ? '#1e1e1e' : '#ffffff',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: mode === 'dark' ? '#1e1e1e' : '#ffffff',
          color: mode === 'dark' ? '#ffffff' : '#1f2937',
        },
      },
    },
  },
});

// Default light theme for backward compatibility
export const theme = createAppTheme('light');