"use client";

import { useCallback, useRef, useState } from "react";
import { AgentUIState, ChatMessage, GraphNode, StreamEvent } from "./types";

function parseSSEChunk(buffer: string) {
  const rawEvents = buffer.split("\n\n");
  const rest = rawEvents.pop() ?? "";

  const events: StreamEvent[] = [];

  for (const raw of rawEvents) {
    const dataLines = raw
      .split("\n")
      .filter((line) => line.startsWith("data: "))
      .map((line) => line.slice(6));

    if (!dataLines.length) continue;

    try {
      events.push(JSON.parse(dataLines.join("\n")));
    } catch {
      console.warn("Failed to parse SSE event", dataLines.join("\n"));
    }
  }

  return { events, rest };
}

function createThreadId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `thread-${Date.now()}`;
}

export function useAgentStream() {
  const [state, setState] = useState<AgentUIState>({
    messages: [],
    graphNodes: [],
    isRunning: false,
    threadId: createThreadId(),
  });

  const thinkingBuffer = useRef("");
  const graphNodesRef = useRef<GraphNode[]>([]);
  const assistantMessageIdRef = useRef<string | null>(null);

  const sendMessage = useCallback(
    async (text: string, location = "Kolkata") => {
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
        kind: "text",
      };

      thinkingBuffer.current = "";
      graphNodesRef.current = [];
      assistantMessageIdRef.current = null;

      setState((prev) => ({
        ...prev,
        isRunning: true,
        messages: [...prev.messages, userMessage],
        graphNodes: [],
      }));

      try {
        const res = await fetch("/api/agent", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: text,
            location,
            thread_id: state.threadId,
          }),
        });

        if (!res.ok || !res.body) {
          throw new Error("Stream connection failed");
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const parsed = parseSSEChunk(buffer);
          buffer = parsed.rest;

          for (const event of parsed.events) {
            handleEvent(event);
          }
        }
      } catch (error) {
        setState((prev) => ({
          ...prev,
          isRunning: false,
          messages: [
            ...prev.messages,
            {
              id: crypto.randomUUID(),
              role: "system",
              content: error instanceof Error ? error.message : "Unknown error",
              kind: "error",
            },
          ],
        }));
      }

      function handleEvent(event: StreamEvent) {
        switch (event.type) {
          case "RUN_STARTED":
            break;

          case "TRACE_START":
            thinkingBuffer.current = "";
            break;

          case "MEMORY_LOOKUP":
            thinkingBuffer.current += `Memory: ${String(event.summary ?? "")}\n`;
            break;

          case "PLANNER_STEP":
            thinkingBuffer.current += String(event.delta ?? "");
            break;

          case "ROUTE_DECISION":
            thinkingBuffer.current += `Route: ${String(event.delta ?? "")}\n`;
            break;

          case "SYNTHESIS_START":
            thinkingBuffer.current += String(event.delta ?? "");
            break;

          case "TEXT_MESSAGE_START": {
            const id = String(event.message_id);
            assistantMessageIdRef.current = id;

            setState((prev) => ({
              ...prev,
              messages: [
                ...prev.messages,
                {
                  id,
                  role: "assistant",
                  content: "",
                  kind: "text",
                  isStreaming: true,
                },
              ],
            }));
            break;
          }

          case "TEXT_MESSAGE_CHUNK": {
            const id = String(event.message_id);
            const delta = String(event.delta ?? "");

            setState((prev) => ({
              ...prev,
              messages: prev.messages.map((m) =>
                m.id === id ? { ...m, content: m.content + delta } : m,
              ),
            }));
            break;
          }

          case "TOOL_CALL": {
            const toolName = String(event.tool_name ?? "unknown_tool");
            const nodeId = String(event.node_id ?? crypto.randomUUID());

            const toolMessage: ChatMessage = {
              id: crypto.randomUUID(),
              role: "assistant",
              content: `Calling tool: ${toolName}`,
              kind: "tool",
            };

            graphNodesRef.current = [
              ...graphNodesRef.current,
              {
                id: nodeId,
                label: toolName,
                status: "running",
              },
            ];

            setState((prev) => ({
              ...prev,
              messages: [...prev.messages, toolMessage],
              graphNodes: [...graphNodesRef.current],
            }));
            break;
          }

          case "TOOL_DONE": {
            const toolName = String(event.tool_name ?? "unknown_tool");

            let updatedOne = false;
            graphNodesRef.current = graphNodesRef.current.map((node) => {
              if (!updatedOne && node.label === toolName && node.status === "running") {
                updatedOne = true;
                return { ...node, status: "done" };
              }
              return node;
            });

            setState((prev) => ({
              ...prev,
              graphNodes: [...graphNodesRef.current],
            }));
            break;
          }

          case "TEXT_MESSAGE_END": {
            const id = String(event.message_id);

            setState((prev) => ({
              ...prev,
              isRunning: false,
              messages: prev.messages.map((m) =>
                m.id === id ? { ...m, isStreaming: false } : m,
              ),
            }));
            break;
          }

          case "TRACE_END":
            break;

          case "RUN_FINISHED":
            setState((prev) => ({
              ...prev,
              isRunning: false,
            }));
            break;

          case "RUN_ERROR":
            setState((prev) => ({
              ...prev,
              isRunning: false,
              messages: [
                ...prev.messages,
                {
                  id: crypto.randomUUID(),
                  role: "system",
                  content: String(event.error ?? "Unknown error"),
                  kind: "error",
                },
              ],
            }));
            break;
        }
      }
    },
    [state.threadId],
  );

  const resetThread = useCallback(() => {
    thinkingBuffer.current = "";
    graphNodesRef.current = [];
    assistantMessageIdRef.current = null;

    setState({
      messages: [],
      graphNodes: [],
      isRunning: false,
      threadId: createThreadId(),
    });
  }, []);

  return {
    state,
    sendMessage,
    resetThread,
    getThinkingTrace: () => thinkingBuffer.current,
  };
}