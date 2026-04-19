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

export function useAgentStream() {
  const [state, setState] = useState<AgentUIState>({
    messages: [],
    graphNodes: [],
    isRunning: false,
  });

  const assistantMessageId = useRef<string | null>(null);
  const thinkingBuffer = useRef("");
  const graphNodesRef = useRef<GraphNode[]>([]);

  const sendMessage = useCallback(async (text: string, location = "Kolkata") => {
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      kind: "text",
    };

    thinkingBuffer.current = "";
    graphNodesRef.current = [];

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

        case "THINKING_START":
          thinkingBuffer.current = "";
          break;

        case "THINKING_DELTA":
          thinkingBuffer.current += String(event.delta ?? "");
          break;

        case "TEXT_MESSAGE_START": {
          const id = String(event.message_id);
          assistantMessageId.current = id;

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
              m.id === id ? { ...m, content: m.content + delta } : m
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

          graphNodesRef.current = graphNodesRef.current.map((node) =>
            node.label === toolName && node.status === "running"
              ? { ...node, status: "done" }
              : node
          );

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
              m.id === id ? { ...m, isStreaming: false } : m
            ),
          }));
          break;
        }

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
  }, []);

  return {
    state,
    sendMessage,
    getThinkingTrace: () => thinkingBuffer.current,
  };
}