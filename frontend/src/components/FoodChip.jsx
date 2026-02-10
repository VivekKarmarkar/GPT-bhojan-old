export default function FoodChip({ label, confidence }) {
  const pct = Math.round(confidence * 100);
  return (
    <div className="inline-flex items-center gap-2 bg-card border border-text-muted/20 rounded-full px-4 py-2 shrink-0">
      <span className="text-text text-sm font-medium capitalize">{label}</span>
      <span className="text-[10px] bg-primary/20 text-primary font-semibold rounded-full px-2 py-0.5">
        {pct}%
      </span>
    </div>
  );
}
