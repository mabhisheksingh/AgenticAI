import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  TextField,
  Autocomplete,
  MenuItem,
  Typography,
  CircularProgress,
  Avatar,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
} from '@mui/material';
import { Add as AddIcon, Person as PersonIcon, Delete as DeleteIcon } from '@mui/icons-material';
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
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

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

  const handleDeleteUser = async () => {
    if (!userToDelete) return;
    
    setDeleteLoading(true);
    setDeleteError(null);
    
    try {
      await api.deleteUser({ user_id: userToDelete });
      // Remove deleted user from the list
      setUsers(prev => prev.filter(userId => userId !== userToDelete));
      // If the deleted user was the currently selected user, clear selection
      if (value === userToDelete) {
        onChange('');
        onUserSelect?.('');
      }
      setDeleteDialogOpen(false);
    } catch (err) {
      setDeleteError(err.message || 'Failed to delete user');
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <>
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
                    {params.InputProps.endAdornment}
                    {value && (
                      <Tooltip title="Delete User">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            setUserToDelete(value);
                            setDeleteDialogOpen(true);
                          }}
                          sx={{ p: 0.5 }}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </>
                ),
              }}
            />
          )}
          renderOption={(props, option) => (
            <Box component="li" {...props}>
              <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                <Typography variant="body2">{option.label}</Typography>
                {!option.isCreateNew && (
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      setUserToDelete(option.id);
                      setDeleteDialogOpen(true);
                    }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                )}
              </Box>
            </Box>
          )}
          noOptionsText={
            searchTerm ? (
              <Typography variant="body2" color="text.secondary">
                No users found. Press Enter to create "{searchTerm}".
              </Typography>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No users available.
              </Typography>
            )
          }
        />
      </Box>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm User Deletion</DialogTitle>
        <DialogContent>
          {deleteError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {deleteError}
            </Alert>
          )}
          <Typography>
            Are you sure you want to delete user <strong>{userToDelete}</strong>? This action will remove all threads and data associated with this user.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={deleteLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteUser} 
            color="error" 
            variant="contained"
            disabled={deleteLoading}
          >
            {deleteLoading ? <CircularProgress size={24} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default UserSelector;