import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, LayoutGrid, Camera } from 'lucide-react';
import FoodItemCard from '../components/FoodItemCard';

const ITEMS_KEY = 'foodLibrary';
const LIKES_KEY = 'bhojan_liked_items';

function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export default function Library() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [likes, setLikes] = useState({});
  const [query, setQuery] = useState('');

  useEffect(() => {
    setItems(readJson(ITEMS_KEY, []));
    setLikes(readJson(LIKES_KEY, {}));
  }, []);

  const filtered = useMemo(() => {
    if (!query.trim()) return items;
    const q = query.toLowerCase();
    return items.filter((it) => it.label?.toLowerCase().includes(q));
  }, [items, query]);

  function toggleLike(id) {
    setLikes((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      localStorage.setItem(LIKES_KEY, JSON.stringify(next));
      return next;
    });
  }

  // Empty state
  if (items.length === 0) {
    return (
      <div className="px-5 pt-12 pb-8 flex flex-col items-center">
        <h1 className="text-xl font-bold text-text">Food Library</h1>
        <div className="mt-16 flex flex-col items-center">
          <div className="w-16 h-16 rounded-full bg-card flex items-center justify-center">
            <LayoutGrid size={28} className="text-text-muted" />
          </div>
          <p className="mt-5 text-base font-medium text-text">
            No food items yet
          </p>
          <p className="mt-2 text-sm text-text-muted text-center max-w-[240px] leading-relaxed">
            Upload your first meal to start building your library
          </p>
          <button
            onClick={() => navigate('/upload')}
            className="mt-8 flex items-center gap-2 px-6 py-3 rounded-full bg-primary text-white text-sm font-medium active:scale-95 transition-transform shadow-lg shadow-primary/25"
          >
            <Camera size={18} />
            Upload a Meal
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="px-5 pt-8 pb-8">
      <h1 className="text-xl font-bold text-text">Food Library</h1>

      {/* Search bar */}
      <div className="mt-4 relative">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted"
        />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search items..."
          className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-card text-sm text-text placeholder:text-text-muted outline-none border border-white/5 focus:border-primary/40 transition-colors"
        />
      </div>

      {/* Grid */}
      <div className="mt-5 grid grid-cols-2 gap-3">
        {filtered.map((item) => (
          <FoodItemCard
            key={item.id ?? item.label}
            item={item}
            liked={!!likes[item.id ?? item.label]}
            onToggleLike={() => toggleLike(item.id ?? item.label)}
          />
        ))}
      </div>

      {filtered.length === 0 && query.trim() && (
        <p className="mt-8 text-center text-sm text-text-muted">
          No items matching "{query}"
        </p>
      )}
    </div>
  );
}
