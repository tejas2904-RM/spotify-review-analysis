"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface Props {
  data: { theme: string; count: number }[];
  height?: number;
}

export default function ThemeBar({ data, height = 280 }: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
        <XAxis type="number" tick={{ fill: "#B3B3B3", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="theme"
          tick={{ fill: "#B3B3B3", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={120}
          tickFormatter={(v: string) => v.replace(/_/g, " ")}
        />
        <Tooltip
          cursor={{ fill: "rgba(255,255,255,0.04)" }}
          contentStyle={{ background: "#282828", border: "1px solid #535353", borderRadius: 8, color: "#fff" }}
        />
        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={i === 0 ? "#1DB954" : i < 3 ? "#1ed760" : "#535353"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
