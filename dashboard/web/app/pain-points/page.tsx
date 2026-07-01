import { api } from "@/lib/api";
import SentimentBadge from "@/components/SentimentBadge";
import { AlertTriangle, Lightbulb } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function PainPointsPage() {
  let data: any = {};
  try { data = await api.painPoints(); } catch {}

  const painPoints: any[] = data.ranked_pain_points ?? [];
  const featureRequests: any[] = data.ranked_feature_requests ?? [];

  const maxScore = painPoints[0]?.weighted_score ?? 1;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-sp-white">Pain Points & Feature Requests</h1>
        <p className="text-sp-light-gray text-sm mt-1">Ranked by frequency × negativity weight</p>
      </div>

      {/* Pain points */}
      <div className="bg-sp-dark rounded-sp p-6">
        <h2 className="text-sp-white font-semibold mb-1 flex items-center gap-2">
          <AlertTriangle size={16} className="text-sp-negative" /> Top Pain Points
        </h2>
        <p className="text-sp-light-gray text-xs mb-5">Weighted by sentiment severity</p>
        <div className="space-y-3">
          {painPoints.slice(0, 20).map((p: any, i: number) => (
            <div key={i} className="bg-sp-gray rounded-sp p-4 hover:bg-sp-gray/80 transition-colors">
              <div className="flex items-start justify-between gap-4 mb-2">
                <p className="text-sp-white text-sm flex-1 capitalize">{p.pain_point}</p>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-sp-light-gray text-xs">{p.mention_count} mentions</span>
                  <span className="text-sp-negative text-xs font-semibold">{p.negativity_rate}% neg</span>
                </div>
              </div>
              {/* Weight bar */}
              <div className="flex items-center gap-2 mt-2">
                <div className="flex-1 bg-sp-black/50 rounded-full h-1">
                  <div
                    className="bg-gradient-to-r from-sp-negative to-sp-negative/60 h-1 rounded-full"
                    style={{ width: `${(p.weighted_score / maxScore) * 100}%` }}
                  />
                </div>
                <span className="text-sp-mid-gray text-xs">score {p.weighted_score}</span>
              </div>
              {/* Source tags */}
              <div className="flex gap-1 mt-2">
                {Object.entries(p.sources ?? {}).map(([src, cnt]: [string, any]) => (
                  <span key={src} className="text-xs bg-sp-black/40 text-sp-light-gray px-2 py-0.5 rounded-full">
                    {src.replace(/_/g, " ")} {cnt}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Feature requests */}
      <div className="bg-sp-dark rounded-sp p-6">
        <h2 className="text-sp-white font-semibold mb-1 flex items-center gap-2">
          <Lightbulb size={16} className="text-sp-green" /> Feature Requests
        </h2>
        <p className="text-sp-light-gray text-xs mb-5">What users explicitly ask Spotify to build</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {featureRequests.slice(0, 16).map((f: any, i: number) => (
            <div key={i} className="bg-sp-gray rounded-sp p-4 hover:bg-sp-gray/80 transition-colors">
              <div className="flex items-start justify-between gap-2 mb-2">
                <p className="text-sp-white text-sm flex-1 capitalize">{f.feature_request}</p>
                <span className="bg-sp-green/20 text-sp-green text-xs font-bold px-2 py-0.5 rounded-full shrink-0">
                  ×{f.count}
                </span>
              </div>
              {f.top_themes?.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {f.top_themes.map((t: string) => (
                    <span key={t} className="text-xs bg-sp-black/40 text-sp-green/80 px-2 py-0.5 rounded-full capitalize">
                      #{t.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
