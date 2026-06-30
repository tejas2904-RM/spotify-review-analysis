import { api } from "@/lib/api";
import ThemeBar from "@/components/charts/ThemeBar";
import SentimentBadge from "@/components/SentimentBadge";
import { Hash } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function ThemesPage() {
  let data: any = {};
  try { data = await api.themes(); } catch {}

  const topThemes: any[] = data.top_themes ?? [];
  const sentBreak: any = data.sentiment_breakdown ?? {};
  const bySource: any = data.by_source ?? {};
  const cooc: any[] = data.cooccurrence ?? [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-sp-white">Themes Explorer</h1>
        <p className="text-sp-light-gray text-sm mt-1">What users talk about most — and how they feel about it</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top themes bar */}
        <div className="bg-sp-dark rounded-sp p-6">
          <h2 className="text-sp-white font-semibold mb-1">Top Themes by Volume</h2>
          <p className="text-sp-light-gray text-xs mb-4">Total mentions across all 1,799 reviews</p>
          <ThemeBar data={topThemes.slice(0, 12)} height={320} />
        </div>

        {/* Theme sentiment table */}
        <div className="bg-sp-dark rounded-sp p-6">
          <h2 className="text-sp-white font-semibold mb-4">Theme × Sentiment</h2>
          <div className="space-y-2 overflow-y-auto max-h-80">
            {Object.entries(sentBreak)
              .sort((a: any, b: any) => b[1].total - a[1].total)
              .slice(0, 15)
              .map(([theme, info]: [string, any]) => (
                <div key={theme} className="flex items-center justify-between bg-sp-gray rounded-sp px-3 py-2">
                  <div className="flex items-center gap-2">
                    <Hash size={12} className="text-sp-green" />
                    <span className="text-sp-white text-sm capitalize">{theme.replace(/_/g, " ")}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sp-light-gray text-xs">{info.total} mentions</span>
                    <SentimentBadge value={info.dominant_sentiment} />
                    <span className="text-sp-negative text-xs w-12 text-right">{info.negativity_rate}% neg</span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Co-occurrence */}
      {cooc.length > 0 && (
        <div className="bg-sp-dark rounded-sp p-6">
          <h2 className="text-sp-white font-semibold mb-4">Theme Co-occurrence</h2>
          <p className="text-sp-light-gray text-xs mb-4">Theme pairs that appear together most often</p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {cooc.slice(0, 10).map((pair: any, i: number) => (
              <div key={i} className="bg-sp-gray rounded-sp p-3 text-center">
                <p className="text-sp-green text-xs font-semibold capitalize">{pair.theme_a.replace(/_/g, " ")}</p>
                <p className="text-sp-mid-gray text-xs my-1">+</p>
                <p className="text-sp-green text-xs font-semibold capitalize">{pair.theme_b.replace(/_/g, " ")}</p>
                <p className="text-sp-white text-lg font-bold mt-2">{pair.count}</p>
                <p className="text-sp-mid-gray text-xs">times</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* By source */}
      <div className="bg-sp-dark rounded-sp p-6">
        <h2 className="text-sp-white font-semibold mb-4">Themes by Source</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(bySource).map(([source, themes]: [string, any]) => (
            <div key={source}>
              <p className="text-sp-white text-sm font-semibold capitalize mb-2">{source.replace(/_/g, " ")}</p>
              <div className="space-y-1">
                {themes.slice(0, 6).map((t: any) => (
                  <div key={t.theme} className="flex items-center gap-2">
                    <div className="flex-1 bg-sp-gray rounded-full h-1.5">
                      <div className="bg-sp-green h-1.5 rounded-full" style={{ width: `${Math.min(t.pct_of_source, 100)}%` }} />
                    </div>
                    <span className="text-sp-light-gray text-xs w-28 truncate capitalize">{t.theme.replace(/_/g, " ")}</span>
                    <span className="text-sp-mid-gray text-xs w-10 text-right">{t.count}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
