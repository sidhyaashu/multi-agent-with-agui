"use client";

import { useRef, useState } from "react";
import ChatMessage from "@/components/ChatMessage";
import { useAgentStream } from "@/lib/useAgentStream";

export default function Home() {
  const [input, setInput] = useState("");
  const { state, sendMessage, resetThread, getThinkingTrace } = useAgentStream();
  const endRef = useRef<HTMLDivElement>(null);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || state.isRunning) return;

    setInput("");
    await sendMessage(text);

    setTimeout(() => {
      endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 50);
  };

  return (
    <div className="min-h-screen bg-white text-black">
      <div className="mx-auto flex min-h-screen max-w-4xl flex-col">
        <header className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-lg font-semibold">ReAct Multi-Agent Assistant</h1>
              <p className="text-sm text-gray-500">
                FastAPI + PydanticAI + Next.js
              </p>
              <p className="mt-1 text-xs text-gray-400">
                Thread: {state.threadId}
              </p>
            </div>

            <button
              onClick={resetThread}
              disabled={state.isRunning}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 transition hover:bg-gray-50 disabled:opacity-40"
            >
              New chat
            </button>
          </div>
        </header>

        <main className="flex-1 px-4 py-6 sm:px-6">
          {state.messages.length === 0 ? (
            <div className="mt-24 text-center text-gray-400">
              <p className="text-lg">Ask anything.</p>
              <p className="mt-2 text-sm">
                Try: “Weather in Tokyo”, “345 * 99 + 120 / 6”, or
                “Compare weather in Tokyo and Kolkata and latest AI news”
              </p>
            </div>
          ) : (
            <div className="mx-auto flex max-w-3xl flex-col gap-4">
              {state.messages.map((message, index) => {
                const isLastAssistantText =
                  message.role === "assistant" &&
                  message.kind === "text" &&
                  index === state.messages.length - 1;

                return (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    graphNodes={isLastAssistantText ? state.graphNodes : undefined}
                    thinkingTrace={isLastAssistantText ? getThinkingTrace() : undefined}
                  />
                );
              })}
              <div ref={endRef} />
            </div>
          )}
        </main>

        <footer className="border-t border-gray-200 p-4">
          <div className="mx-auto flex max-w-3xl gap-2">
            <input
              className="flex-1 rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ask something..."
              value={input}
              disabled={state.isRunning}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
            />
            <button
              onClick={handleSend}
              disabled={state.isRunning || !input.trim()}
              className="rounded-xl bg-blue-600 px-5 py-3 text-sm text-white transition hover:bg-blue-700 disabled:opacity-40"
            >
              {state.isRunning ? "..." : "Send"}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}