import { api } from "@/lib/api";
import { TrendingUp, Users, Lightbulb, BarChart2, Clock } from "lucide-react";
import SentimentDonut from "@/components/charts/SentimentDonut";
import ThemeBar from "@/components/charts/ThemeBar";
import SourceBar from "@/components/charts/SourceBar";

export const dynamic = "force-dynamic";

function StatCard({ label, value, sub, icon: Icon, color = "#1DB954" }: {
  label: string; value: string | number; sub: string;
  icon: React.ElementType; color?: string;
}) {
  return (
    <div className="glass-card p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#555555" }}>{label}</p>
        <div className="w-8 h-8 rounded-sp-sm flex items-center justify-center" style={{ background: `${color}18` }}>
          <Icon size={16} style={{ color }} />
        </div>
      </div>
      <p className="text-3xl font-bold text-white">{value}</p>
      <p className="text-xs" style={{ color: "#999999" }}>{sub}</p>
    </div>
  );
}

export default async function OverviewPage() {
  let data: any = null;
  let error = false;
  try { data = await api.overview(); } catch { error = true; }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-80 gap-4">
        <div className="text-5xl">🎵</div>
        <h2 className="text-lg font-bold text-white">API not reachable</h2>
        <p className="text-sm text-center max-w-sm" style={{ color: "#999999" }}>
          Start the FastAPI server:<br />
          <code className="text-xs px-2 py-1 rounded mt-2 inline-block" style={{ color: "#1DB954", background: "#1c1c1c" }}>
            uvicorn dashboard.api.main:app --reload
          </code>
        </p>
      </div>
    );
  }

  const kpi = data.kpis ?? {};
  const themes = (data.top_themes ?? []).slice(0, 8);
  const insightsReady = data.insights_ready === true;
  const enrichPct: number = kpi.enrichment_pct ?? 0;
  const enrichComplete: boolean = kpi.enrichment_complete ?? false;

  return (
    <div className="space-y-6">

      {/* Enrichment progress */}
      {!enrichComplete && (
        <div className="glass-card p-4 flex items-center gap-4">
          <Clock size={16} style={{ color: "#1DB954" }} className="shrink-0 animate-pulse" />
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-medium text-white">
                AI enrichment in progress — {kpi.enriched_reviews?.toLocaleString()} / {kpi.total_reviews_analysed?.toLocaleString()}
              </p>
              <span className="text-sm font-bold" style={{ color: "#1DB954" }}>{enrichPct}%</span>
            </div>
            <div className="w-full rounded-full h-1.5" style={{ background: "#2a2a2a" }}>
              <div className="h-1.5 rounded-full transition-all" style={{ width: `${enrichPct}%`, background: "#1DB954" }} />
            </div>
          </div>
        </div>
      )}

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Relevant Reviews"    value={kpi.total_reviews_analysed?.toLocaleString() ?? "—"} sub={`${kpi.enriched_reviews?.toLocaleString()} enriched`} icon={BarChart2} color="#1DB954" />
        <StatCard label="Positive Sentiment"  value={insightsReady ? `${kpi.positive_pct ?? 0}%` : "—"} sub={insightsReady ? `Avg score ${kpi.avg_sentiment_score?.toFixed(2)}` : "Run aggregate"} icon={TrendingUp} color="#1DB954" />
        <StatCard label="Churn Risk Users"    value={insightsReady ? `${kpi.churn_risk_pct ?? 0}%` : "—"} sub={insightsReady ? `${kpi.churn_risk_count ?? 0} flagged` : "Run aggregate"} icon={Users} color="#E84040" />
        <StatCard label="Opportunities"       value={insightsReady ? kpi.product_opportunities ?? 0 : "—"} sub="AI-generated recommendations" icon={Lightbulb} color="#1DB954" />
      </div>

      {/* Not ready placeholder */}
      {!insightsReady && (
        <div className="glass-card p-12 flex flex-col items-center justify-center gap-4" style={{ borderStyle: "dashed" }}>
          <Clock size={32} style={{ color: "#555555" }} />
          <div className="text-center">
            <p className="font-semibold text-white mb-1">Insights not yet computed</p>
            <p className="text-sm mb-4" style={{ color: "#999999" }}>Run the pipeline to populate all charts</p>
            <div className="flex flex-col gap-2">
              {["cluster", "summarize", "aggregate"].map(cmd => (
                <code key={cmd} className="text-xs px-3 py-1.5 rounded" style={{ color: "#1DB954", background: "#1c1c1c" }}>
                  python -m src.pipeline {cmd}
                </code>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      {insightsReady && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="glass-card p-6">
            <p className="text-sm font-semibold text-white mb-1">Sentiment Split</p>
            <p className="text-xs mb-5" style={{ color: "#999999" }}>Overall distribution</p>
            <SentimentDonut
              positive={kpi.positive_pct ?? 0}
              neutral={kpi.neutral_pct ?? 0}
              negative={kpi.negative_pct ?? 0}
            />
          </div>
          <div className="lg:col-span-2 glass-card p-6">
            <p className="text-sm font-semibold text-white mb-1">Top Themes</p>
            <p className="text-xs mb-4" style={{ color: "#999999" }}>Most discussed topics</p>
            <ThemeBar data={themes} height={240} />
          </div>
        </div>
      )}

      {/* Source breakdown */}
      <div className="glass-card p-6">
        <p className="text-sm font-semibold text-white mb-1">Reviews by Source</p>
        <p className="text-xs mb-4" style={{ color: "#999999" }}>
          Filtered to on-topic reviews (algorithm · discovery · recommendations · mood · churn)
        </p>
        <SourceBar data={data.source_breakdown ?? {}} height={160} />
      </div>

      {/* Footer */}
      <p className="text-center text-xs pb-4" style={{ color: "#555555" }}>
        © 2026 ReviewAnalytics Platform. Powered by GPT-4o-mini.
      </p>
    </div>
  );
}
