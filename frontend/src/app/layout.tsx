import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Overseer AI",
    template: "%s | Overseer AI",
  },
  description: "AI-powered oversight and monitoring platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-surface-muted antialiased dark:bg-surface-dark">
        {children}
      </body>
    </html>
  );
}
