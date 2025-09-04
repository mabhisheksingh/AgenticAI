import React, { useState, useEffect } from 'react';
import { api } from '../api/controller';

const useThreads = (userId) => {
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadThreads = async () => {
    if (!userId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const res = await api.listThreads({ userId });
      const items = Array.isArray(res?.data) ? res.data : res;
      setThreads(items || []);
    } catch (err) {
      setError(err.message || 'Failed to load threads');
      setThreads([]);
    } finally {
      setLoading(false);
    }
  };

  const deleteThread = async (threadId) => {
    try {
      await api.deleteThread({ userId, threadId });
      await loadThreads(); // Refresh the list
      return true;
    } catch (err) {
      setError(err.message || 'Failed to delete thread');
      return false;
    }
  };

  const renameThread = async (thread, newLabel) => {
    try {
      const threadId = thread.thread_id || thread.id;
      await api.renameThreadLabel({
        userId,
        threadId,
        label: newLabel,
      });
      await loadThreads(); // Refresh the list
      return true;
    } catch (err) {
      setError(err.message || 'Failed to rename thread');
      return false;
    }
  };

  const loadThreadDetails = async (threadId) => {
    try {
      const threadDetails = await api.getThreadDetails({ userId, threadId });
      return threadDetails?.data?.messages || [];
    } catch (err) {
      setError(err.message || 'Failed to load thread details');
      return [];
    }
  };

  useEffect(() => {
    if (userId) {
      loadThreads();
    }
  }, [userId]);

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