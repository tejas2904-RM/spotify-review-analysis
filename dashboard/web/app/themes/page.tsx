import { api } from "@/lib/api";
import ThemeBar from "@/components/charts/ThemeBar";
import SentimentTimeline from "@/components/charts/SentimentTimeline";
import { Hash } from "lucide-react";

export const dynamic = "force-dynamic";

const SENTIMENT_COLOR: Record<string, string> = {
  positive: "#1DB954",
  neutral:  "#999999",
  negative: "#E84040",
};

export default async function ThemesPage() {
  let data: any = {};
  try { data = await api.themes(); } catch {}

  const topThemes: any[] = data.top_themes ?? [];
  const sentBreak: any = data.sentiment_breakdown ?? {};
  const bySource: any = data.by_source ?? {};
  const cooc: any[] = data.cooccurrence ?? [];

  return (
    <div className="space-y-6">

      {/* Theme Frequency — full width */}
      <div className="glass-card p-6">
        <p className="text-sm font-semibold text-white mb-1">Theme Frequency</p>
        <p className="text-xs mb-5" style={{ color: "#999999" }}>
          Top recurring topics identified across 1,799 reviews
        </p>
        {topThemes.length > 0 ? (
          <ThemeBar data={topThemes.slice(0, 10)} height={280} />
        ) : (
          <div className="flex items-center justify-center h-40">
            <p className="text-sm" style={{ color: "#555555" }}>No theme data yet — run aggregate</p>
          </div>
        )}
      </div>

      {/* Sentiment breakout + co-occurrence */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Theme Sentiment Breakout */}
        <div className="glass-card p-6">
          <p className="text-sm font-semibold text-white mb-4">Theme Sentiment Breakout</p>
          <div className="space-y-3 overflow-y-auto max-h-72">
            {Object.entries(sentBreak)
              .sort((a: any, b: any) => b[1].total - a[1].total)
              .slice(0, 10)
              .map(([theme, info]: [string, any]) => {
                const sp = info.percentages ?? {};
                return (
                  <div key={theme}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm capitalize text-white">{theme.replace(/_/g, " ")}</span>
                      <span className="text-xs" style={{ color: "#555555" }}>{info.total}</span>
                    </div>
                    <div className="flex h-2 rounded-full overflow-hidden gap-px">
                      <div style={{ width: `${sp.positive ?? 0}%`, background: "#1DB954" }} />
                      <div style={{ width: `${sp.neutral ?? 0}%`,  background: "#555555" }} />
                      <div style={{ width: `${sp.negative ?? 0}%`, background: "#E84040" }} />
                    </div>
                  </div>
                );
              })}
          </div>
          <div className="flex gap-5 mt-4 pt-3" style={{ borderTop: "1px solid #2a2a2a" }}>
            {[["#1DB954","Positive"],["#555555","Neutral"],["#E84040","Negative"]].map(([c,l]) => (
              <div key={l} className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ background: c }} />
                <span className="text-xs" style={{ color: "#999999" }}>{l}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Theme Co-occurrence */}
        <div className="glass-card p-6">
          <p className="text-sm font-semibold text-white mb-1">Theme Co-occurrence</p>
          <p className="text-xs mb-4" style={{ color: "#999999" }}>Pairs that appear together most often</p>
          {cooc.length > 0 ? (
            <div className="grid grid-cols-2 gap-2 overflow-y-auto max-h-72">
              {cooc.slice(0, 8).map((pair: any, i: number) => (
                <div key={i} className="rounded-sp-sm p-3 text-center" style={{ background: "#1c1c1c" }}>
                  <p className="text-xs font-semibold capitalize" style={{ color: "#1DB954" }}>
                    {pair.theme_a.replace(/_/g, " ")}
                  </p>
                  <p className="text-xs my-0.5" style={{ color: "#555555" }}>+</p>
                  <p className="text-xs font-semibold capitalize" style={{ color: "#1DB954" }}>
                    {pair.theme_b.replace(/_/g, " ")}
                  </p>
                  <p className="text-xl font-bold text-white mt-2">{pair.count}</p>
                  <p className="text-xs" style={{ color: "#555555" }}>times</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-40">
              <p className="text-sm" style={{ color: "#555555" }}>No co-occurrence data</p>
            </div>
          )}
        </div>
      </div>

      {/* Volume Trends (themes by source as proxy) */}
      <div className="glass-card p-6">
        <p className="text-sm font-semibold text-white mb-1">Themes by Source</p>
        <p className="text-xs mb-5" style={{ color: "#999999" }}>Distribution of top themes per data source</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Object.entries(bySource).map(([source, themes]: [string, any]) => (
            <div key={source}>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-5 h-5 rounded flex items-center justify-center"
                     style={{ background: "#1DB95418" }}>
                  <Hash size={11} style={{ color: "#1DB954" }} />
                </div>
                <p className="text-sm font-semibold text-white capitalize">{source.replace(/_/g, " ")}</p>
              </div>
              <div className="space-y-2">
                {themes.slice(0, 6).map((t: any) => (
                  <div key={t.theme}>
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-xs capitalize" style={{ color: "#999999" }}>{t.theme.replace(/_/g, " ")}</span>
                      <span className="text-xs" style={{ color: "#555555" }}>{t.count}</span>
                    </div>
                    <div className="h-1.5 rounded-full" style={{ background: "#2a2a2a" }}>
                      <div className="h-1.5 rounded-full" style={{ width: `${Math.min(t.pct_of_source, 100)}%`, background: "#1DB954" }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <p className="text-center text-xs pb-4" style={{ color: "#555555" }}>
        © 2026 ReviewAnalytics Platform. All data real-time via API.
      </p>
    </div>
  );
}
