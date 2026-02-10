import { useNavigate } from 'react-router-dom';
import { Camera, Zap, LayoutGrid, TrendingUp } from 'lucide-react';

const features = [
  {
    icon: Zap,
    title: 'AI Analysis',
    desc: 'Get health scores, calorie estimates, and more',
  },
  {
    icon: LayoutGrid,
    title: 'Food Library',
    desc: 'Build your personal food collection',
  },
  {
    icon: TrendingUp,
    title: 'Track Progress',
    desc: 'See your eating patterns over time',
  },
];

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="px-5 pt-12 pb-8 flex flex-col items-center">
      {/* Title */}
      <h1 className="text-3xl font-bold tracking-tight text-text">
        GPT Bhojan
      </h1>
      <p className="text-text-muted text-sm mt-1">Strava for Food</p>

      {/* Accent line */}
      <div className="mt-4 w-16 h-1 rounded-full bg-gradient-to-r from-primary to-primary-dark" />

      {/* CTA area */}
      <div className="mt-12 flex flex-col items-center">
        <button
          onClick={() => navigate('/upload')}
          className="relative group active:scale-95 transition-transform"
        >
          {/* Glow ring */}
          <div className="absolute inset-0 rounded-full bg-primary/20 blur-xl group-active:bg-primary/30 transition-colors" />
          <div className="relative w-28 h-28 rounded-full bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center shadow-lg shadow-primary/25">
            <Camera size={40} color="white" strokeWidth={2} />
          </div>
        </button>
        <h2 className="mt-6 text-lg font-semibold text-text">
          Analyze Your First Meal
        </h2>
        <p className="mt-2 text-sm text-text-muted text-center max-w-[260px] leading-relaxed">
          Take a photo and get instant AI-powered nutrition insights
        </p>
      </div>

      {/* Feature cards */}
      <div className="mt-14 w-full space-y-3">
        {features.map(({ icon: Icon, title, desc }) => (
          <div
            key={title}
            className="flex items-start gap-4 p-4 rounded-xl bg-card"
          >
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
              <Icon size={20} className="text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-text">{title}</p>
              <p className="text-xs text-text-muted mt-0.5 leading-relaxed">
                {desc}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
