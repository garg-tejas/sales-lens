import "./globals.css";
import type { ReactNode } from "react";
import { ClientLayout } from "./client-layout";

export const metadata = {
  title: {
    default: "SalesLens - Real-Time Call Intelligence",
    template: "%s | SalesLens",
  },
  description: "Upload and analyze sales calls with real-time transcription, sentiment analysis, and AI-powered insights.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}
