const API_BASE = 'http://localhost:8000';

export async function analyzeFood(formData) {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Analysis failed: ${res.status}`);
  return res.json();
}

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}
