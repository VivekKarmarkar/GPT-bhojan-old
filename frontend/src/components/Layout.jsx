import BottomNav from './BottomNav';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-bg text-text">
      <main className="pb-24 max-w-md mx-auto">
        {children}
      </main>
      <BottomNav />
    </div>
  );
}
