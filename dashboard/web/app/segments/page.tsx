import { api } from "@/lib/api";
import SentimentDonut from "@/components/charts/SentimentDonut";
import { Users, AlertTriangle } from "lucide-react";

export const dynamic = "force-dynamic";

const SEGMENT_COLORS: Record<string, string> = {
  casual:      "bg-blue-500",
  power_user:  "bg-sp-green",
  new_user:    "bg-yellow-400",
  churn_risk:  "bg-sp-negative",
  unknown:     "bg-sp-mid-gray",
};
const SEGMENT_LABEL: Record<string, string> = {
  casual:     "Casual Listeners",
  power_user: "Power Users",
  new_user:   "New Users",
  churn_risk: "Churn Risk",
  unknown:    "Unknown",
};

export default async function SegmentsPage() {
  let data: any = {};
  try { data = await api.segments(); } catch {}

  const dist: any = data.distribution ?? {};
  const themes: any = data.themes_by_segment ?? {};
  const sentSeg: any = data.sentiment_by_segment ?? {};
  const churn: any = data.churn_signals ?? {};

  const total = Object.values(dist).reduce((s: number, v: any) => s + (v.count ?? 0), 0);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-sp-white">User Segments</h1>
        <p className="text-sp-light-gray text-sm mt-1">Who is talking and what they care about</p>
      </div>

      {/* Distribution */}
      <div className="bg-sp-dark rounded-sp p-6">
        <h2 className="text-sp-white font-semibold mb-5 flex items-center gap-2">
          <Users size={16} className="text-sp-green" /> Segment Distribution
        </h2>
        <div className="flex gap-1 h-6 rounded-full overflow-hidden mb-4">
          {Object.entries(dist)
            .filter(([k]) => k !== "unknown")
            .map(([seg, info]: [string, any]) => (
              <div
                key={seg}
                className={`${SEGMENT_COLORS[seg]} transition-all`}
                style={{ width: `${info.pct ?? 0}%` }}
                title={`${SEGMENT_LABEL[seg]}: ${info.pct}%`}
              />
            ))}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {Object.entries(dist).map(([seg, info]: [string, any]) => (
            <div key={seg} className="bg-sp-gray rounded-sp p-3 text-center">
              <div className={`w-3 h-3 rounded-full ${SEGMENT_COLORS[seg]} mx-auto mb-2`} />
              <p className="text-sp-white text-lg font-bold">{info.pct ?? 0}%</p>
              <p className="text-sp-light-gray text-xs capitalize">{SEGMENT_LABEL[seg]}</p>
              <p className="text-sp-mid-gray text-xs">{info.count} reviews</p>
            </div>
          ))}
        </div>
      </div>

      {/* Per-segment themes */}
      <div className="bg-sp-dark rounded-sp p-6">
        <h2 className="text-sp-white font-semibold mb-4">Top Themes by Segment</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(themes).map(([seg, themeList]: [string, any]) => (
            <div key={seg} className="bg-sp-gray rounded-sp p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className={`w-2 h-2 rounded-full ${SEGMENT_COLORS[seg]}`} />
                <p className="text-sp-white text-sm font-semibold">{SEGMENT_LABEL[seg] ?? seg}</p>
              </div>
              <div className="space-y-1.5">
                {themeList.slice(0, 5).map((t: any) => (
                  <div key={t.theme} className="flex items-center justify-between">
                    <span className="text-sp-light-gray text-xs capitalize">{t.theme.replace(/_/g, " ")}</span>
                    <span className="text-sp-mid-gray text-xs">{t.count}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Churn signals */}
      {churn.count > 0 && (
        <div className="bg-sp-negative/10 border border-sp-negative/30 rounded-sp p-6">
          <h2 className="text-sp-white font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle size={16} className="text-sp-negative" /> Churn Risk Signals
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-4xl font-bold text-sp-negative">{churn.count}</p>
              <p className="text-sp-light-gray text-sm">churn-risk reviews ({churn.pct_of_total}% of total)</p>
              <div className="mt-4 space-y-2">
                <p className="text-sp-light-gray text-xs font-semibold uppercase tracking-wider">Top Emotions</p>
                {Object.entries(churn.top_emotions ?? {}).slice(0, 4).map(([e, c]: [string, any]) => (
                  <div key={e} className="flex items-center justify-between">
                    <span className="text-sp-white text-sm capitalize">{e}</span>
                    <span className="text-sp-negative text-xs">{c} reviews</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sp-light-gray text-xs font-semibold uppercase tracking-wider mb-2">Churn-Risk Themes</p>
              <div className="space-y-1.5">
                {Object.entries(churn.top_themes ?? {}).slice(0, 6).map(([t, c]: [string, any]) => (
                  <div key={t} className="flex items-center gap-2">
                    <div className="flex-1 bg-sp-black/30 rounded-full h-1.5">
                      <div
                        className="bg-sp-negative h-1.5 rounded-full"
                        style={{ width: `${Math.min((c / churn.count) * 100, 100)}%` }}
                      />
                    </div>
                    <span className="text-sp-light-gray text-xs w-32 capitalize">{t.replace(/_/g, " ")}</span>
                    <span className="text-sp-mid-gray text-xs">{c}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
