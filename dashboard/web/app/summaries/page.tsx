import { api } from "@/lib/api";
import { FileText, CheckCircle, Lightbulb } from "lucide-react";

export const dynamic = "force-dynamic";

function SummaryCard({ label, summary }: { label: string; summary: any }) {
  return (
    <div className="bg-sp-dark rounded-sp p-6 space-y-4">
      <div className="flex items-center gap-2">
        <FileText size={16} className="text-sp-green" />
        <h3 className="text-sp-white font-semibold capitalize">{label.replace(/_/g, " ")}</h3>
        {summary.review_count && (
          <span className="text-sp-mid-gray text-xs ml-auto">{summary.review_count} reviews</span>
        )}
      </div>
      {summary.summary && (
        <p className="text-sp-light-gray text-sm leading-relaxed">{summary.summary}</p>
      )}
      {summary.key_issues?.length > 0 && (
        <div>
          <p className="text-sp-white text-xs font-semibold uppercase tracking-wider mb-2">Key Issues</p>
          <ul className="space-y-1">
            {summary.key_issues.map((issue: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-sp-light-gray text-sm">
                <span className="text-sp-negative mt-0.5">•</span>
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}
      {summary.recommendations?.length > 0 && (
        <div>
          <p className="text-sp-white text-xs font-semibold uppercase tracking-wider mb-2">Recommendations</p>
          <ul className="space-y-1">
            {summary.recommendations.map((rec: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-sp-light-gray text-sm">
                <CheckCircle size={14} className="text-sp-green mt-0.5 shrink-0" />
                {rec}
              </li>
            ))}
          </ul>
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

  const hasThemes = Object.keys(themeSummaries).length > 0;
  const hasSources = Object.keys(sourceSummaries).length > 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-sp-white">AI Summaries</h1>
        <p className="text-sp-light-gray text-sm mt-1">LLM-generated insights per theme and source (Groq Llama 3.3 70B)</p>
      </div>

      {!hasThemes && !hasSources && (
        <div className="flex flex-col items-center justify-center h-64 gap-4 bg-sp-dark rounded-sp">
          <Lightbulb size={40} className="text-sp-mid-gray" />
          <p className="text-sp-light-gray text-sm">No summaries yet.</p>
          <code className="text-sp-green text-xs bg-sp-gray px-3 py-1.5 rounded">
            python -m src.pipeline summarize
          </code>
        </div>
      )}

      {hasThemes && (
        <section>
          <h2 className="text-sp-white font-semibold text-lg mb-4">By Theme</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Object.entries(themeSummaries).map(([theme, summary]: [string, any]) => (
              <SummaryCard key={theme} label={theme} summary={summary} />
            ))}
          </div>
        </section>
      )}

      {hasSources && (
        <section>
          <h2 className="text-sp-white font-semibold text-lg mb-4">By Source</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Object.entries(sourceSummaries).map(([source, summary]: [string, any]) => (
              <SummaryCard key={source} label={source} summary={summary} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
