import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ReAct Multi-Agent Assistant",
  description: "FastAPI + PydanticAI + Next.js",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}