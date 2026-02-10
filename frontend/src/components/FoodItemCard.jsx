import { Heart } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function FoodItemCard({ item, liked, onToggleLike }) {
  return (
    <div className="bg-card rounded-xl overflow-hidden flex flex-col">
      {/* Crop image or placeholder */}
      {item.crop_url ? (
        <img
          src={API_BASE + item.crop_url}
          alt={item.label}
          className="w-full aspect-square object-cover"
        />
      ) : (
        <div className="w-full aspect-square bg-white/5 flex items-center justify-center">
          <span className="text-text-muted text-xs capitalize">{item.label}</span>
        </div>
      )}

      <div className="p-4 flex flex-col gap-3">
        {/* Label + count */}
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-sm font-medium text-text leading-snug">
            {item.label}
          </h3>
          {item.count > 1 && (
            <span className="text-[10px] text-text-muted bg-white/5 px-1.5 py-0.5 rounded-full shrink-0">
              x{item.count}
            </span>
          )}
        </div>

        {/* Confidence badge + like */}
        <div className="flex items-center justify-between">
          {item.confidence != null && (
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-success/15 text-success">
              {Math.round(item.confidence * 100)}%
            </span>
          )}
          <button
            onClick={onToggleLike}
            className="ml-auto active:scale-90 transition-transform"
          >
            <Heart
              size={18}
              className={liked ? 'text-primary fill-primary' : 'text-text-muted'}
              strokeWidth={liked ? 0 : 1.5}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
