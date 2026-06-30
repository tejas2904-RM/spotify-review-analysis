"use client";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = ["#1DB954", "#B3B3B3", "#E9143D"];

interface Props {
  positive: number;
  neutral: number;
  negative: number;
}

export default function SentimentDonut({ positive, neutral, negative }: Props) {
  const data = [
    { name: "Positive", value: positive },
    { name: "Neutral",  value: neutral  },
    { name: "Negative", value: negative },
  ];

  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={65}
          outerRadius={100}
          paddingAngle={3}
          dataKey="value"
          strokeWidth={0}
        >
          {data.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
        </Pie>
        <Tooltip
          formatter={(v) => [`${v}%`, ""]}
          contentStyle={{ background: "#282828", border: "1px solid #535353", borderRadius: 8, color: "#fff" }}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(v) => <span style={{ color: "#B3B3B3", fontSize: 12 }}>{v}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
