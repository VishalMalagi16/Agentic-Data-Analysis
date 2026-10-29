// frontend/components/controls/AnalysisControls.jsx

import { FileUpload } from './FileUpload';
import { MessageList } from '../chat/MessageList';
import { InputBar } from '../chat/InputBar';

// NEW: A simple component to show the status
const StatusIndicator = ({ status }) => (
  <div className="px-4 py-2 text-sm text-center text-gray-600 bg-gray-100">
    <div className="flex items-center justify-center gap-2">
      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
      <span>{status}</span>
    </div>
  </div>
);


export const AnalysisControls = (props) => {
  const { 
    uploadedFile, 
    onFileSelect, 
    messages, 
    onSendMessage, 
    isLoading,
    statusText // <-- NEW PROP
  } = props;

  const isChatDisabled = isLoading || !uploadedFile;
  const placeholderText = !uploadedFile 
    ? "Upload a dataset to enable chat"
    : "Ask for insights...";

  return (
    <>
      <header className="p-4 border-b border-gray-200 shrink-0">
        <h1 className="text-xl font-bold text-gray-800">Agentic Analysis</h1>
        <p className='text-m font-light text-gray-600'>how it works ?</p>
      </header>
      
      <div className="p-4 border-b border-gray-200 shrink-0">
        <FileUpload uploadedFile={uploadedFile} onFileSelect={onFileSelect} />
      </div>
      
      <div className="flex-grow flex flex-col bg-gray-50 overflow-hidden">
        <MessageList messages={messages} isLoading={isLoading && !statusText} />
        
        {/* Show status indicator when loading */}
        {isLoading && statusText && <StatusIndicator status={statusText} />}
        
        <InputBar
          onSendMessage={onSendMessage}
          isLoading={isChatDisabled}
          placeholder={placeholderText}
        />
      </div>
    </>
  );
};