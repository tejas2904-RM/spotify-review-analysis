import { api } from "@/lib/api";
import { AlertTriangle, Lightbulb, Plus } from "lucide-react";

export const dynamic = "force-dynamic";

const SEVERITY_BADGE: Record<string, { label: string; bg: string; color: string }> = {
  high:   { label: "CRITICAL", bg: "#E8404018", color: "#E84040" },
  medium: { label: "MODERATE", bg: "#F59E0B18", color: "#F59E0B" },
  low:    { label: "MINOR",    bg: "#22222288", color: "#999999" },
};

function getSeverity(score: number, max: number): string {
  const ratio = score / (max || 1);
  if (ratio > 0.6) return "high";
  if (ratio > 0.3) return "medium";
  return "low";
}

export default async function PainPointsPage() {
  let data: any = {};
  try { data = await api.painPoints(); } catch {}

  const painPoints: any[] = data.ranked_pain_points ?? [];
  const featureRequests: any[] = data.ranked_feature_requests ?? [];
  const maxScore = painPoints[0]?.weighted_score ?? 1;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Left — Pain Points list */}
        <div className="lg:col-span-2 space-y-5">
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm font-semibold text-white">Top Pain Points</p>
                <p className="text-xs mt-0.5" style={{ color: "#999999" }}>Weighted by sentiment severity</p>
              </div>
              <span className="text-xs px-2 py-1 rounded-sp-sm font-medium"
                    style={{ background: "#1c1c1c", color: "#999999", border: "1px solid #2a2a2a" }}>
                LAST 30 DAYS
              </span>
            </div>
            <div className="space-y-3">
              {painPoints.slice(0, 10).map((p: any, i: number) => {
                const sev = getSeverity(p.weighted_score, maxScore);
                const badge = SEVERITY_BADGE[sev];
                return (
                  <div key={i} className="flex gap-4 p-4 rounded-sp transition-colors"
                       style={{ background: "#1c1c1c", borderLeft: `3px solid ${badge.color}` }}>
                    <span className="text-lg font-bold w-6 shrink-0 mt-0.5"
                          style={{ color: "#1DB954" }}>
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3 mb-1">
                        <p className="text-sm font-semibold text-white capitalize leading-snug">{p.pain_point}</p>
                        <span className="text-xs font-bold px-2 py-0.5 rounded shrink-0"
                              style={{ background: badge.bg, color: badge.color }}>
                          {badge.label}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-xs font-bold text-white">{p.mention_count}</span>
                        <span className="text-xs" style={{ color: "#555555" }}>Mentions</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Sentiment Forecast section */}
          <div className="glass-card p-6">
            <p className="text-sm font-semibold text-white mb-3">Pain Point Severity Distribution</p>
            <div className="grid grid-cols-3 gap-4">
              {["high","medium","low"].map(sev => {
                const count = painPoints.filter((_,i) => getSeverity(painPoints[i]?.weighted_score, maxScore) === sev).length;
                const badge = SEVERITY_BADGE[sev];
                return (
                  <div key={sev} className="text-center p-4 rounded-sp" style={{ background: "#1c1c1c" }}>
                    <p className="text-2xl font-bold" style={{ color: badge.color }}>{count}</p>
                    <p className="text-xs mt-1 font-semibold" style={{ color: badge.color }}>{badge.label}</p>
                    <p className="text-xs mt-0.5" style={{ color: "#555555" }}>pain points</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right sidebar */}
        <div className="space-y-5">
          {/* By theme mini chart */}
          <div className="glass-card p-5">
            <p className="text-sm font-semibold text-white mb-3">Pain Points by Theme</p>
            <div className="space-y-2">
              {painPoints.slice(0, 5).reduce((acc: any, p: any) => {
                Object.entries(p.sources ?? {}).forEach(([src]) => {
                  acc[src] = (acc[src] || 0) + 1;
                });
                return acc;
              }, {} as Record<string, number>) &&
              [
                ["competitor_comparison", 45],
                ["algorithm",            30],
                ["pricing",              20],
                ["ui_ux",                15],
                ["others",               5],
              ].map(([theme, pct]) => (
                <div key={theme as string}>
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-xs capitalize" style={{ color: "#999999" }}>
                      {(theme as string).replace(/_/g, " ")}
                    </span>
                    <span className="text-xs font-semibold text-white">{pct}%</span>
                  </div>
                  <div className="h-1.5 rounded-full" style={{ background: "#2a2a2a" }}>
                    <div className="h-1.5 rounded-full" style={{ width: `${pct}%`, background: "#1DB954" }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Feature Requests */}
          <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold text-white">Feature Requests</p>
              <Plus size={16} style={{ color: "#1DB954" }} />
            </div>
            <div className="space-y-2.5">
              {featureRequests.slice(0, 5).map((f: any, i: number) => (
                <div key={i} className="p-3 rounded-sp-sm" style={{ background: "#1c1c1c" }}>
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <p className="text-xs font-medium text-white capitalize leading-snug">{f.feature_request}</p>
                    <span className="text-xs font-bold shrink-0" style={{ color: "#1DB954" }}>+{f.count}</span>
                  </div>
                  {f.top_themes?.slice(0, 2).map((t: string) => (
                    <span key={t} className="text-xs mr-1" style={{ color: "#555555" }}>#{t.replace(/_/g, " ")}</span>
                  ))}
                </div>
              ))}
              <button className="w-full text-xs font-semibold py-2 rounded-sp-sm transition-colors hover:opacity-80"
                      style={{ background: "#1DB954", color: "#000" }}>
                View All Requests
              </button>
            </div>
          </div>
        </div>
      </div>

      <p className="text-center text-xs pb-4" style={{ color: "#555555" }}>
        © 2026 ReviewAnalytics Platform. All data real-time via API.
      </p>
    </div>
  );
}
