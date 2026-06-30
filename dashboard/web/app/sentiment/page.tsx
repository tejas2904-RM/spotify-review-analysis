import { api } from "@/lib/api";
import SentimentDonut from "@/components/charts/SentimentDonut";
import SentimentTimeline from "@/components/charts/SentimentTimeline";
import SentimentBadge from "@/components/SentimentBadge";
import { BarChart2 } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function SentimentPage() {
  let data: any = {};
  try { data = await api.sentiment(); } catch {}

  const overall = data.overall ?? {};
  const bySource = data.by_source ?? {};
  const overTime = data.over_time ?? {};

  const pct = overall.percentages ?? {};

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-sp-white">Sentiment Analysis</h1>
        <p className="text-sp-light-gray text-sm mt-1">How users feel about Spotify across all sources</p>
      </div>

      {/* Overall row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-sp-dark rounded-sp p-6 flex flex-col items-center">
          <p className="text-sp-light-gray text-xs font-semibold uppercase tracking-wider mb-4">Overall Split</p>
          <SentimentDonut
            positive={pct.positive ?? 0}
            neutral={pct.neutral ?? 0}
            negative={pct.negative ?? 0}
          />
          <p className="text-sp-light-gray text-xs mt-2">{overall.total?.toLocaleString() ?? 0} reviews</p>
        </div>

        {/* Stat boxes */}
        <div className="lg:col-span-2 grid grid-cols-3 gap-4 content-center">
          {[
            { label: "Positive", val: pct.positive, color: "text-sp-green",    count: overall.counts?.positive },
            { label: "Neutral",  val: pct.neutral,  color: "text-sp-light-gray",count: overall.counts?.neutral },
            { label: "Negative", val: pct.negative, color: "text-sp-negative",  count: overall.counts?.negative },
          ].map(({ label, val, color, count }) => (
            <div key={label} className="bg-sp-gray rounded-sp p-5 text-center">
              <p className={`text-4xl font-bold ${color}`}>{val ?? 0}%</p>
              <p className="text-sp-light-gray text-xs mt-1">{label}</p>
              <p className="text-sp-mid-gray text-xs">{count?.toLocaleString() ?? 0} reviews</p>
            </div>
          ))}
          <div className="col-span-3 bg-sp-gray rounded-sp p-5">
            <p className="text-sp-light-gray text-xs font-semibold uppercase tracking-wider mb-1">Avg Sentiment Score</p>
            <p className="text-3xl font-bold text-sp-white">{overall.avg_score?.toFixed(3) ?? "—"}</p>
            <p className="text-sp-mid-gray text-xs">0 = strongly negative · 1 = strongly positive</p>
          </div>
        </div>
      </div>

      {/* Timeline */}
      {Object.keys(overTime).length > 0 && (
        <div className="bg-sp-dark rounded-sp p-6">
          <h2 className="text-sp-white font-semibold mb-1 flex items-center gap-2">
            <BarChart2 size={16} className="text-sp-green" /> Sentiment Over Time
          </h2>
          <p className="text-sp-light-gray text-xs mb-4">Monthly trend by sentiment label</p>
          <SentimentTimeline overTime={overTime} />
        </div>
      )}

      {/* By source */}
      <div className="bg-sp-dark rounded-sp p-6">
        <h2 className="text-sp-white font-semibold mb-4">Sentiment by Source</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(bySource).map(([source, info]: [string, any]) => {
            const sp = info.percentages ?? {};
            return (
              <div key={source} className="bg-sp-gray rounded-sp p-4">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sp-white text-sm font-semibold capitalize">{source.replace(/_/g, " ")}</p>
                  <span className="text-sp-light-gray text-xs">{info.total} reviews</span>
                </div>
                <div className="flex h-2 rounded-full overflow-hidden gap-0.5">
                  <div style={{ width: `${sp.positive ?? 0}%` }} className="bg-sp-green rounded-l-full" />
                  <div style={{ width: `${sp.neutral ?? 0}%` }}  className="bg-sp-light-gray" />
                  <div style={{ width: `${sp.negative ?? 0}%` }} className="bg-sp-negative rounded-r-full" />
                </div>
                <div className="flex gap-4 mt-2">
                  {["positive", "neutral", "negative"].map((s) => (
                    <span key={s} className="text-xs text-sp-light-gray">
                      {sp[s] ?? 0}% {s}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
