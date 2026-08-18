import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Pantau Infrastruktur",
    template: "%s | Pantau Infrastruktur",
  },
  description: "Portal monitoring server, jaringan, dan layanan digital.",
};

export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}

