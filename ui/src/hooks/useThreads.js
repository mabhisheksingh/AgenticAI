import React, { useState, useEffect } from 'react';
import { api } from '../api/controller';

const useThreads = (user_id) => {
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadThreads = async () => {
    if (!user_id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const res = await api.listThreads({ user_id });
      const items = Array.isArray(res?.data) ? res.data : res;
      setThreads(items || []);
    } catch (err) {
      setError(err.message || 'Failed to load threads');
      setThreads([]);
    } finally {
      setLoading(false);
    }
  };

  const deleteThread = async (thread_id) => {
    try {
      await api.deleteThread({ user_id, thread_id });
      await loadThreads(); // Refresh the list
      return true;
    } catch (err) {
      setError(err.message || 'Failed to delete thread');
      return false;
    }
  };

  const renameThread = async (thread, newLabel) => {
    try {
      const thread_id = thread.thread_id || thread.id;
      await api.renameThreadLabel({
        user_id,
        thread_id,
        label: newLabel,
      });
      await loadThreads(); // Refresh the list
      return true;
    } catch (err) {
      setError(err.message || 'Failed to rename thread');
      return false;
    }
  };

  const loadThreadDetails = async (thread_id) => {
    try {
      const threadDetails = await api.getThreadDetails({ user_id, thread_id });
      return threadDetails?.data?.messages || [];
    } catch (err) {
      setError(err.message || 'Failed to load thread details');
      return [];
    }
  };

  useEffect(() => {
    if (user_id) {
      // Clear threads first when user changes
      setThreads([]);
      setError(null);
      loadThreads();
    } else {
      // Clear threads if no user selected
      setThreads([]);
      setError(null);
    }
  }, [user_id]);

  return {
    threads,
    loading,
    error,
    loadThreads,
    deleteThread,
    renameThread,
    loadThreadDetails,
  };
};

export default useThreads;