import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import {
  Flame, Calendar, Battery, Heart,
  ArrowLeft, ChevronDown, ChevronUp, Zap,
} from 'lucide-react';
import ScoreRing from '../components/ScoreRing';
import StatCard from '../components/StatCard';
import FoodChip from '../components/FoodChip';

function parseScore(str) {
  if (typeof str === 'number') return str;
  const m = String(str).match(/(\d+\.?\d*)/);
  return m ? parseFloat(m[1]) : 0;
}

export default function Results() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [showDesc, setShowDesc] = useState(false);
  const [visible, setVisible] = useState(false);

  const result = state?.result;

  // Entrance animation trigger
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 30);
    return () => clearTimeout(t);
  }, []);

  // Save detected items to localStorage for Library page
  useEffect(() => {
    const segItems = result?.segmentation?.segmented_items;
    const detItems = result?.detections?.detections;
    const items = segItems || detItems;
    if (!items || items.length === 0) return;
    try {
      const existing = JSON.parse(localStorage.getItem('foodLibrary') || '[]');
      const newItems = items.map((d) => ({
        label: d.label,
        confidence: d.confidence,
        crop_url: d.crop_url || null,
        timestamp: Date.now(),
      }));
      localStorage.setItem('foodLibrary', JSON.stringify([...newItems, ...existing]));
    } catch {
      // silently fail
    }
  }, [result]);

  if (!result) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 px-4">
        <p className="text-text-muted">No results found.</p>
        <button
          onClick={() => navigate('/upload')}
          className="text-primary font-medium"
        >
          Go to Upload
        </button>
      </div>
    );
  }

  const API_BASE = 'http://localhost:8000';

  const analysis = result.analysis || {};
  const segmentation = result.segmentation;
  const segmentedItems = segmentation?.segmented_items || [];
  const detections = result.detections?.detections || [];
  const heroImage = segmentation?.visualization_url
    ? API_BASE + segmentation.visualization_url
    : result.detections?.result_image_url || null;

  const healthScore = parseScore(analysis.health_score);
  const satietyScore = parseScore(analysis.satiety_score);
  const bloatScore = parseScore(analysis.bloat_score);
  const tastyScore = parseScore(analysis.tasty_score);
  const addictionScore = parseScore(analysis.addiction_score);

  const baseTransition = 'transition-all duration-700 ease-out';
  const fadeUp = visible
    ? 'opacity-100 translate-y-0'
    : 'opacity-0 translate-y-6';

  return (
    <div className="flex flex-col pb-8">
      {/* Hero image with score overlay */}
      <div className={`relative w-full ${baseTransition} ${fadeUp}`}>
        {heroImage && (
          <img
            src={heroImage}
            alt="Analyzed meal"
            className="w-full aspect-[4/3] object-cover"
          />
        )}
        {/* Back button */}
        <button
          onClick={() => navigate('/upload')}
          className="absolute top-4 left-4 w-10 h-10 rounded-full bg-bg/70 backdrop-blur flex items-center justify-center active:scale-90 transition-transform"
        >
          <ArrowLeft size={20} className="text-text" />
        </button>
        {/* Mini score ring on hero */}
        <div className="absolute bottom-4 right-4 bg-bg/70 backdrop-blur rounded-full p-1">
          <div className="relative">
            <ScoreRing score={healthScore} size={56} strokeWidth={5} />
          </div>
        </div>
      </div>

      <div className="px-4 flex flex-col gap-5 mt-5">
        {/* Large score ring */}
        <div
          className={`flex flex-col items-center gap-2 ${baseTransition} ${fadeUp}`}
          style={{ transitionDelay: '100ms' }}
        >
          <div className="relative">
            <ScoreRing score={healthScore} size={140} strokeWidth={10} label="Health Score" />
          </div>
        </div>

        {/* Quick stats row */}
        <div
          className={`grid grid-cols-4 gap-2 ${baseTransition} ${fadeUp}`}
          style={{ transitionDelay: '200ms' }}
        >
          <StatCard
            icon={Flame}
            value={analysis.total_calories || '--'}
            label="Calories"
          />
          <StatCard
            icon={Calendar}
            value={analysis.eat_frequency || '--'}
            label="Frequency"
          />
          <StatCard
            icon={Battery}
            value={`${satietyScore}/10`}
            label="Satiety"
          />
          <StatCard
            icon={Heart}
            value={`${tastyScore}/10`}
            label="Tasty"
          />
        </div>

        {/* Sub-scores row */}
        <div
          className={`flex justify-around bg-card rounded-xl py-4 ${baseTransition} ${fadeUp}`}
          style={{ transitionDelay: '300ms' }}
        >
          <ScoreRing score={satietyScore} size={60} strokeWidth={5} label="Satiety" />
          <ScoreRing score={bloatScore} size={60} strokeWidth={5} label="Bloat" />
          <ScoreRing score={tastyScore} size={60} strokeWidth={5} label="Tasty" />
          <ScoreRing score={addictionScore} size={60} strokeWidth={5} label="Addiction" />
        </div>

        {/* Detected / Segmented items */}
        {(segmentedItems.length > 0 || detections.length > 0) && (
          <div
            className={`${baseTransition} ${fadeUp}`}
            style={{ transitionDelay: '400ms' }}
          >
            <h3 className="text-sm font-semibold text-text-muted mb-2 tracking-wide uppercase">
              Detected Items
            </h3>
            {segmentedItems.length > 0 ? (
              <div className="grid grid-cols-2 gap-3">
                {segmentedItems.map((item, i) => (
                  <div key={i} className="bg-card rounded-xl overflow-hidden">
                    {item.crop_url ? (
                      <img
                        src={API_BASE + item.crop_url}
                        alt={item.label}
                        className="w-full aspect-square object-cover"
                      />
                    ) : (
                      <div className="w-full aspect-square bg-card flex items-center justify-center">
                        <span className="text-text-muted text-xs">No image</span>
                      </div>
                    )}
                    <div className="px-3 py-2 flex items-center justify-between">
                      <span className="text-sm text-text font-medium capitalize truncate">
                        {item.label}
                      </span>
                      {item.confidence != null && (
                        <span className="text-[10px] bg-primary/20 text-primary font-semibold rounded-full px-2 py-0.5 shrink-0 ml-2">
                          {Math.round(item.confidence * 100)}%
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4">
                {detections.map((d, i) => (
                  <FoodChip key={i} label={d.label} confidence={d.confidence} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Description */}
        {analysis.description && (
          <div
            className={`bg-card rounded-xl p-4 ${baseTransition} ${fadeUp}`}
            style={{ transitionDelay: '500ms' }}
          >
            <button
              onClick={() => setShowDesc(!showDesc)}
              className="w-full flex items-center justify-between"
            >
              <span className="text-sm font-semibold text-text-muted uppercase tracking-wide">
                Description
              </span>
              {showDesc ? (
                <ChevronUp size={16} className="text-text-muted" />
              ) : (
                <ChevronDown size={16} className="text-text-muted" />
              )}
            </button>
            <p
              className={`text-sm text-text mt-2 leading-relaxed ${
                showDesc ? '' : 'line-clamp-3'
              }`}
            >
              {analysis.description}
            </p>
          </div>
        )}

        {/* Mood card */}
        {analysis.mood_impact && (
          <div
            className={`bg-card rounded-xl p-4 ${baseTransition} ${fadeUp}`}
            style={{ transitionDelay: '600ms' }}
          >
            <span className="text-sm font-semibold text-text-muted uppercase tracking-wide">
              Mood Impact
            </span>
            <p className="text-sm text-text mt-2 leading-relaxed">
              {analysis.mood_impact}
            </p>
          </div>
        )}

        {/* Upload another */}
        <div
          className={`flex justify-center mt-2 ${baseTransition} ${fadeUp}`}
          style={{ transitionDelay: '700ms' }}
        >
          <button
            onClick={() => navigate('/upload')}
            className="flex items-center justify-center gap-2 bg-primary text-white font-semibold text-base py-4 px-8 rounded-full shadow-lg shadow-primary/30 active:scale-95 active:bg-primary-dark transition-all"
            style={{ minHeight: '52px' }}
          >
            <Zap size={20} strokeWidth={2.5} />
            Upload Another
          </button>
        </div>
      </div>
    </div>
  );
}
