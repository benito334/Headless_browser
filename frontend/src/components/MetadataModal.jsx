import React from 'react';

export default function MetadataModal({ isOpen, onClose, jsonData }) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white max-w-2xl w-full p-4 rounded shadow-lg overflow-y-auto max-h-[90vh]">
        <h2 className="text-lg font-semibold mb-2">Metadata JSON</h2>
        <pre className="bg-gray-100 p-2 text-xs overflow-x-auto whitespace-pre-wrap">
          {JSON.stringify(jsonData, null, 2)}
        </pre>
        <button
          className="mt-4 px-3 py-1 bg-blue-500 text-white rounded"
          onClick={onClose}
        >
          Close
        </button>
      </div>
    </div>
  );
}
