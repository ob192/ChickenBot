import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "ChickenBot admin",
  description: "Control the bot, its users and who may talk to it",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="topbar">
            <div className="brand">
              Chicken<span>Bot</span> admin
            </div>
            <nav className="nav">
              <Link href="/">Dashboard</Link>
              <Link href="/users">Users</Link>
              <Link href="/messages">Messages</Link>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
