import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "TransportERP-UA",
  description: "Transport enterprise management system for Ukraine",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="uk">
      <body>{children}</body>
    </html>
  );
}
