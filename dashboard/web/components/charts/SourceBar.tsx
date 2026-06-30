"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const SOURCE_COLORS: Record<string, string> = {
  google_play:       "#1DB954",
  youtube:           "#E9143D",
  hacker_news:       "#FF6600",
  spotify_community: "#1d72db",
};

interface Props {
  data: Record<string, number>;
  height?: number;
}

export default function SourceBar({ data, height = 200 }: Props) {
  const chartData = Object.entries(data)
    .filter(([k]) => k !== "total")
    .map(([source, count]) => ({
      source: source.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      count,
      key: source,
    }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
        <XAxis dataKey="source" tick={{ fill: "#B3B3B3", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "#B3B3B3", fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip
          cursor={{ fill: "rgba(255,255,255,0.04)" }}
          contentStyle={{ background: "#282828", border: "1px solid #535353", borderRadius: 8, color: "#fff" }}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {chartData.map((d, i) => (
            <Cell key={i} fill={SOURCE_COLORS[d.key] ?? "#535353"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
