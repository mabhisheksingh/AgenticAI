/**
 * Utility functions for thread management
 */

/**
 * Generate a thread label from a chat message
 * Takes the first 10 words maximum and adds ellipsis if longer
 * @param {string} message - The chat message
 * @returns {string} - The generated thread label (max 10 words)
 */
export const generateThreadLabel = (message) => {
  if (!message || typeof message !== 'string') {
    return 'New Thread';
  }

  const cleanMessage = message.trim();
  if (!cleanMessage) {
    return 'New Thread';
  }

  const words = cleanMessage.split(/\\s+/);
  // Always limit to maximum 10 words
  const maxWords = 10;
  const limitedWords = words.slice(0, maxWords);
  const label = limitedWords.join(' ');
  
  // Add ellipsis if original message had more than 10 words
  return words.length > maxWords ? `${label}...` : label;
};

/**
 * Validate and enforce 10-word limit on thread labels
 * @param {string} label - The thread label to validate
 * @returns {string} - The validated thread label (max 10 words)
 */
export const validateThreadLabel = (label) => {
  if (!label || typeof label !== 'string') {
    return 'New Thread';
  }

  const cleanLabel = label.trim();
  if (!cleanLabel) {
    return 'New Thread';
  }

  const words = cleanLabel.split(/\\s+/);
  const maxWords = 10;
  
  if (words.length <= maxWords) {
    return cleanLabel;
  }
  
  // Truncate to 10 words and add ellipsis
  const limitedWords = words.slice(0, maxWords);
  return `${limitedWords.join(' ')}...`;
};

/**
 * Truncate thread title for display
 * @param {string} title - The thread title
 * @param {number} maxLength - Maximum character length (default: 50)
 * @returns {string} - The truncated title
 */
export const truncateThreadTitle = (title, maxLength = 50) => {
  if (!title || typeof title !== 'string') {
    return 'Untitled Thread';
  }

  if (title.length <= maxLength) {
    return title;
  }

  return `${title.slice(0, maxLength)}...`;
};

/**
 * Format thread display name - show thread label or thread ID as fallback
 * @param {Object} thread - The thread object
 * @returns {string} - The thread label or thread ID
 */
export const getThreadDisplayName = (thread) => {
  if (!thread) {
    return 'Unknown Thread';
  }

  const label = thread.thread_label || thread.title;
  const threadId = thread.thread_id || thread.id;
  
  // Show thread label if available
  if (label && label.trim()) {
    return truncateThreadTitle(label);
  }

  // Fallback to thread ID if no label exists
  if (threadId) {
    const shortId = threadId.toString();
    return truncateThreadTitle(shortId, 30); // Show more of the thread ID
  }

  return 'Untitled Thread';
};