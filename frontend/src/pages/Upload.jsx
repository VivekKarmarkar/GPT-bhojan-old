import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Camera, Zap, Loader2, AlertCircle, X } from 'lucide-react';
import { analyzeFood } from '../api';

const LOADING_STAGES = [
  'Analyzing food...',
  'Segmenting items...',
  'Building visualization...',
];

export default function Upload() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stageIndex, setStageIndex] = useState(0);
  const [error, setError] = useState(null);
  const stageIntervalRef = useRef(null);

  function handleFileChange(e) {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setError(null);
    const reader = new FileReader();
    reader.onload = (ev) => setPreview(ev.target.result);
    reader.readAsDataURL(selected);
  }

  function clearPhoto() {
    setFile(null);
    setPreview(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  async function handleAnalyze() {
    if (!file || loading) return;
    setLoading(true);
    setError(null);
    setStageIndex(0);

    stageIntervalRef.current = setInterval(() => {
      setStageIndex((prev) => (prev + 1) % LOADING_STAGES.length);
    }, 5000);

    try {
      const formData = new FormData();
      formData.append('file', file);
      const result = await analyzeFood(formData);
      clearInterval(stageIntervalRef.current);
      navigate('/results', { state: { result } });
    } catch (err) {
      clearInterval(stageIntervalRef.current);
      setLoading(false);
      setError(err.message || 'Analysis failed. Please try again.');
    }
  }

  return (
    <div className="flex flex-col items-center px-4 pt-6 pb-4 min-h-[calc(100vh-6rem)]">
      {/* Header */}
      <h1 className="text-lg font-semibold tracking-tight mb-4">
        Snap your meal
      </h1>

      {/* Camera viewfinder area */}
      <div className="relative w-full aspect-[3/4] max-h-[60vh] rounded-2xl overflow-hidden">
        {!preview ? (
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full h-full flex flex-col items-center justify-center gap-4 bg-surface border-2 border-dashed border-text-muted/30 rounded-2xl active:scale-[0.98] transition-transform cursor-pointer"
            style={{ minHeight: '44px' }}
          >
            <div className="w-24 h-24 rounded-full border-2 border-primary/60 flex items-center justify-center animate-pulse">
              <Camera size={40} className="text-primary" strokeWidth={1.5} />
            </div>
            <span className="text-text-muted text-sm">
              Tap to take or choose a photo
            </span>
          </button>
        ) : (
          <>
            <img
              src={preview}
              alt="Meal preview"
              className="w-full h-full object-cover rounded-2xl"
            />

            {/* Loading overlay */}
            {loading && (
              <div className="absolute inset-0 bg-bg/70 flex flex-col items-center justify-center gap-5 rounded-2xl">
                <Loader2
                  size={48}
                  className="text-primary animate-spin"
                  strokeWidth={2}
                />
                <p className="text-text text-base font-medium animate-pulse">
                  {LOADING_STAGES[stageIndex]}
                </p>
              </div>
            )}

            {/* Clear button (hidden while loading) */}
            {!loading && (
              <button
                onClick={clearPhoto}
                className="absolute top-3 right-3 w-9 h-9 rounded-full bg-bg/70 flex items-center justify-center active:scale-90 transition-transform"
              >
                <X size={18} className="text-text" />
              </button>
            )}
          </>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-4 w-full flex items-center gap-2 bg-danger/10 border border-danger/20 rounded-xl px-4 py-3">
          <AlertCircle size={18} className="text-danger shrink-0" />
          <span className="text-danger text-sm flex-1">{error}</span>
          <button
            onClick={handleAnalyze}
            className="text-sm text-primary font-medium ml-2 whitespace-nowrap"
          >
            Retry
          </button>
        </div>
      )}

      {/* Analyze button */}
      {preview && !loading && (
        <button
          onClick={handleAnalyze}
          className="mt-6 w-full max-w-xs flex items-center justify-center gap-2 bg-primary text-white font-semibold text-base py-4 rounded-full shadow-lg shadow-primary/30 active:scale-95 active:bg-primary-dark transition-all"
          style={{ minHeight: '52px' }}
        >
          <Zap size={20} strokeWidth={2.5} />
          Analyze My Meal
        </button>
      )}

      {/* Subtle hint when loading */}
      {loading && (
        <p className="mt-6 text-text-muted text-xs text-center">
          This takes about 20 seconds — sit tight!
        </p>
      )}
    </div>
  );
}
