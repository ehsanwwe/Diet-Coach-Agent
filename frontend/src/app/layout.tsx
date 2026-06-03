import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Diet Coach Agent",
  description: "Your AI-powered nutrition companion",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // Phase 2 will set lang and dir attributes server-side from cookie/param.
    // For now, direction is prepared in [lang]/layout.tsx.
    <html>
      <body>{children}</body>
    </html>
  );
}
