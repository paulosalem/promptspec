## Real-Time Communication Module

### WebSocket Protocol
- Endpoint: `ws(s)://host/ws` with JWT token in the first message or query param.
- Message format: JSON with `{"type": "...", "payload": {...}, "id": "uuid"}`.
- Server sends `{"type": "ack", "id": "..."}` for every client message.
- Heartbeat: server sends `{"type": "ping"}` every 30 seconds; client MUST
  respond with `{"type": "pong"}` within 10 seconds or connection is closed.

### Presence
- Server tracks connected users per channel/room.
- On join/leave, broadcast `{"type": "presence", "payload": {"user_id": "...", "status": "online|offline"}}`.
- Client can request current presence list via `{"type": "presence_list", "payload": {"channel": "..."}}`.

### Message Types
- `chat`: text message with `sender_id`, `content`, `timestamp`.
- `state_update`: game/app state delta with `entity_id`, `changes` (JSON patch).
- `error`: server error with `code` and `message`.

### Reconnection
- Client MUST implement exponential backoff: 1s, 2s, 4s, 8s, max 30s.
- On reconnect, client sends `{"type": "resume", "payload": {"last_event_id": "..."}}`.
- Server replays missed events since `last_event_id` (up to 1000 events or 5 minutes).
