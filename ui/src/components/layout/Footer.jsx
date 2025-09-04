import React from 'react';
import { Box, Typography, Link, alpha } from '@mui/material';

const Footer = () => {
  return (
    <Box
      component="footer"
      sx={{
        textAlign: 'center',
        py: 1,
        px: 2,
        borderTop: 1,
        borderColor: 'divider',
        backgroundColor: (theme) => alpha(theme.palette.background.paper, 0.8),
        backdropFilter: 'blur(8px)',
      }}
    >
      <Typography variant="caption" color="text.secondary">
        FastAPI at{' '}
        <Link
          href="http://localhost:8000"
          target="_blank"
          rel="noopener"
          sx={{ color: 'primary.main', textDecoration: 'none' }}
        >
          http://localhost:8000
        </Link>
        {' '} | UI via Vite
      </Typography>
    </Box>
  );
};

export default Footer;