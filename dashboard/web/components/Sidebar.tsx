"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BarChart2,
  Hash,
  AlertTriangle,
  Users,
  FileText,
  Lightbulb,
  Settings,
} from "lucide-react";

const NAV = [
  { href: "/",              label: "Overview",       icon: LayoutDashboard },
  { href: "/sentiment",     label: "Sentiments",     icon: BarChart2       },
  { href: "/themes",        label: "Themes",         icon: Hash            },
  { href: "/pain-points",   label: "Pain Points",    icon: AlertTriangle   },
  { href: "/segments",      label: "User Segments",  icon: Users           },
  { href: "/summaries",     label: "AI Summaries",   icon: FileText        },
  { href: "/opportunities", label: "Opportunities",  icon: Lightbulb       },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed top-0 left-0 h-full w-56 flex flex-col z-50"
           style={{ background: "#111111", borderRight: "1px solid #2a2a2a" }}>

      {/* Brand */}
      <div className="px-5 py-5 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
             style={{ background: "#1DB954" }}>
          <svg viewBox="0 0 24 24" className="w-4 h-4 fill-black" aria-hidden>
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
        </div>
        <div>
          <p className="text-white font-bold text-sm leading-tight">ReviewAnalytics</p>
          <p className="text-[10px] leading-tight" style={{ color: "#555555" }}>DATA INSIGHTS</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-2 space-y-0.5 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-sp-sm text-sm font-medium transition-all duration-150 ${
                active
                  ? "text-white"
                  : "hover:text-white"
              }`}
              style={{
                background:  active ? "#222222" : "transparent",
                color:       active ? "#ffffff"  : "#999999",
              }}
            >
              <Icon
                size={17}
                style={{ color: active ? "#1DB954" : "currentColor" }}
              />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Divider */}
      <div style={{ borderTop: "1px solid #2a2a2a" }} className="mx-3" />

      {/* Settings */}
      <div className="px-3 py-2">
        <Link
          href="#"
          className="flex items-center gap-3 px-3 py-2.5 rounded-sp-sm text-sm font-medium transition-all duration-150"
          style={{ color: "#999999" }}
        >
          <Settings size={17} />
          Settings
        </Link>
      </div>

      {/* Footer */}
      <div className="px-5 py-4" style={{ borderTop: "1px solid #2a2a2a" }}>
        <p className="text-xs font-medium" style={{ color: "#999999" }}>Spotify Review Engine</p>
        <p className="text-xs" style={{ color: "#555555" }}>1,799 reviews analysed</p>
      </div>
    </aside>
  );
}
