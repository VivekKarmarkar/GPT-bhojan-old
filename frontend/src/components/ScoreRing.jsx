import { useEffect, useState } from 'react';

function getColor(score) {
  if (score >= 7) return '#00C853';
  if (score >= 4) return '#FFD600';
  return '#FF1744';
}

export default function ScoreRing({ score, size = 120, label, strokeWidth = 8 }) {
  const [offset, setOffset] = useState(100);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const color = getColor(score);

  useEffect(() => {
    const timer = setTimeout(() => {
      setOffset(100 - (score / 10) * 100);
    }, 50);
    return () => clearTimeout(timer);
  }, [score]);

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="rotate-[-90deg]">
          {/* Background track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#2A2A44"
            strokeWidth={strokeWidth}
          />
          {/* Animated fill */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={(offset / 100) * circumference}
            style={{ transition: 'stroke-dashoffset 1s ease-out' }}
          />
        </svg>
        {/* Score number centered over the ring */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-bold" style={{ fontSize: size * 0.3, color }}>
            {score}
          </span>
          {size >= 80 && (
            <span className="text-text-muted" style={{ fontSize: size * 0.12 }}>
              /10
            </span>
          )}
        </div>
      </div>
      {label && (
        <span className="text-text-muted text-xs mt-1">{label}</span>
      )}
    </div>
  );
}
