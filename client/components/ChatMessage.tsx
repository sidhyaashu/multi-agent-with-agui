// "use client";

// import CollapsibleTrace from "./CollapsibleTrace";
// import ToolGraph from "./ToolGraph";
// import { ChatMessage as ChatMessageType, GraphNode } from "@/lib/types";

// export default function ChatMessage({
//   message,
//   graphNodes,
//   thinkingTrace,
// }: {
//   message: ChatMessageType;
//   graphNodes?: GraphNode[];
//   thinkingTrace?: string;
// }) {
//   const isUser = message.role === "user";

//   return (
//     <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
//       <div
//         className={[
//           "max-w-[85%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap",
//           isUser
//             ? "bg-blue-600 text-white"
//             : message.kind === "error"
//             ? "border border-red-200 bg-red-50 text-red-700"
//             : message.kind === "tool"
//             ? "border border-amber-200 bg-amber-50 text-amber-800"
//             : "bg-gray-100 text-gray-800",
//         ].join(" ")}
//       >
//         {message.content}
//         {message.isStreaming && (
//           <span className="ml-1 inline-block h-4 w-1 animate-pulse rounded bg-gray-400 align-middle" />
//         )}

//         {!isUser && thinkingTrace && (
//           <CollapsibleTrace title="Thinking" content={thinkingTrace} />
//         )}

//         {!isUser && graphNodes && graphNodes.length > 0 && (
//           <ToolGraph nodes={graphNodes} />
//         )}
//       </div>
//     </div>
//   );
// }



"use client";

import CollapsibleTrace from "./CollapsibleTrace";
import ToolGraph from "./ToolGraph";
import { ChatMessage as ChatMessageType, GraphNode } from "@/lib/types";

export default function ChatMessage({
  message,
  graphNodes,
  thinkingTrace,
}: {
  message: ChatMessageType;
  graphNodes?: GraphNode[];
  thinkingTrace?: string;
}) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className="max-w-[85%]">
        <div
          className={[
            "rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap",
            isUser
              ? "bg-blue-600 text-white"
              : message.kind === "error"
              ? "border border-red-200 bg-red-50 text-red-700"
              : message.kind === "tool"
              ? "border border-amber-200 bg-amber-50 text-amber-800"
              : "bg-gray-100 text-gray-800",
          ].join(" ")}
        >
          {message.content}
          {message.isStreaming && (
            <span className="ml-1 inline-block h-4 w-1 animate-pulse rounded bg-gray-400 align-middle" />
          )}
        </div>

        {!isUser && thinkingTrace && <CollapsibleTrace title="Reasoning timeline" content={thinkingTrace} />}

        {!isUser && graphNodes && graphNodes.length > 0 && (
          <ToolGraph nodes={graphNodes} />
        )}
      </div>
    </div>
  );
}