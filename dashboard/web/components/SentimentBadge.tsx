const MAP: Record<string, string> = {
  positive:    "bg-sp-green/20 text-sp-green",
  negative:    "bg-sp-negative/20 text-sp-negative",
  neutral:     "bg-sp-gray text-sp-light-gray",
  high:        "bg-sp-negative/20 text-sp-negative",
  medium:      "bg-yellow-500/20 text-yellow-400",
  low:         "bg-sp-green/20 text-sp-green",
};

export default function SentimentBadge({ value }: { value: string }) {
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold capitalize ${MAP[value] ?? "bg-sp-gray text-sp-light-gray"}`}>
      {value}
    </span>
  );
}
