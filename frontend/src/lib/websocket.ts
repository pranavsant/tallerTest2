/**
 * Typed WebSocket client for realtime session communication.
 *
 * Mirrors the backend protocol in `src/interfaces/api/websocket_handler.py`:
 *
 *   Client → Server:  { type: "message",       content, user_id }
 *   Client → Server:  { type: "audio_request", text, agent_id }
 *   Client → Server:  { type: "ping" }
 *   Server → Client:  { event: "connected" | "message.sent" | "audio.chunk"
 *                              | "error" | "pong", data: { ... } }
 *
 * The endpoint is `${NEXT_PUBLIC_API_BASE_URL}/ws/session/{session_id}` with the
 * scheme switched to ws/wss.
 */

import { NEXT_PUBLIC_API_BASE_URL } from "@/env";

/** Server → client event names. */
export type WsServerEvent = "connected" | "message.sent" | "audio.chunk" | "error" | "pong";

/** Payload of a `message.sent` event. */
export interface WsMessageData {
  message_id: string;
  role: string;
  content: string;
  audio_url: string | null;
}

/** Payload of an `audio.chunk` event. */
export interface WsAudioChunkData {
  audio_b64: string;
  voice_id: string;
  model_id: string;
}

type WsHandler<T> = (data: T) => void;

/** Derive the ws(s):// session URL from the configured API base URL. */
function sessionUrl(sessionId: string): string {
  const base = NEXT_PUBLIC_API_BASE_URL.replace(/^http/, "ws").replace(/\/+$/, "");
  return `${base}/ws/session/${sessionId}`;
}

export class SessionWebSocket {
  private socket: WebSocket | null = null;
  private readonly handlers = new Map<string, Set<WsHandler<unknown>>>();

  constructor(private readonly sessionId: string) {}

  /** Open the connection. Safe to call once per instance. */
  connect(): void {
    if (this.socket) return;
    const ws = new WebSocket(sessionUrl(this.sessionId));
    this.socket = ws;

    ws.onmessage = (event: MessageEvent<string>) => {
      let parsed: { event?: string; data?: unknown };
      try {
        parsed = JSON.parse(event.data);
      } catch {
        return;
      }
      if (!parsed.event) return;
      const set = this.handlers.get(parsed.event);
      if (set) for (const handler of set) handler(parsed.data);
    };
  }

  /** Subscribe to a server event. Returns an unsubscribe function. */
  on<T = unknown>(event: WsServerEvent | string, handler: WsHandler<T>): () => void {
    let set = this.handlers.get(event);
    if (!set) {
      set = new Set();
      this.handlers.set(event, set);
    }
    set.add(handler as WsHandler<unknown>);
    return () => set?.delete(handler as WsHandler<unknown>);
  }

  /** Send a text message into the session. */
  sendMessage(userId: string, content: string): void {
    this.send({ type: "message", user_id: userId, content });
  }

  /** Request synthesized audio for `text` from a given agent. */
  requestAudio(agentId: string, text: string): void {
    this.send({ type: "audio_request", agent_id: agentId, text });
  }

  /** Send a keepalive ping. */
  ping(): void {
    this.send({ type: "ping" });
  }

  private send(payload: Record<string, unknown>): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload));
    }
  }

  /** Close the connection and drop all handlers. */
  disconnect(): void {
    this.socket?.close();
    this.socket = null;
    this.handlers.clear();
  }
}
