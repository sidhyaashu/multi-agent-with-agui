export type StreamEventType =
  | "RUN_STARTED"
  | "TRACE_START"
  | "MEMORY_LOOKUP"
  | "PLANNER_STEP"
  | "ROUTE_DECISION"
  | "SYNTHESIS_START"
  | "TOOL_CALL"
  | "TOOL_DONE"
  | "TEXT_MESSAGE_START"
  | "TEXT_MESSAGE_CHUNK"
  | "TEXT_MESSAGE_END"
  | "TRACE_END"
  | "RUN_FINISHED"
  | "RUN_ERROR";

export interface StreamEvent {
  type: StreamEventType;
  [key: string]: unknown;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  kind?: "text" | "tool" | "error";
  isStreaming?: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  status: "running" | "done";
}

export interface AgentUIState {
  messages: ChatMessage[];
  graphNodes: GraphNode[];
  isRunning: boolean;
  threadId: string;
}