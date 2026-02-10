export default function StatCard({ icon: Icon, value, label }) {
  return (
    <div className="flex-1 flex flex-col items-center gap-2 bg-card rounded-xl py-3 px-2 min-w-0">
      <Icon size={20} className="text-primary shrink-0" strokeWidth={2} />
      <span className="text-text font-bold text-base truncate w-full text-center">
        {value}
      </span>
      <span className="text-text-muted text-[11px] truncate w-full text-center">
        {label}
      </span>
    </div>
  );
}
