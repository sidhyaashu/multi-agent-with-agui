"use client";

import { GraphNode } from "@/lib/types";

export default function ToolGraph({ nodes }: { nodes: GraphNode[] }) {
  if (nodes.length === 0) return null;

  return (
    <div className="mt-3 rounded-xl border border-gray-200 bg-white p-3">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        Tool graph
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="rounded-full bg-blue-50 px-3 py-1 text-xs text-blue-700">
          User
        </div>

        {nodes.map((node, index) => (
          <div key={node.id} className="flex items-center gap-2">
            <div className="text-gray-300">→</div>
            <div
              className={`rounded-full px-3 py-1 text-xs ${
                node.status === "done"
                  ? "bg-green-50 text-green-700"
                  : "bg-amber-50 text-amber-700"
              }`}
            >
              {node.label}
            </div>
          </div>
        ))}

        {nodes.length > 0 && (
          <>
            <div className="text-gray-300">→</div>
            <div className="rounded-full bg-purple-50 px-3 py-1 text-xs text-purple-700">
              Final answer
            </div>
          </>
        )}
      </div>
    </div>
  );
}