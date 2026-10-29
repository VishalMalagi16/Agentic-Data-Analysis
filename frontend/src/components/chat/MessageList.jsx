// frontend/components/chat/MessageList.jsx

"use client";

import { useEffect, useRef } from 'react';
import { FaUser, FaRobot } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export const MessageList = ({ messages, isLoading }) => {
  const endOfMessagesRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-grow p-6 overflow-y-auto">
      <div className="space-y-6">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex items-start gap-4 ${
              message.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {/* Agent Icon */}
            {message.sender === 'agent' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center">
                <FaRobot />
              </div>
            )}
            
            {/* Message Bubble */}
            <div
              className={`max-w-xl p-4 rounded-xl shadow-md ${
                message.sender === 'user'
                  ? 'bg-blue-600 text-white rounded-br-none'
                  : 'bg-white text-gray-800 rounded-bl-none border border-gray-200'
              }`}
            >
              {/* Use ReactMarkdown to render agent's response, which might contain markdown */}
              {message.sender === 'agent' ? (
                <div className="prose prose-sm max-w-none"> {/* Tailwind Typography for styling markdown */}
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.text}
                  </ReactMarkdown>
                </div>
              ) : (
                <p>{message.text}</p>
              )}
            </div>

            {/* User Icon */}
            {message.sender === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-600 text-white flex items-center justify-center">
                <FaUser />
              </div>
            )}
          </div>
        ))}
        
        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center">
              <FaRobot />
            </div>
            <div className="max-w-xl p-4 rounded-xl shadow-md bg-white border border-gray-200 rounded-bl-none">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse [animation-delay:0.2s]"></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse [animation-delay:0.4s]"></div>
              </div>
            </div>
          </div>
        )}

        {/* Dummy div to scroll to */}
        <div ref={endOfMessagesRef} />
      </div>
    </div>
  );
};