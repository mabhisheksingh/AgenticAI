// API endpoint paths (relative to API_BASE_URL)
export const Endpoints = {
  chat: '/v1/agent/chat',
  threads: '/v1/agent/threads',
  deleteThread: (threadId) => `/v1/agent/threads/${threadId}`,
  renameThreadLabel: (threadId, label) => `/v1/agent/rename-thread-label?threadId=${encodeURIComponent(threadId)}&label=${encodeURIComponent(label)}`,
  threadDetails: (threadId) => `/v1/agent/thread/${threadId}`
}
