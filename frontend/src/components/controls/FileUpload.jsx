// frontend/components/controls/FileUpload.jsx

"use client";

import { useRef } from 'react';
import { FiFile, FiUploadCloud, FiX } from 'react-icons/fi';

export const FileUpload = ({ uploadedFile, onFileSelect }) => {
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) onFileSelect(file);
  };

  const onAreaClick = () => fileInputRef.current?.click();

  // --- THIS IS THE KEY CHANGE ---
  // If a file is uploaded, show a compact version.
  if (uploadedFile) {
    return (
      <div className="flex items-center justify-between w-full p-3 border border-gray-300 bg-white rounded-lg">
        <div className="flex items-center gap-3 overflow-hidden">
          <FiFile className="w-5 h-5 text-blue-600 shrink-0" />
          <p className="text-sm font-medium text-gray-800 truncate" title={uploadedFile.name}>
            {uploadedFile.name}
          </p>
        </div>
        <button
          onClick={() => onFileSelect(null)}
          className="p-1 text-gray-500 rounded-full hover:bg-red-100 hover:text-red-600 shrink-0"
          aria-label="Remove file"
        >
          <FiX className="w-5 h-5" />
        </button>
      </div>
    );
  }

  // Otherwise, show the large upload box.
  return (
    <>
      <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept=".csv" />
      <div
        onClick={onAreaClick}
        className="flex flex-col items-center justify-center w-full p-4 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
      >
        <FiUploadCloud className="w-8 h-8 text-gray-400 mb-2" />
        <p className="text-sm text-gray-500">
          <span className="font-semibold text-blue-600">Upload Dataset</span>
        </p>
        <p className="text-xs text-gray-400">CSV files only</p>
      </div>
    </>
  );
};