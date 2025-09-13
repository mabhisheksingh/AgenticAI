# API Usage

## Base URLs
- Backend: `http://localhost:8080`
- Swagger: `http://localhost:8080/docs`

## Endpoints

### POST /v1/agent/chat
Streaming chat endpoint (SSE).

Headers:
- `user-id: <string>` (required)

Body (JSON):
```json
{
  "message": "Who is the PM of India and what is 3*99.8?",
  "thread_label": "default",
  "thread_id": null
}
```

cURL example:
```bash
curl -N \
  -X POST http://localhost:8080/v1/agent/chat \
  -H 'Content-Type: application/json' \
  -H 'user-id: test-user-123' \
  -d '{
    "message": "Who is the PM of India and what is 3*99.8?",
    "thread_label": "default"
  }'
```

Response: Server-Sent Events stream containing tokens and metadata.

Possible event types:
- `token`: model text chunk
- `tool_call`: informational event when tools node executes
- `error`: error surfaced during streaming
- `[DONE]`: end of stream marker

### POST /v1/user/threads
Create or list threads (see router implementations).

## Errors
- 400/422: Validation issues
- 500: DI or runtime errors (check server logs)

## Notes
- `thread_label` is mandatory for new threads.
- You can resume a thread by passing a valid `thread_id`.
