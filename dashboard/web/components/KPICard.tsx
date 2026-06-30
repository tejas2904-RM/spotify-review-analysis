import { LucideIcon } from "lucide-react";

interface Props {
  label: string;
  value: string | number;
  sub?: string;
  icon?: LucideIcon;
  accent?: "green" | "red" | "neutral";
}

const accentMap = {
  green:   "text-sp-green",
  red:     "text-sp-negative",
  neutral: "text-sp-light-gray",
};

export default function KPICard({ label, value, sub, icon: Icon, accent = "neutral" }: Props) {
  return (
    <div className="bg-sp-dark rounded-sp p-5 hover:bg-sp-gray transition-colors">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sp-light-gray text-xs font-semibold uppercase tracking-wider">{label}</p>
        {Icon && <Icon size={16} className="text-sp-mid-gray" />}
      </div>
      <p className={`text-3xl font-bold ${accentMap[accent]}`}>{value}</p>
      {sub && <p className="text-sp-light-gray text-xs mt-1">{sub}</p>}
    </div>
  );
}
