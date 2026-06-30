const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { next: { revalidate: 30 } });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  overview:      () => get<any>("/api/overview"),
  sentiment:     () => get<any>("/api/sentiment"),
  themes:        () => get<any>("/api/themes"),
  painPoints:    () => get<any>("/api/pain-points"),
  segments:      () => get<any>("/api/segments"),
  summaries:     () => get<any>("/api/summaries"),
  opportunities: () => get<any>("/api/opportunities"),
};
