/* Simple API client for frontend */
export async function getMetadata({ limit = 50, offset = 0, source_type = null } = {}) {
  const base = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
  const params = new URLSearchParams();
  if (limit) params.append('limit', limit);
  if (offset) params.append('offset', offset);
  if (source_type && source_type !== 'all') params.append('source_type', source_type);

  const url = `${base}/api/metadata?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to fetch metadata: ${res.status} ${text}`);
  }
  return res.json();
}
