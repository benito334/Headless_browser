import React, { useState, useEffect, useCallback } from 'react';
import { getMetadata } from '../api/client';

const sourceOptions = [
  { value: 'all', label: 'All' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'youtube', label: 'YouTube' },
  { value: 'pdf', label: 'PDF' },
  { value: 'epub', label: 'EPUB' },
];

const limits = [25, 50, 100];

function truncateMiddle(text, max = 40) {
  if (text.length <= max) return text;
  const half = Math.floor(max / 2);
  return `${text.slice(0, half)}…${text.slice(-half)}`;
}

import MetadataModal from './MetadataModal';

export default function MetadataTable() {
  const [records, setRecords] = useState([]);
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [sourceType, setSourceType] = useState('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalData, setModalData] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMetadata({ limit, offset, source_type: sourceType });
      setRecords(data.records || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [limit, offset, sourceType]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const nextPage = () => setOffset(offset + limit);
  const prevPage = () => setOffset(Math.max(0, offset - limit));

  return (
    <div className="mt-6">
      <div className="flex flex-wrap gap-4 items-end mb-4">
        <label>
          Source:
          <select
            className="ml-2 border p-1"
            value={sourceType}
            onChange={(e) => {
              setOffset(0);
              setSourceType(e.target.value);
            }}
          >
            {sourceOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Limit:
          <select
            className="ml-2 border p-1"
            value={limit}
            onChange={(e) => {
              setOffset(0);
              setLimit(parseInt(e.target.value, 10));
            }}
          >
            {limits.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </label>

        <button
          className="border px-3 py-1 rounded bg-blue-500 text-white"
          onClick={fetchData}
          disabled={loading}
        >
          {loading ? 'Loading…' : 'Refresh'}
        </button>

        {error && (
          <div className="text-red-500 ml-4">Error: {error}</div>
        )}
      </div>

      {records.length === 0 && !loading ? (
        <div>No records yet.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm border">
            <thead className="bg-gray-100">
              <tr>
                <th className="p-2 border">Ingest Date</th>
                <th className="p-2 border">Source</th>
                <th className="p-2 border">Author</th>
                <th className="p-2 border">Original URL</th>
                <th className="p-2 border">File Path</th>
                <th className="p-2 border">Publish Date</th>
                <th className="p-2 border">Length (s)</th>
                <th className="p-2 border">Notes</th>
                <th className="p-2 border">Actions</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="p-2 border whitespace-nowrap">{r.ingest_date}</td>
                  <td className="p-2 border">{r.source_type}</td>
                  <td className="p-2 border">{r.author}</td>
                  <td className="p-2 border text-blue-600 underline">
                    <a href={r.original_url} target="_blank" rel="noreferrer">
                      link
                    </a>
                  </td>
                  <td className="p-2 border" title={r.file_path}>
                    {truncateMiddle(r.file_path)}
                  </td>
                  <td className="p-2 border">{r.publish_date || '-'}</td>
                  <td className="p-2 border text-right">{r.length_seconds ?? '-'}</td>
                  <td className="p-2 border">{r.notes || ''}</td>
                  <td className="p-2 border text-center space-x-2">
                    {/* Download button */}
                    <a
                      href={r.file_path.replace(/.*data[\\/]/, '/static/').replace(/\\/g, '/')}
                      target="_blank"
                      rel="noreferrer"
                      title="Download file"
                      className="text-green-600 hover:underline"
                    >
                      ⬇
                    </a>
                    {/* View JSON */}
                    <button
                      title="View JSON metadata"
                      onClick={async () => {
                        try {
                          const jsonUrl = r.file_path.replace(/\.\w+$/, '.json').replace(/.*data[\\/]/, '/static/').replace(/\\/g, '/');
                          const base = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
                          const res = await fetch(base + jsonUrl);
                          if (!res.ok) throw new Error('Failed to fetch sidecar');
                          const jd = await res.json();
                          setModalData(jd);
                          setModalOpen(true);
                        } catch (e) {
                          alert(e.message);
                        }
                      }}
                    >
                      ℹ
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <MetadataModal isOpen={modalOpen} onClose={() => setModalOpen(false)} jsonData={modalData} />
      )}

      <div className="flex justify-between mt-4">
        <button
          onClick={prevPage}
          disabled={offset === 0}
          className="border px-3 py-1 rounded disabled:opacity-50"
        >
          Prev
        </button>
        <button
          onClick={nextPage}
          disabled={records.length < limit}
          className="border px-3 py-1 rounded disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}
