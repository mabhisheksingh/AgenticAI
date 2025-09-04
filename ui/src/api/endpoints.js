// API endpoint paths (relative to API_BASE_URL)
export const Endpoints = {
  chat: '/v1/agent/chat',
  threads: '/v1/user/threads',
  deleteThread: (threadId) => `/v1/user/threads/${threadId}`,
  renameThreadLabel: (threadId, label) => `/v1/user/rename-thread-label?threadId=${encodeURIComponent(threadId)}&label=${encodeURIComponent(label)}`,
  threadDetails: (threadId) => `/v1/user/thread/${threadId}`,
  getAllUsers: '/v1/user/get-all'
}
