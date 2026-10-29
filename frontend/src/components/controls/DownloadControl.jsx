import { BACKEND_URL } from '@/config';
// src/components/controls/DownloadControl.jsx

"use client";

import { FiDownload } from 'react-icons/fi';

export const DownloadControl = ({ dataset }) => {
  if (!dataset) {
    return null;
  }

  const handleDownload = () => {
    // Construct the full URL to the file
    const downloadUrl = `${BACKEND_URL}${dataset.url}`;
    
    // Create a temporary link element to trigger the download
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', dataset.filename); // This suggests a filename to the browser
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-4 border-b border-gray-200">
      <button
        onClick={handleDownload}
        className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md shadow-sm hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
      >
        <FiDownload className="w-4 h-4 mr-2" />
        Download Cleaned Data
      </button>
    </div>
  );
};