import { http } from './http'
import { Endpoints } from './endpoints'
import { HEADER_THREAD_ID, HEADER_USER_ID } from './config'

// Main controller: all API calls defined here
export const api = {
  chat: async ({ userId, threadId, message }) => {
    const headers = { [HEADER_USER_ID]: userId }
    if (threadId) headers[HEADER_THREAD_ID] = threadId
    const res = await http.post(Endpoints.chat, { message }, { headers })
    return res.data
  },
  listThreads: async ({ userId }) => {
    const headers = { [HEADER_USER_ID]: userId }
    const res = await http.get(Endpoints.threads, { headers })
    return res.data
  },
  deleteThread: async ({ userId, threadId }) => {
    const headers = { [HEADER_USER_ID]: userId }
    const res = await http.delete(Endpoints.deleteThread(threadId), { headers })
    return res.data
  },
  renameThreadLabel: async ({ userId, threadId, label }) => {
    const headers = { 
      [HEADER_USER_ID]: userId,
      'accept': 'application/json'
    }
    const res = await http.patch(
      Endpoints.renameThreadLabel(threadId, label),
      null,
      { headers }
    )
    return res.data
  },
}
