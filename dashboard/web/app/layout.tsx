import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800", "900"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ReviewAnalytics — Spotify Insights",
  description: "AI-powered insights from 1,799 Spotify user reviews",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-spotify antialiased`}
            style={{ background: "#0d0d0d", color: "#ffffff" }}>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <Navbar />
          <main
            className="flex-1 overflow-y-auto"
            style={{ marginLeft: "224px", marginTop: "56px" }}
          >
            <div className="max-w-7xl mx-auto px-8 py-8">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
