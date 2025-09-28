import React from 'react';
import MetadataTable from './components/MetadataTable';

export default function App() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-semibold mb-4">Ingested Content</h1>
      <MetadataTable />
    </div>
  );
}
