"use client";

import { useState } from "react";

export default function CollapsibleTrace({
  title,
  content,
}: {
  title: string;
  content: string;
}) {
  const [open, setOpen] = useState(false);

  if (!content.trim()) return null;

  return (
    <div className="mt-2 rounded-xl border border-gray-200 bg-gray-50">
      <button
        className="w-full px-4 py-3 text-left text-sm font-medium text-gray-700"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? "▼" : "▶"} {title}
      </button>
      {open && (
        <div className="border-t border-gray-200 px-4 py-3 text-sm whitespace-pre-wrap text-gray-600">
          {content}
        </div>
      )}
    </div>
  );
}