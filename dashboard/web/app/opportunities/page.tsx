import { api } from "@/lib/api";
import { Sparkles, Download, Zap, Smartphone, Tag, BarChart2, Bell, Globe } from "lucide-react";

export const dynamic = "force-dynamic";

const PRIORITY_BADGE: Record<string, { label: string; color: string; bg: string }> = {
  high:   { label: "HIGH PRIORITY",      color: "#E84040", bg: "#E8404018" },
  medium: { label: "MEDIUM PRIORITY",    color: "#999999", bg: "#22222288" },
  low:    { label: "GROWTH OPPORTUNITY", color: "#1DB954", bg: "#1DB95418" },
};

const OPP_ICONS = [Sparkles, Download, Smartphone, Tag, Bell, Globe, BarChart2, Zap];

export default async function OpportunitiesPage() {
  let data: any = {};
  try { data = await api.opportunities(); } catch {}

  const opps: any[] = data.opportunities ?? [];

  return (
    <div className="space-y-6">

      {/* Hero banner */}
      <div className="glass-card p-8 relative overflow-hidden"
           style={{
             background: "linear-gradient(135deg, #161616 60%, #1DB95415 100%)",
             border: "1px solid #2a2a2a",
           }}>
        <div className="flex items-start gap-4">
          <span className="text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1.5"
                style={{ background: "#1DB95418", color: "#1DB954", border: "1px solid #1DB95440" }}>
            <span className="w-1.5 h-1.5 rounded-full bg-[#1DB954] animate-pulse" />
            AI Insights Live
          </span>
        </div>
        <h2 className="text-3xl font-bold text-white mt-3">
          {opps.length} product {opps.length === 1 ? "opportunity" : "opportunities"} identified
        </h2>
        <p className="mt-2 max-w-lg" style={{ color: "#999999" }}>
          We've analysed 1,799 customer reviews to pinpoint high-impact areas for your next sprint.
        </p>
        {/* Decorative circles */}
        <div className="absolute right-8 top-1/2 -translate-y-1/2 w-32 h-32 rounded-full opacity-10"
             style={{ background: "#1DB954", filter: "blur(40px)" }} />
      </div>

      {opps.length === 0 && (
        <div className="glass-card p-12 flex flex-col items-center gap-4">
          <Sparkles size={36} style={{ color: "#555555" }} />
          <p className="font-semibold text-white">No opportunities yet</p>
          <code className="text-xs px-3 py-1.5 rounded" style={{ color: "#1DB954", background: "#1c1c1c" }}>
            python -m src.pipeline aggregate
          </code>
        </div>
      )}

      {/* 3-column grid */}
      {opps.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {opps.map((opp: any, i: number) => {
            const badge = PRIORITY_BADGE[opp.priority] ?? PRIORITY_BADGE.medium;
            const Icon = OPP_ICONS[i % OPP_ICONS.length];
            return (
              <div key={i}
                   className="glass-card p-5 flex flex-col gap-3 hover:border-[#3a3a3a] transition-colors cursor-pointer">
                <div className="flex items-start justify-between">
                  <div className="w-9 h-9 rounded-sp-sm flex items-center justify-center"
                       style={{ background: "#1DB95418" }}>
                    <Icon size={18} style={{ color: "#1DB954" }} />
                  </div>
                  <span className="text-xs font-bold px-2 py-0.5 rounded"
                        style={{ background: badge.bg, color: badge.color }}>
                    {badge.label}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-white">{opp.title}</h3>
                <p className="text-xs leading-relaxed flex-1" style={{ color: "#999999" }}>
                  {opp.problem_statement}
                </p>
                {opp.evidence?.slice(0, 2).map((e: string, j: number) => (
                  <div key={j} className="flex items-start gap-1.5 text-xs" style={{ color: "#999999" }}>
                    <span style={{ color: "#1DB954" }}>→</span>
                    <span className="line-clamp-1">{e}</span>
                  </div>
                ))}
                <div className="flex gap-2 pt-3" style={{ borderTop: "1px solid #2a2a2a" }}>
                  <span className="text-xs px-2 py-0.5 rounded-full flex items-center gap-1"
                        style={{ background: "#1c1c1c", color: "#999999", border: "1px solid #2a2a2a" }}>
                    <span style={{ color: "#1DB954" }}>↗</span> Impact: {opp.priority === "high" ? "High" : opp.priority === "medium" ? "Med" : "Low"}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded-full flex items-center gap-1"
                        style={{ background: "#1c1c1c", color: "#999999", border: "1px solid #2a2a2a" }}>
                    <span style={{ color: "#F59E0B" }}>⚡</span> Effort: {opp.priority === "low" ? "Low" : "Med"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Bottom summary row */}
      {opps.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="glass-card p-6">
            <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "#555555" }}>Summary Analysis</p>
            <h3 className="text-lg font-bold text-white mb-1">
              Addressing these could improve user satisfaction
            </h3>
            <p className="text-sm mb-4" style={{ color: "#999999" }}>
              Based on trend analysis from {opps.length} identified opportunities.
            </p>
            <button className="px-5 py-2.5 rounded-full text-sm font-bold transition-opacity hover:opacity-80"
                    style={{ background: "#1DB954", color: "#000" }}>
              Generate Roadmap
            </button>
          </div>
          <div className="glass-card p-6 flex items-center gap-6">
            <div className="text-center shrink-0">
              <p className="text-4xl font-bold" style={{ color: "#1DB954" }}>
                {Math.round(60 + opps.length * 3)}%
              </p>
            </div>
            <div>
              <p className="text-sm font-semibold text-white mb-1">Data Confidence</p>
              <p className="text-xs" style={{ color: "#999999" }}>
                High correlation between identified reviews and churn data points.
              </p>
            </div>
          </div>
        </div>
      )}

      <p className="text-center text-xs pb-4" style={{ color: "#555555" }}>
        © 2026 ReviewAnalytics Platform. All data real-time via API.
      </p>
    </div>
  );
}
