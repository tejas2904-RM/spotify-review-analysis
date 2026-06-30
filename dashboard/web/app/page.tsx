import { api } from "@/lib/api";
import KPICard from "@/components/KPICard";
import SentimentDonut from "@/components/charts/SentimentDonut";
import ThemeBar from "@/components/charts/ThemeBar";
import SourceBar from "@/components/charts/SourceBar";
import { TrendingUp, Users, AlertTriangle, Lightbulb, BarChart2, Hash, Clock } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function OverviewPage() {
  let data: any = null;
  let error = false;
  try {
    data = await api.overview();
  } catch {
    error = true;
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <div className="text-6xl">🎵</div>
        <h2 className="text-xl font-bold text-sp-white">API not reachable</h2>
        <p className="text-sp-light-gray text-sm text-center max-w-sm">
          Start the FastAPI server first:<br />
          <code className="text-sp-green text-xs bg-sp-gray px-2 py-1 rounded mt-2 inline-block">
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
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-sp-white">Overview</h1>
        <p className="text-sp-light-gray text-sm mt-1">
          AI-powered analysis of <span className="text-sp-white font-semibold">{kpi.total_reviews_analysed?.toLocaleString()}</span> relevant Spotify user reviews
        </p>
      </div>

      {/* Enrichment progress banner — shown while enrichment is running */}
      {!enrichComplete && (
        <div className="bg-sp-gray rounded-sp p-4 flex items-center gap-4">
          <Clock size={18} className="text-sp-green shrink-0 animate-pulse" />
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sp-white text-sm font-medium">
                AI enrichment in progress — {kpi.enriched_reviews?.toLocaleString()} / {kpi.total_reviews_analysed?.toLocaleString()} reviews enriched
              </p>
              <span className="text-sp-green text-sm font-bold">{enrichPct}%</span>
            </div>
            <div className="w-full bg-sp-black/50 rounded-full h-1.5">
              <div
                className="bg-sp-green h-1.5 rounded-full transition-all"
                style={{ width: `${enrichPct}%` }}
              />
            </div>
            <p className="text-sp-mid-gray text-xs mt-1">
              Run <code className="text-sp-green">python -m src.pipeline aggregate</code> after enrichment completes to populate all insights.
            </p>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label="Relevant Reviews"
          value={kpi.total_reviews_analysed?.toLocaleString() ?? "—"}
          sub={`${kpi.enriched_reviews?.toLocaleString()} enriched (${enrichPct}%)`}
          icon={BarChart2}
          accent="neutral"
        />
        <KPICard
          label="Positive Sentiment"
          value={insightsReady ? `${kpi.positive_pct ?? 0}%` : "—"}
          sub={insightsReady ? `Avg score ${kpi.avg_sentiment_score?.toFixed(2) ?? "—"}` : "Run aggregate to populate"}
          icon={TrendingUp}
          accent={insightsReady ? "green" : "neutral"}
        />
        <KPICard
          label="Churn Risk Users"
          value={insightsReady ? `${kpi.churn_risk_pct ?? 0}%` : "—"}
          sub={insightsReady ? `${kpi.churn_risk_count} reviews flagged` : "Run aggregate to populate"}
          icon={Users}
          accent={insightsReady ? "red" : "neutral"}
        />
        <KPICard
          label="Opportunities"
          value={insightsReady ? kpi.product_opportunities ?? 0 : "—"}
          sub={insightsReady ? "Product recommendations" : "Run aggregate to populate"}
          icon={Lightbulb}
          accent={insightsReady ? "green" : "neutral"}
        />
      </div>

      {/* Insights pending placeholder */}
      {!insightsReady && (
        <div className="bg-sp-dark rounded-sp p-10 flex flex-col items-center justify-center gap-4 border border-sp-gray border-dashed">
          <Clock size={36} className="text-sp-mid-gray" />
          <div className="text-center">
            <p className="text-sp-white font-semibold mb-1">Insights not yet computed</p>
            <p className="text-sp-light-gray text-sm">
              Wait for enrichment to finish, then run:
            </p>
            <div className="flex flex-col gap-1 mt-3">
              <code className="text-sp-green text-xs bg-sp-gray px-3 py-1.5 rounded inline-block">
                python -m src.pipeline cluster
              </code>
              <code className="text-sp-green text-xs bg-sp-gray px-3 py-1.5 rounded inline-block">
                python -m src.pipeline summarize
              </code>
              <code className="text-sp-green text-xs bg-sp-gray px-3 py-1.5 rounded inline-block">
                python -m src.pipeline aggregate
              </code>
            </div>
          </div>
        </div>
      )}

      {/* Charts row — only show when insights are ready */}
      {insightsReady && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-sp-dark rounded-sp p-6">
              <h2 className="text-sp-white font-semibold mb-1 flex items-center gap-2">
                <BarChart2 size={16} className="text-sp-green" /> Sentiment Split
              </h2>
              <p className="text-sp-light-gray text-xs mb-4">Overall distribution</p>
              <SentimentDonut
                positive={kpi.positive_pct ?? 0}
                neutral={kpi.neutral_pct ?? 0}
                negative={kpi.negative_pct ?? 0}
              />
            </div>
            <div className="lg:col-span-2 bg-sp-dark rounded-sp p-6">
              <h2 className="text-sp-white font-semibold mb-1 flex items-center gap-2">
                <Hash size={16} className="text-sp-green" /> Top Themes
              </h2>
              <p className="text-sp-light-gray text-xs mb-4">Most mentioned topics</p>
              <ThemeBar data={themes} height={260} />
            </div>
          </div>
        </>
      )}

      {/* Source breakdown — always visible */}
      <div className="bg-sp-dark rounded-sp p-6">
        <h2 className="text-sp-white font-semibold mb-1 flex items-center gap-2">
          <AlertTriangle size={16} className="text-sp-green" /> Relevant Reviews by Source
        </h2>
        <p className="text-sp-light-gray text-xs mb-4">
          Filtered to on-topic reviews only (algorithm, discovery, recommendations, mood, churn)
        </p>
        <SourceBar data={data.source_breakdown ?? {}} height={180} />
      </div>
    </div>
  );
}
