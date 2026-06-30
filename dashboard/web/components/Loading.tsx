export default function Loading({ text = "Loading…" }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
      <div className="w-10 h-10 border-4 border-sp-gray border-t-sp-green rounded-full animate-spin" />
      <p className="text-sp-light-gray text-sm">{text}</p>
    </div>
  );
}
