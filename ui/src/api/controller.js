import { http } from './http'
import { Endpoints } from './endpoints'
import { HEADER_THREAD_ID, HEADER_USER_ID } from './config'

// Main controller: all API calls defined here
export const api = {
  chat: async ({ user_id, thread_id, message }) => {
    const headers = { [HEADER_USER_ID]: user_id }
    if (thread_id) headers[HEADER_THREAD_ID] = thread_id
    const res = await http.post(Endpoints.chat, { message }, { headers })
    return res.data
  },
  // Streaming chat over SSE (POST)
  // Usage: api.chatStream({ user_id, thread_id, message, threadLabel, onEvent, onDone, onError })
  chatStream: async ({ user_id, thread_id, message, threadLabel, onEvent, onDone, onError, signal }) => {
    const url = http.buildUrl(Endpoints.chat)
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      [HEADER_USER_ID]: user_id,
    }
    
    // Ensure threadLabel is always provided - it's now mandatory
    if (!threadLabel) {
      throw new Error('thread_label is required for all chat requests')
    }
    
    // Ensure user_id is provided
    if (!user_id) {
      throw new Error('user_id is required for all chat requests')
    }
    
    // Build request body with message, optional thread_id, and mandatory thread_label
    const requestBody = { message, thread_label: threadLabel }
    // Only add thread_id if it's a valid non-null value
    if (thread_id && thread_id !== 'null' && thread_id !== 'undefined' && thread_id !== 'None') {
      requestBody.thread_id = thread_id
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
      // Log detailed error information for debugging
      console.error('Chat API Error Details:', {
        status: res.status,
        statusText: res.statusText,
        url: url,
        headers: headers,
        requestBody: requestBody,
        responseText: text
      })
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
  listThreads: async ({ user_id }) => {
    const headers = { [HEADER_USER_ID]: user_id }
    const res = await http.get(Endpoints.threads, { headers })
    return res.data
  },
  deleteThread: async ({ user_id, thread_id }) => {
    const headers = { [HEADER_USER_ID]: user_id }
    const res = await http.delete(Endpoints.deleteThread(thread_id), { headers })
    return res.data
  },
  renameThreadLabel: async ({ user_id, thread_id, label }) => {
    const headers = { 
      [HEADER_USER_ID]: user_id,
      'accept': 'application/json'
    }
    const res = await http.patch(
      Endpoints.renameThreadLabel(thread_id, label),
      null,
      { headers }
    )
    return res.data
  },
  getThreadDetails: async ({ user_id, thread_id }) => {
    const headers = { 
      [HEADER_USER_ID]: user_id,
      'accept': 'application/json'
    }
    const res = await http.get(Endpoints.threadDetails(thread_id), { headers })
    return res.data
  },
  
  // Get all users
  getAllUsers: async () => {
    const res = await http.get(Endpoints.getAllUsers)
    return res.data
  },
}
