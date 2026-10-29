"use client";

import { useState, useEffect, useRef } from 'react';
import { AnalysisControls } from '@/components/controls/AnalysisControls';
import { Dashboard } from '@/components/dashboard/Dashboard';
import { DownloadControl } from '@/components/controls/DownloadControl';

export default function Home() {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([
    { sender: 'agent', text: 'Hello! Please upload a CSV dataset to begin analysis.' },
  ]);
  const [dashboardCards, setDashboardCards] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStatus, setCurrentStatus] = useState('');
  const [downloadableDataset, setDownloadableDataset] = useState(null);
  
  const eventSourceRef = useRef(null);

  const startAnalysisStream = (sid) => {
    if (eventSourceRef.current) eventSourceRef.current.close();
    
    const es = new EventSource(`http://127.0.0.1:8000/session/stream/${sid}`);
    eventSourceRef.current = es;

    es.onopen = () => {
      console.log("SSE connection opened for session:", sid);
      setCurrentStatus('Connection established. Waiting for agent...');
    };

    es.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.event) {
        case 'status_update':
          setCurrentStatus(data.data);
          break;
        case 'final_report':
          setMessages((prev) => [...prev, { sender: 'agent', text: data.data }]);
          
          if (data.artifacts) {
            // SOLUTION: Append new plots to existing ones instead of replacing
            if (data.artifacts.plots && data.artifacts.plots.length > 0) {
              const newCards = data.artifacts.plots.map(plotPath => ({
                  type: 'plot', title: 'Generated Plot', path: `/${plotPath}`
              }));
              setDashboardCards(prev => [...prev, ...newCards]);
            }
            if (data.artifacts.datasets && data.artifacts.datasets.length > 0) {
              setDownloadableDataset(data.artifacts.datasets[0]);
            }
          }
          break;
        case 'error':
           setMessages((prev) => [...prev, { sender: 'agent', text: `An error occurred: ${data.data}` }]);
           setIsLoading(false);
           es.close();
           break;
        case 'end':
          console.log("SSE stream ended by server.");
          setIsLoading(false);
          setCurrentStatus('');
          es.close();
          break;
      }
    };

    es.onerror = (err) => {
      console.error("EventSource failed:", err);
      setCurrentStatus('Connection lost. Please try again.');
      setIsLoading(false);
      es.close();
    };
  };

  // This function is no longer needed as we will handle state clearing manually
  // const clearStateForNewRun = () => { ... }

  const handleFileSelect = async (file) => {
    setUploadedFile(file);
    if (!file) {
      if (eventSourceRef.current) eventSourceRef.current.close();
      setSessionId(null);
      // Reset everything for a new session
      setMessages([{ sender: 'agent', text: 'Upload cancelled. Please upload a new dataset.' }]);
      setDashboardCards([]);
      setDownloadableDataset(null);
      return;
    }
    
    setIsLoading(true);
    setCurrentStatus(`Uploading "${file.name}"...`);
    // SOLUTION: Clear state ONLY when a new file is uploaded, creating a new session.
    setMessages([]);
    setDashboardCards([]);
    setDownloadableDataset(null);

    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://127.0.0.1:8000/session/start', { method: 'POST', body: formData });
      if (!response.ok) throw new Error("Failed to start session.");
      const result = await response.json();
      setSessionId(result.session_id);
      startAnalysisStream(result.session_id);
    } catch (error) {
      setMessages([{ sender: 'agent', text: `Error: Could not start analysis. ${error.message}` }]);
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (prompt) => {
    if (!sessionId) return;
    setMessages((prev) => [...prev, { sender: 'user', text: prompt }]);
    setIsLoading(true);
    setCurrentStatus('Sending prompt to agent...');
    // SOLUTION: Do NOT clear old messages or cards here.
    // We can clear the download link if we want new ones to replace it, or keep it. Let's keep it.
    // setDownloadableDataset(null); 
    
    try {
      const response = await fetch('http://127.0.0.1:8000/session/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, prompt: prompt }),
      });
      if (!response.ok) throw new Error("Failed to send prompt.");
      startAnalysisStream(sessionId);
    } catch (error) {
       setMessages((prev) => [...prev, { sender: 'agent', text: `Error: Could not send prompt. ${error.message}` }]);
       setIsLoading(false);
    }
  };

  useEffect(() => {
    return () => { if (eventSourceRef.current) eventSourceRef.current.close(); };
  }, []);

  return (
    <main className="flex h-screen bg-gray-100">
      <div className="w-1/3 max-w-md flex flex-col bg-white border-r border-gray-200">
        <AnalysisControls
          uploadedFile={uploadedFile}
          onFileSelect={handleFileSelect}
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          statusText={currentStatus}
        />
        <DownloadControl dataset={downloadableDataset} />
      </div>
      <div className="w-2/3 flex-1 flex flex-col overflow-y-auto">
        <Dashboard cards={dashboardCards} />
      </div>
    </main>
  );
}