import { api } from "@/lib/api";
import SentimentDonut from "@/components/charts/SentimentDonut";
import SentimentTimeline from "@/components/charts/SentimentTimeline";
import { TrendingUp, TrendingDown, Minus, Filter } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function SentimentPage() {
  let data: any = {};
  try { data = await api.sentiment(); } catch {}

  const overall = data.overall ?? {};
  const bySource = data.by_source ?? {};
  const overTime = data.over_time ?? {};
  const pct = overall.percentages ?? {};
  const counts = overall.counts ?? {};

  return (
    <div className="space-y-6">

      {/* KPI row — styled like mockup */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Positive */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#555555" }}>Positive Sentiment</p>
            <TrendingUp size={16} style={{ color: "#1DB954" }} />
          </div>
          <p className="text-4xl font-bold mt-2" style={{ color: "#1DB954" }}>{pct.positive ?? 0}%</p>
          <div className="mt-3 h-1 rounded-full" style={{ background: "#2a2a2a" }}>
            <div className="h-1 rounded-full" style={{ width: `${pct.positive ?? 0}%`, background: "#1DB954" }} />
          </div>
          <p className="text-xs mt-2" style={{ color: "#999999" }}>{counts.positive?.toLocaleString() ?? 0} reviews</p>
        </div>

        {/* Neutral */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#555555" }}>Neutral Sentiment</p>
            <Minus size={16} style={{ color: "#999999" }} />
          </div>
          <p className="text-4xl font-bold mt-2 text-white">{pct.neutral ?? 0}%</p>
          <div className="mt-3 h-1 rounded-full" style={{ background: "#2a2a2a" }}>
            <div className="h-1 rounded-full" style={{ width: `${pct.neutral ?? 0}%`, background: "#999999" }} />
          </div>
          <p className="text-xs mt-2" style={{ color: "#999999" }}>{counts.neutral?.toLocaleString() ?? 0} reviews</p>
        </div>

        {/* Negative */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#555555" }}>Negative Sentiment</p>
            <TrendingDown size={16} style={{ color: "#E84040" }} />
          </div>
          <p className="text-4xl font-bold mt-2" style={{ color: "#E84040" }}>{pct.negative ?? 0}%</p>
          <div className="mt-3 h-1 rounded-full" style={{ background: "#2a2a2a" }}>
            <div className="h-1 rounded-full" style={{ width: `${pct.negative ?? 0}%`, background: "#E84040" }} />
          </div>
          <p className="text-xs mt-2" style={{ color: "#999999" }}>{counts.negative?.toLocaleString() ?? 0} reviews</p>
        </div>
      </div>

      {/* Distribution + Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        <div className="glass-card p-6 flex flex-col items-center lg:col-span-2">
          <p className="text-sm font-semibold text-white w-full mb-1">Distribution</p>
          <p className="text-xs w-full mb-5" style={{ color: "#999999" }}>Net score: {overall.avg_score?.toFixed(1) ?? "—"}</p>
          <SentimentDonut
            positive={pct.positive ?? 0}
            neutral={pct.neutral ?? 0}
            negative={pct.negative ?? 0}
          />
          <div className="flex gap-4 mt-4">
            {[
              { label: "Positive", val: counts.positive, color: "#1DB954" },
              { label: "Neutral",  val: counts.neutral,  color: "#999999" },
              { label: "Negative", val: counts.negative, color: "#E84040" },
            ].map(({ label, val, color }) => (
              <div key={label} className="text-center">
                <div className="flex items-center gap-1 mb-0.5">
                  <div className="w-2 h-2 rounded-full" style={{ background: color }} />
                  <span className="text-xs" style={{ color: "#999999" }}>{label}</span>
                </div>
                <p className="text-sm font-bold text-white">{val?.toLocaleString() ?? 0}</p>
              </div>
            ))}
          </div>
        </div>

        {Object.keys(overTime).length > 0 ? (
          <div className="glass-card p-6 lg:col-span-3">
            <p className="text-sm font-semibold text-white mb-1">Sentiment Trends</p>
            <p className="text-xs mb-4" style={{ color: "#999999" }}>Monthly trend by label</p>
            <SentimentTimeline overTime={overTime} />
          </div>
        ) : (
          <div className="glass-card p-6 lg:col-span-3 flex items-center justify-center">
            <p className="text-sm" style={{ color: "#555555" }}>No timeline data yet</p>
          </div>
        )}
      </div>

      {/* Sentiment by Source */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-sm font-semibold text-white">Sentiment by Source</p>
            <p className="text-xs mt-0.5" style={{ color: "#999999" }}>
              Breakdown of user perception across primary channels
            </p>
          </div>
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-sp-sm text-xs font-medium transition-colors hover:bg-[#222222]"
                  style={{ color: "#999999", border: "1px solid #2a2a2a" }}>
            <Filter size={12} /> Filter Channels
          </button>
        </div>
        <div className="space-y-4">
          {Object.entries(bySource).map(([source, info]: [string, any]) => {
            const sp = info.percentages ?? {};
            const posW = sp.positive ?? 0;
            return (
              <div key={source} className="flex items-center gap-4">
                <div className="w-8 h-8 rounded-sp-sm flex items-center justify-center shrink-0"
                     style={{ background: "#222222" }}>
                  <span className="text-xs font-bold" style={{ color: "#1DB954" }}>
                    {source[0].toUpperCase()}
                  </span>
                </div>
                <p className="w-32 text-sm capitalize shrink-0 text-white">
                  {source.replace(/_/g, " ")}
                </p>
                <div className="flex-1 flex h-2.5 rounded-full overflow-hidden gap-px">
                  <div style={{ width: `${posW}%`,         background: "#1DB954" }} />
                  <div style={{ width: `${sp.neutral ?? 0}%`, background: "#2a2a2a" }} />
                  <div style={{ width: `${sp.negative ?? 0}%`, background: "#E84040" }} />
                </div>
                <p className="w-10 text-right text-sm font-semibold text-white">{posW}%</p>
              </div>
            );
          })}
        </div>
        {/* Legend */}
        <div className="flex gap-6 mt-5 pt-4" style={{ borderTop: "1px solid #2a2a2a" }}>
          {[["#1DB954","Positive Feedback"],["#2a2a2a","Neutral"],["#E84040","Negative/Critical"]].map(([c,l]) => (
            <div key={l} className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: c }} />
              <span className="text-xs" style={{ color: "#999999" }}>{l}</span>
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
