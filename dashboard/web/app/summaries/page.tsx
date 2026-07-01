import { api } from "@/lib/api";
import {
  Navigation, Zap, Sparkles, Headphones, DollarSign, Smartphone,
  RefreshCw, FileText,
} from "lucide-react";

export const dynamic = "force-dynamic";

const SEVERITY: Record<string, { label: string; color: string; bg: string }> = {
  critical:      { label: "CRITICAL",      color: "#E84040", bg: "#E8404018" },
  moderate:      { label: "MODERATE",      color: "#999999", bg: "#22222288" },
  positive:      { label: "HIGH POSITIVE", color: "#1DB954", bg: "#1DB95418" },
  high_positive: { label: "HIGH POSITIVE", color: "#1DB954", bg: "#1DB95418" },
  neutral:       { label: "NEUTRAL",       color: "#F59E0B", bg: "#F59E0B18" },
  attention:     { label: "ATTENTION",     color: "#F59E0B", bg: "#F59E0B18" },
};

const ICONS = [Navigation, Zap, Sparkles, Headphones, DollarSign, Smartphone, FileText];

function getSeverityTag(summary: any): string {
  const s = (summary.summary ?? "").toLowerCase();
  if (s.includes("critical") || s.includes("major issue") || s.includes("urgent")) return "critical";
  if (s.includes("positive") || s.includes("excellent") || s.includes("great")) return "positive";
  return "moderate";
}

function SummaryCard({ label, summary, index }: { label: string; summary: any; index: number }) {
  const sev = getSeverityTag(summary);
  const badge = SEVERITY[sev] ?? SEVERITY.moderate;
  const Icon = ICONS[index % ICONS.length];
  const tags: string[] = summary.key_issues?.slice(0, 3) ?? [];

  return (
    <div className="glass-card p-5 flex flex-col gap-3 hover:border-[#3a3a3a] transition-colors"
         style={{ borderTop: `2px solid ${badge.color}` }}>
      <div className="flex items-start justify-between">
        <div className="w-9 h-9 rounded-sp-sm flex items-center justify-center shrink-0"
             style={{ background: "#1DB95418" }}>
          <Icon size={17} style={{ color: "#1DB954" }} />
        </div>
        <span className="text-xs font-bold px-2 py-0.5 rounded"
              style={{ background: badge.bg, color: badge.color }}>
          {badge.label}
        </span>
      </div>
      <div>
        <h3 className="text-sm font-bold text-white capitalize leading-snug">
          {label.replace(/_/g, " ")}
        </h3>
        {summary.review_count && (
          <p className="text-xs mt-0.5" style={{ color: "#555555" }}>
            Based on {summary.review_count} reviews
          </p>
        )}
      </div>
      {summary.summary && (
        <p className="text-xs leading-relaxed line-clamp-4" style={{ color: "#999999" }}>
          {summary.summary}
        </p>
      )}
      {summary.recommendations?.[0] && (
        <p className="text-xs">
          <span className="font-semibold" style={{ color: "#1DB954" }}>Actionable: </span>
          <span style={{ color: "#999999" }}>{summary.recommendations[0]}</span>
        </p>
      )}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-2" style={{ borderTop: "1px solid #2a2a2a" }}>
          {tags.map((t: string) => (
            <span key={t} className="text-xs px-2 py-0.5 rounded-full"
                  style={{ background: "#1c1c1c", color: "#999999", border: "1px solid #2a2a2a" }}>
              #{t.replace(/[: ]+/g, "_").toLowerCase().slice(0, 20)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default async function SummariesPage() {
  let data: any = {};
  try { data = await api.summaries(); } catch {}

  const themeSummaries: any = data.theme_summaries ?? {};
  const sourceSummaries: any = data.source_summaries ?? {};

  const hasThemes  = Object.keys(themeSummaries).length > 0;
  const hasSources = Object.keys(sourceSummaries).length > 0;

  return (
    <div className="space-y-6">

      {/* Tab-like section headers */}
      {(hasThemes || hasSources) && (
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <button className="px-4 py-1.5 rounded-full text-sm font-semibold transition-colors"
                    style={{ background: "#1DB954", color: "#000" }}>
              By Theme
            </button>
            <button className="px-4 py-1.5 rounded-full text-sm font-medium transition-colors hover:bg-[#222222]"
                    style={{ color: "#999999", border: "1px solid #2a2a2a" }}>
              By Source
            </button>
          </div>
          <button className="flex items-center gap-1.5 text-xs font-medium transition-opacity hover:opacity-70"
                  style={{ color: "#1DB954" }}>
            <RefreshCw size={12} /> Refresh Data
          </button>
        </div>
      )}

      {!hasThemes && !hasSources && (
        <div className="glass-card p-16 flex flex-col items-center justify-center gap-4">
          <FileText size={36} style={{ color: "#555555" }} />
          <p className="font-semibold text-white">No summaries yet</p>
          <p className="text-sm text-center" style={{ color: "#999999" }}>
            Run the summarize pipeline step to generate AI insights
          </p>
          <code className="text-xs px-3 py-1.5 rounded" style={{ color: "#1DB954", background: "#1c1c1c" }}>
            python -m src.pipeline summarize
          </code>
        </div>
      )}

      {hasThemes && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(themeSummaries).map(([theme, summary]: [string, any], i: number) => (
            <SummaryCard key={theme} label={theme} summary={summary} index={i} />
          ))}
        </div>
      )}

      {hasSources && (
        <section className="space-y-3">
          <p className="text-sm font-semibold text-white">By Source</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(sourceSummaries).map(([source, summary]: [string, any], i: number) => (
              <SummaryCard key={source} label={source} summary={summary} index={i + 10} />
            ))}
          </div>
        </section>
      )}

      <p className="text-center text-xs pb-4" style={{ color: "#555555" }}>
        © 2026 ReviewAnalytics Platform. All data real-time via API.
      </p>
    </div>
  );
}
