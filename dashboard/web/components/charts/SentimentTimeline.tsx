"use client";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from "recharts";

interface Props {
  overTime: Record<string, Record<string, number>>;
}

export default function SentimentTimeline({ overTime }: Props) {
  const data = Object.entries(overTime).map(([month, vals]) => ({
    month,
    Positive: vals.positive ?? 0,
    Neutral:  vals.neutral  ?? 0,
    Negative: vals.negative ?? 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#282828" />
        <XAxis dataKey="month" tick={{ fill: "#B3B3B3", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "#B3B3B3", fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={{ background: "#282828", border: "1px solid #535353", borderRadius: 8, color: "#fff" }} />
        <Legend formatter={(v) => <span style={{ color: "#B3B3B3", fontSize: 12 }}>{v}</span>} />
        <Line type="monotone" dataKey="Positive" stroke="#1DB954" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Neutral"  stroke="#B3B3B3" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Negative" stroke="#E9143D" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
