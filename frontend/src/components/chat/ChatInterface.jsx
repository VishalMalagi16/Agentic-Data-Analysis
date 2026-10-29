// frontend/components/chat/ChatInterface.jsx

"use client";

import { useState } from 'react';
import { MessageList } from './MessageList';
import { InputBar } from './InputBar';
// frontend/components/chat/ChatInterface.jsx

import { FileUpload } from '../controls/FileUpload'; // Import the new component

export const ChatInterface = () => {
  const [uploadedFile, setUploadedFile] = useState(null); // State for the uploaded file
  const [messages, setMessages] = useState([
    {
      sender: 'agent',
      text: 'Hello! Please upload a dataset to begin your analysis.',
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);

  // This function will be passed to the FileUpload component
  const handleFileSelect = (file) => {
    setUploadedFile(file);
    if(file) {
      // Add a message to the chat confirming the upload
      setMessages(prev => [...prev, {
        sender: 'agent',
        text: `Successfully uploaded **${file.name}**. You may now ask questions about your data.`
      }]);
    }
  };

  const handleSendMessage = async (prompt) => {
    // Prevent sending a message if no file is uploaded
    if (!uploadedFile) {
        alert("Please upload a dataset before sending a message.");
        return;
    }

    setMessages((prevMessages) => [
      ...prevMessages,
      { sender: 'user', text: prompt },
    ]);
    
    setIsLoading(true);

    const formData = new FormData();
    formData.append('file', uploadedFile); // Use the actual file from state
    formData.append('prompt', prompt);

    try {
      const response = await fetch('http://127.0.0.1:8000/analyze/agent', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }
      
      const agentResponse = await response.json(); // Use the REAL response now
      
      // The agent's final response should be in a field like 'final_report' or similar
      const reportText = agentResponse.final_report || agentResponse.error || "I received a response, but it was not in the expected format.";

      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'agent', text: reportText },
      ]);

    } catch (error) {
      console.error("Error calling analysis API:", error);
      const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'agent', text: `Sorry, I ran into an error: ${errorMessage}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Determine if the chat input should be disabled
  const isChatDisabled = isLoading || !uploadedFile;
  const placeholderText = !uploadedFile 
    ? "Please upload a dataset to enable chat"
    : "Ask for insights from your data...";

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="p-4 bg-white border-b border-gray-200 shadow-sm shrink-0">
        <h1 className="text-xl font-bold text-gray-800">Agentic Analysis Chat</h1>
      </header>

      <div className="flex-grow flex flex-col overflow-hidden">
        {/* File Upload Area */}
        <div className="shrink-0">
            <FileUpload uploadedFile={uploadedFile} onFileSelect={handleFileSelect} />
        </div>
        
        {/* Chat Area */}
        <div className="flex-grow flex flex-col bg-gray-50 overflow-hidden">
            <MessageList messages={messages} isLoading={isLoading} />
            <InputBar 
                onSendMessage={handleSendMessage} 
                isLoading={isChatDisabled} 
                placeholder={placeholderText} 
            />
        </div>
      </div>
    </div>
  );
};