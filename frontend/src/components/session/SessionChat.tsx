"use client";

import { useEffect, useRef, useState } from "react";
import {
  SessionWebSocket,
  type WsMessageData,
} from "@/lib/websocket";
import { cn } from "@/lib/utils";

interface ChatMessage {
  id: string;
  role: "user" | "agent" | "system";
  content: string;
  audioUrl: string | null;
  timestamp: Date;
}

interface SessionChatProps {
  sessionId: string;
  userId: string;
}

export function SessionChat({ sessionId, userId }: SessionChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<SessionWebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ws = new SessionWebSocket(sessionId);
    wsRef.current = ws;

    ws.on<{ session_id: string }>("connected", () => {
      setConnected(true);
    });

    ws.on<WsMessageData>("message.sent", (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: data.message_id,
          role: data.role as "user" | "agent",
          content: data.content,
          audioUrl: data.audio_url,
          timestamp: new Date(),
        },
      ]);
    });

    ws.on<{ detail: string }>("error", (data) => {
      setError(data.detail);
    });

    ws.connect();

    return () => {
      ws.disconnect();
    };
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || !wsRef.current) return;
    // Optimistically add user message
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: input.trim(),
        audioUrl: null,
        timestamp: new Date(),
      },
    ]);
    wsRef.current.sendMessage(userId, input.trim());
    setInput("");
  };

  return (
    <div className="flex h-full flex-col">
      {/* Connection status */}
      <div className="flex items-center gap-2 border-b border-gray-200 px-4 py-3 dark:border-gray-800">
        <div
          className={cn(
            "h-2 w-2 rounded-full",
            connected ? "bg-green-500" : "bg-gray-400",
          )}
        />
        <span className="text-xs text-gray-500">
          {connected ? "Connected" : "Connecting…"}
        </span>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 px-4 py-2 text-xs text-red-600 dark:bg-red-900/20 dark:text-red-400">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex",
              msg.role === "user" ? "justify-end" : "justify-start",
            )}
          >
            <div
              className={cn(
                "max-w-xs rounded-2xl px-4 py-2.5 text-sm lg:max-w-md",
                msg.role === "user"
                  ? "bg-brand-600 text-white"
                  : "bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white",
              )}
            >
              <p>{msg.content}</p>
              {msg.audioUrl && (
                <audio controls src={msg.audioUrl} className="mt-2 w-full" />
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 dark:border-gray-800">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type a message…"
            className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !connected}
            className="rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
