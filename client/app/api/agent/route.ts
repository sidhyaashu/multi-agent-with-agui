import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();

  const res = await fetch("http://localhost:8000/agent", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!res.body) {
    return new Response("No backend stream", { status: 500 });
  }

  return new Response(res.body, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
    },
  });
}