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
} from "lucide-react";

const NAV = [
  { href: "/",              label: "Overview",        icon: LayoutDashboard },
  { href: "/sentiment",     label: "Sentiment",       icon: BarChart2       },
  { href: "/themes",        label: "Themes",          icon: Hash            },
  { href: "/pain-points",   label: "Pain Points",     icon: AlertTriangle   },
  { href: "/segments",      label: "User Segments",   icon: Users           },
  { href: "/summaries",     label: "AI Summaries",    icon: FileText        },
  { href: "/opportunities", label: "Opportunities",   icon: Lightbulb       },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed top-0 left-0 h-full w-56 bg-sp-black flex flex-col z-50 border-r border-sp-gray">
      {/* Logo */}
      <div className="px-6 py-6 flex items-center gap-3">
        <svg viewBox="0 0 24 24" className="w-8 h-8 fill-sp-green" aria-hidden>
          <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
        </svg>
        <div>
          <p className="text-sp-white font-bold text-sm leading-tight">Review</p>
          <p className="text-sp-green font-bold text-sm leading-tight">Analysis</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-2 space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-sp text-sm font-medium transition-all
                ${active
                  ? "bg-sp-gray text-sp-white"
                  : "text-sp-light-gray hover:text-sp-white hover:bg-sp-gray/50"
                }`}
            >
              <Icon size={18} className={active ? "text-sp-green" : "text-current"} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-6 py-4 border-t border-sp-gray">
        <p className="text-sp-light-gray text-xs">Spotify Review Engine</p>
        <p className="text-sp-mid-gray text-xs">1,799 reviews analysed</p>
      </div>
    </aside>
  );
}
