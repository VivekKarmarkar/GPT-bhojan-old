import { useLocation, useNavigate } from 'react-router-dom';
import { Home, Camera, LayoutGrid } from 'lucide-react';

const tabs = [
  { path: '/', icon: Home, label: 'Home' },
  { path: '/upload', icon: Camera, label: 'Upload', isCenter: true },
  { path: '/library', icon: LayoutGrid, label: 'Library' },
];

export default function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  // Hide nav on results page
  if (location.pathname === '/results') return null;

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-surface border-t border-white/5 pb-[env(safe-area-inset-bottom)]">
      <div className="flex items-end justify-around px-4 py-2 max-w-md mx-auto">
        {tabs.map(({ path, icon: Icon, label, isCenter }) => {
          const active = location.pathname === path;

          if (isCenter) {
            return (
              <button
                key={path}
                onClick={() => navigate(path)}
                className="flex flex-col items-center -mt-5"
              >
                <div className="w-14 h-14 rounded-full bg-primary flex items-center justify-center shadow-lg shadow-primary/30 active:scale-95 transition-transform">
                  <Icon size={26} color="white" strokeWidth={2.5} />
                </div>
                <span className="text-[10px] mt-1 text-primary font-medium">{label}</span>
              </button>
            );
          }

          return (
            <button
              key={path}
              onClick={() => navigate(path)}
              className="flex flex-col items-center py-1 px-3"
            >
              <Icon
                size={22}
                className={active ? 'text-primary' : 'text-text-muted'}
                strokeWidth={active ? 2.5 : 1.5}
              />
              <span className={`text-[10px] mt-1 ${active ? 'text-primary font-medium' : 'text-text-muted'}`}>
                {label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
