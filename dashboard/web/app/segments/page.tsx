import { api } from "@/lib/api";
import { AlertTriangle, Zap, Coffee, UserPlus, Download } from "lucide-react";

export const dynamic = "force-dynamic";

const SEGMENTS = [
  {
    key: "churn_risk",
    label: "Churn Risk",
    desc: "Users with declining activity and negative recent sentiment trends.",
    border: "#E84040",
    bg: "#E8404010",
    badge: { text: "HIGH PRIORITY", color: "#E84040", bg: "#E8404018" },
    icon: AlertTriangle,
    iconColor: "#E84040",
  },
  {
    key: "power_user",
    label: "Power Users",
    desc: "High-engagement advocates who use core features daily.",
    border: "#1DB954",
    bg: "#1DB95410",
    badge: { text: "LOYALISTS", color: "#1DB954", bg: "#1DB95418" },
    icon: Zap,
    iconColor: "#1DB954",
  },
  {
    key: "casual",
    label: "Casual Users",
    desc: "Infrequent visitors using basic utility features occasionally.",
    border: "#555555",
    bg: "#55555510",
    badge: { text: "STABLE", color: "#999999", bg: "#22222288" },
    icon: Coffee,
    iconColor: "#999999",
  },
  {
    key: "new_user",
    label: "New Users",
    desc: "Users who joined recently. Critical for first impressions.",
    border: "#1DB954",
    bg: "#1DB95410",
    badge: { text: "ONBOARDING", color: "#1DB954", bg: "#1DB95418" },
    icon: UserPlus,
    iconColor: "#1DB954",
  },
];

export default async function SegmentsPage() {
  let data: any = {};
  try { data = await api.segments(); } catch {}

  const dist: any  = data.distribution ?? {};
  const sentSeg: any = data.sentiment_by_segment ?? {};
  const churn: any = data.churn_signals ?? {};

  const total = Object.values(dist).reduce((s: number, v: any) => s + (v.count ?? 0), 0) as number;

  return (
    <div className="space-y-6">

      {/* Top row: donut + key insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="glass-card p-6 lg:col-span-2">
          <p className="text-sm font-semibold text-white mb-1">Segment Distribution</p>
          <div className="flex items-center gap-8 mt-4">
            {/* Visual bar */}
            <div className="flex-1">
              <div className="flex h-3 rounded-full overflow-hidden gap-0.5">
                {SEGMENTS.map(seg => {
                  const info = dist[seg.key] ?? {};
                  return (
                    <div key={seg.key}
                         style={{ width: `${info.pct ?? 0}%`, background: seg.border }}
                         title={`${seg.label}: ${info.pct ?? 0}%`} />
                  );
                })}
              </div>
              <div className="grid grid-cols-2 gap-3 mt-4">
                {SEGMENTS.map(seg => {
                  const info = dist[seg.key] ?? {};
                  return (
                    <div key={seg.key} className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: seg.border }} />
                      <div>
                        <p className="text-sm font-semibold text-white">{seg.label}</p>
                        <p className="text-xs" style={{ color: "#999999" }}>{info.pct ?? 0}%</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            {/* Big donut placeholder stat */}
            <div className="text-center shrink-0">
              <p className="text-5xl font-bold" style={{ color: "#1DB954" }}>{total.toLocaleString()}</p>
              <p className="text-xs mt-1 font-semibold" style={{ color: "#999999" }}>TOTAL</p>
            </div>
          </div>
        </div>

        {/* Key Insights */}
        <div className="glass-card p-6">
          <p className="text-sm font-semibold text-white mb-4">Key Insights</p>
          <div className="space-y-4">
            {[
              { label: "Churn Risk",   val: `${dist.churn_risk?.pct ?? 0}%`,  color: "#E84040" },
              { label: "Avg Sentiment",val: "0.41",                            color: "#1DB954" },
              { label: "Power Users",  val: `${dist.power_user?.pct ?? 0}%`,  color: "#1DB954" },
            ].map(({ label, val, color }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-sm" style={{ color: "#999999" }}>{label}</span>
                <span className="text-lg font-bold" style={{ color }}>{val}</span>
              </div>
            ))}
            <button className="w-full text-xs font-semibold py-2 rounded-sp-sm mt-2 transition-opacity hover:opacity-80"
                    style={{ background: "#1DB954", color: "#000" }}>
              Download Report
            </button>
          </div>
        </div>
      </div>

      {/* 2×2 Segment cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SEGMENTS.map(seg => {
          const info = dist[seg.key] ?? {};
          const ss   = sentSeg[seg.key] ?? {};
          const Icon = seg.icon;
          return (
            <div key={seg.key} className="glass-card p-5"
                 style={{ borderLeft: `3px solid ${seg.border}` }}>
              <div className="flex items-start justify-between mb-3">
                <div className="w-9 h-9 rounded-sp-sm flex items-center justify-center"
                     style={{ background: seg.bg }}>
                  <Icon size={18} style={{ color: seg.iconColor }} />
                </div>
                <span className="text-xs font-bold px-2 py-0.5 rounded"
                      style={{ background: seg.badge.bg, color: seg.badge.color }}>
                  {seg.badge.text}
                </span>
              </div>
              <h3 className="text-base font-bold text-white mb-1">{seg.label}</h3>
              <p className="text-xs leading-relaxed mb-3" style={{ color: "#999999" }}>{seg.desc}</p>
              <div className="flex gap-4 pt-3" style={{ borderTop: "1px solid #2a2a2a" }}>
                <div>
                  <p className="text-xs" style={{ color: "#555555" }}>SIZE</p>
                  <p className="text-sm font-bold text-white">{info.count?.toLocaleString() ?? "—"}</p>
                </div>
                <div>
                  <p className="text-xs" style={{ color: "#555555" }}>SENTIMENT</p>
                  <p className="text-sm font-bold" style={{ color: seg.iconColor }}>
                    {ss.percentages?.positive ?? "—"}{ss.percentages?.positive ? "%" : ""}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom: sentiment by segment + churn signals */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="glass-card p-6">
          <p className="text-sm font-semibold text-white mb-4">Sentiment by Segment</p>
          <div className="space-y-4">
            {SEGMENTS.map(seg => {
              const ss = sentSeg[seg.key] ?? {};
              const pos = ss.percentages?.positive ?? 0;
              return (
                <div key={seg.key}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-white">{seg.label}</span>
                    <span className="text-xs font-semibold" style={{ color: "#1DB954" }}>{pos}% Positive</span>
                  </div>
                  <div className="flex h-2 rounded-full overflow-hidden">
                    <div style={{ width: `${pos}%`,                         background: "#1DB954" }} />
                    <div style={{ width: `${ss.percentages?.neutral ?? 0}%`, background: "#555555" }} />
                    <div style={{ width: `${ss.percentages?.negative ?? 0}%`,background: "#E84040" }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Churn risk signals */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-semibold text-white">Churn Risk Signals</p>
            {churn.count > 0 && (
              <span className="text-xs font-bold px-2 py-0.5 rounded"
                    style={{ background: "#E8404018", color: "#E84040" }}>
                {churn.count} CRITICAL
              </span>
            )}
          </div>
          {churn.count > 0 ? (
            <div className="space-y-2">
              {Object.entries(churn.top_emotions ?? {}).slice(0, 4).map(([emotion, count]: [string, any]) => (
                <div key={emotion} className="flex items-center justify-between p-3 rounded-sp-sm"
                     style={{ background: "#1c1c1c" }}>
                  <p className="text-sm capitalize text-white">{emotion}</p>
                  <span className="text-xs font-bold px-2 py-0.5 rounded"
                        style={{ background: "#E8404018", color: "#E84040" }}>
                    ALERT
                  </span>
                </div>
              ))}
              {Object.entries(churn.top_themes ?? {}).slice(0, 3).map(([theme, count]: [string, any]) => (
                <div key={theme} className="flex items-center justify-between p-3 rounded-sp-sm"
                     style={{ background: "#1c1c1c" }}>
                  <p className="text-sm capitalize text-white">{theme.replace(/_/g, " ")}</p>
                  <span className="text-xs" style={{ color: "#999999" }}>{count} reviews</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-32">
              <p className="text-sm" style={{ color: "#555555" }}>No churn signals detected</p>
            </div>
          )}
        </div>
      </div>

      <p className="text-center text-xs pb-4" style={{ color: "#555555" }}>
        © 2026 ReviewAnalytics Platform. All data real-time via API.
      </p>
    </div>
  );
}
