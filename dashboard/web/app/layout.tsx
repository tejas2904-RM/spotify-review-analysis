import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800", "900"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Spotify Review Analysis",
  description: "AI-powered insights from 1,800+ Spotify user reviews",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} bg-sp-black text-white font-spotify antialiased`}>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <main className="ml-56 flex-1 overflow-y-auto bg-gradient-to-b from-sp-dark to-sp-black">
            <div className="max-w-7xl mx-auto px-8 py-8">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
