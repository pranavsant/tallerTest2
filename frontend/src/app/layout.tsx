import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Overseer AI",
  description: "AI-powered oversight and monitoring platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 dark:bg-gray-950">{children}</body>
    </html>
  );
}
