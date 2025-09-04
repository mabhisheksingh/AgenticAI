import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  TextField,
  Autocomplete,
  MenuItem,
  Typography,
  CircularProgress,
  Avatar,
} from '@mui/material';
import { Add as AddIcon, Person as PersonIcon } from '@mui/icons-material';
import { api } from '../../api/controller';

const UserSelector = ({ 
  value, 
  onChange, 
  onUserSelect,
  loading = false, 
  error = null 
}) => {
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [open, setOpen] = useState(false);

  // Load all users when component mounts
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoadingUsers(true);
    try {
      const response = await api.getAllUsers();
      // Expecting response.data to be an array of user IDs like ["123", "abc", ...]
      const userList = Array.isArray(response?.data) ? response.data : [];
      setUsers(userList);
    } catch (err) {
      console.error('Failed to load users:', err);
      setUsers([]);
    } finally {
      setLoadingUsers(false);
    }
  };

  // Create options array with "Create New User" as first option
  const options = [
    { id: '__create_new__', label: 'Create New User', isCreateNew: true },
    ...users.map(userId => ({ id: userId, label: userId, isCreateNew: false }))
  ];

  const handleChange = (event, newValue) => {
    if (newValue?.isCreateNew) {
      // Handle "Create New User" selection
      const newUserId = prompt('Enter new user ID:');
      if (newUserId && newUserId.trim()) {
        const trimmedId = newUserId.trim();
        onChange(trimmedId);
        onUserSelect?.(trimmedId);
        // Add to users list if not already present
        if (!users.includes(trimmedId)) {
          setUsers(prev => [trimmedId, ...prev]);
        }
      }
    } else if (newValue) {
      onChange(newValue.id);
      onUserSelect?.(newValue.id);
    } else {
      onChange('');
      onUserSelect?.('');
    }
  };

  const handleInputChange = (event, newInputValue) => {
    // Just track the search term for noOptionsText display
    setSearchTerm(newInputValue);
  };

  // Find the selected option
  const selectedOption = options.find(option => option.id === value) || null;

  return (
    <Box sx={{ minWidth: 200, maxWidth: 300 }}>
      <Autocomplete
        options={options}
        value={selectedOption}
        onChange={handleChange}
        onInputChange={handleInputChange}
        // Let Autocomplete manage its own inputValue for better search experience
        open={open}
        onOpen={() => setOpen(true)}
        onClose={() => setOpen(false)}
        loading={loadingUsers}
        getOptionLabel={(option) => option?.label || ''}
        isOptionEqualToValue={(option, value) => option?.id === value?.id}
        disablePortal={false}
        slotProps={{
          popper: {
            placement: 'bottom-start',
            modifiers: [
              {
                name: 'offset',
                options: {
                  offset: [0, 8],
                },
              },
            ],
          },
        }}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Select User"
            variant="outlined"
            size="small"
            error={!!error}
            helperText={error}
            InputProps={{
              ...params.InputProps,
              startAdornment: (
                <Avatar sx={{ width: 24, height: 24, mr: 1, bgcolor: 'primary.main' }}>
                  <PersonIcon sx={{ fontSize: 14 }} />
                </Avatar>
              ),
              endAdornment: (
                <>
                  {loadingUsers ? <CircularProgress color="inherit" size={20} /> : null}
                  {params.InputProps.endAdornment}
                </>
              ),
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                paddingLeft: 1,
              },
            }}
          />
        )}
        renderOption={(props, option) => (
          <MenuItem {...props} key={option.id}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
              {option.isCreateNew ? (
                <>
                  <Avatar sx={{ width: 24, height: 24, bgcolor: 'success.main' }}>
                    <AddIcon sx={{ fontSize: 14 }} />
                  </Avatar>
                  <Typography variant="body2" color="success.main" fontWeight="medium">
                    {option.label}
                  </Typography>
                </>
              ) : (
                <>
                  <Avatar sx={{ width: 24, height: 24, bgcolor: 'grey.400' }}>
                    <PersonIcon sx={{ fontSize: 14 }} />
                  </Avatar>
                  <Typography variant="body2">
                    {option.label}
                  </Typography>
                </>
              )}
            </Box>
          </MenuItem>
        )}
        ListboxProps={{
          style: {
            maxHeight: 300, // Scrollable dropdown
          }
        }}
        sx={{
          '& .MuiAutocomplete-listbox': {
            maxHeight: 300,
            overflowY: 'auto',
          },
          '& .MuiAutocomplete-popper': {
            '& .MuiPaper-root': {
              marginTop: '8px', // Add some spacing from input
            }
          }
        }}
        noOptionsText={
          searchTerm ? 
            `No users found for "${searchTerm}"` : 
            'No users available'
        }
        disabled={loading}
      />
    </Box>
  );
};

export default UserSelector;