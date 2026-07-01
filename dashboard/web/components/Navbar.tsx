"use client";
import { usePathname } from "next/navigation";
import { Search, Bell, HelpCircle } from "lucide-react";

const PAGE_TITLES: Record<string, string> = {
  "/":              "Overview",
  "/sentiment":     "Sentiment Analysis",
  "/themes":        "Themes Analysis",
  "/pain-points":   "Pain Points",
  "/segments":      "User Segments",
  "/summaries":     "AI Summaries",
  "/opportunities": "Product Opportunities",
};

export default function Navbar() {
  const pathname = usePathname();
  const title = PAGE_TITLES[pathname] ?? "Dashboard";

  return (
    <header
      className="fixed top-0 right-0 z-40 flex items-center gap-4 px-8 h-14"
      style={{
        left: "224px",
        background: "#0d0d0d",
        borderBottom: "1px solid #2a2a2a",
      }}
    >
      {/* Page title */}
      <h1 className="text-white font-semibold text-base flex-shrink-0">{title}</h1>

      {/* Search */}
      <div className="flex-1 max-w-xs ml-4">
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-full"
          style={{ background: "#1c1c1c", border: "1px solid #2a2a2a" }}
        >
          <Search size={14} style={{ color: "#555555" }} />
          <input
            type="text"
            placeholder={`Search ${title.toLowerCase()}...`}
            className="bg-transparent text-sm outline-none flex-1 placeholder:text-[#555555] text-white"
          />
        </div>
      </div>

      <div className="flex-1" />

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          className="w-8 h-8 rounded-full flex items-center justify-center transition-colors hover:bg-[#1c1c1c]"
          style={{ color: "#999999" }}
        >
          <Bell size={16} />
        </button>
        <button
          className="w-8 h-8 rounded-full flex items-center justify-center transition-colors hover:bg-[#1c1c1c]"
          style={{ color: "#999999" }}
        >
          <HelpCircle size={16} />
        </button>

        {/* Avatar */}
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white ml-1"
          style={{ background: "#1DB954" }}
        >
          S
        </div>
      </div>
    </header>
  );
}
