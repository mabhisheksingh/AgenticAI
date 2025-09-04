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
  // Streaming chat over SSE (POST)
  // Usage: api.chatStream({ userId, threadId, message, threadLabel, onEvent, onDone, onError })
  chatStream: async ({ userId, threadId, message, threadLabel, onEvent, onDone, onError, signal }) => {
    const url = http.buildUrl(Endpoints.chat)
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      [HEADER_USER_ID]: userId,
    }
    
    // Ensure threadLabel is always provided - it's now mandatory
    if (!threadLabel) {
      throw new Error('thread_label is required for all chat requests')
    }
    
    // Build request body with message, optional thread_id, and mandatory thread_label
    const requestBody = { message, thread_label: threadLabel }
    if (threadId) {
      requestBody.thread_id = threadId
    }

    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(requestBody),
      signal,
    })

    if (!res.ok || !res.body) {
      const text = await res.text().catch(() => '')
      const err = new Error(text || `Request failed with ${res.status}`)
      err.status = res.status
      throw err
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        let idx
        while ((idx = buffer.indexOf('\n')) !== -1) {
          const line = buffer.slice(0, idx)
          buffer = buffer.slice(idx + 1)
          if (!line) continue
          if (line.startsWith('data: ')) {
            const payload = line.slice(6).trim()
            if (payload === '[DONE]') {
              onDone?.()
              return
            }
            onEvent?.(payload)
          }
        }
      }
      onDone?.()
    } catch (e) {
      if (e?.name === 'AbortError') return
      if (onError) onError(e)
      else throw e
    } finally {
      try { reader.releaseLock() } catch {}
    }
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
  getThreadDetails: async ({ userId, threadId }) => {
    const headers = { 
      [HEADER_USER_ID]: userId,
      'accept': 'application/json'
    }
    const res = await http.get(Endpoints.threadDetails(threadId), { headers })
    return res.data
  },
}
