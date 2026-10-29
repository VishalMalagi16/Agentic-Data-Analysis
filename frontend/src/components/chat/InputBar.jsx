// frontend/components/chat/InputBar.jsx

"use client";

import { useState } from 'react';
import { IoSend } from 'react-icons/io5';

// Make the component accept a placeholder prop
export const InputBar = ({ onSendMessage, isLoading, placeholder }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  return (
    <div className="p-4 bg-white border-t border-gray-200">
      <form onSubmit={handleSubmit} className="flex items-center space-x-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          // Use the placeholder prop here
          placeholder={isLoading ? "Agent is thinking..." : placeholder}
          disabled={isLoading}
          className="flex-grow px-4 py-2 text-gray-700 bg-gray-100 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="flex-shrink-0 p-3 text-white bg-blue-600 rounded-full hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          <IoSend size={20} />
        </button>
      </form>
    </div>
  );
};