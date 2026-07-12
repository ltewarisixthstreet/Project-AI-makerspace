/**
 * Financial Advisor AI - Main Application
 * Task 4: End-to-End Prototype
 *
 * This is the main Next.js app component that provides:
 * 1. Chat interface for financial questions
 * 2. User context form (salary, assets, goals)
 * 3. Session management
 * 4. Source citations & retrieval display
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

interface UserContext {
  salary?: number;
  assets?: number;
  debt?: number;
  timeline_years?: number;
  risk_tolerance?: string;
  goals?: string[];
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{
    source_label: string;
    file: string;
    page: number;
    relevance_score: number;
  }>;
  timestamp: string;
}

interface ChatResponse {
  session_id: string;
  user_message: string;
  assistant_response: string;
  sources: Array<any>;
  num_chunks_retrieved: number;
  retrieval_scores: number[];
  timestamp: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function FinancialAdvisorApp() {
  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userContext, setUserContext] = useState<UserContext>({});
  const [showContextForm, setShowContextForm] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize session on mount
  useEffect(() => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle user context submission
  const handleContextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowContextForm(false);
    // User context will be sent with each chat message
  };

  // Handle sending a message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputValue.trim()) return;

    // Add user message to chat
    const userMessage: Message = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Send to backend
      const response = await axios.post<ChatResponse>(`${API_BASE_URL}/chat`, {
        user_id: sessionId,
        message: inputValue,
        session_id: sessionId,
        user_context: userContext,
      });

      const data = response.data;

      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.assistant_response,
        sources: data.sources,
        timestamp: data.timestamp,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar: User Context */}
      <div className="w-80 bg-white shadow-lg p-6 overflow-y-auto border-r border-gray-200">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Financial Profile</h2>

        {showContextForm ? (
          <form onSubmit={handleContextSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Annual Salary ($)
              </label>
              <input
                type="number"
                placeholder="e.g., 150000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                onChange={(e) =>
                  setUserContext({ ...userContext, salary: parseFloat(e.target.value) })
                }
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current Assets ($)
              </label>
              <input
                type="number"
                placeholder="e.g., 500000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                onChange={(e) =>
                  setUserContext({ ...userContext, assets: parseFloat(e.target.value) })
                }
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Outstanding Debt ($)
              </label>
              <input
                type="number"
                placeholder="e.g., 100000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                onChange={(e) =>
                  setUserContext({ ...userContext, debt: parseFloat(e.target.value) })
                }
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Years to Retirement
              </label>
              <input
                type="number"
                placeholder="e.g., 25"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                onChange={(e) =>
                  setUserContext({ ...userContext, timeline_years: parseInt(e.target.value) })
                }
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Risk Tolerance
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                onChange={(e) =>
                  setUserContext({ ...userContext, risk_tolerance: e.target.value })
                }
              >
                <option value="">Select...</option>
                <option value="conservative">Conservative</option>
                <option value="moderate">Moderate</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 transition font-medium"
            >
              Start Conversation
            </button>
          </form>
        ) : (
          <div className="space-y-3 text-sm">
            <div className="bg-blue-50 p-3 rounded-md border border-blue-200">
              <p className="text-gray-600 text-xs uppercase font-semibold text-gray-500 mb-1">
                Your Profile
              </p>
              {userContext.salary && (
                <p className="text-gray-700">
                  💰 Salary: ${(userContext.salary / 1000).toFixed(0)}k
                </p>
              )}
              {userContext.assets && (
                <p className="text-gray-700">
                  📊 Assets: ${(userContext.assets / 1000).toFixed(0)}k
                </p>
              )}
              {userContext.timeline_years && (
                <p className="text-gray-700">⏰ Timeline: {userContext.timeline_years} years</p>
              )}
              {userContext.risk_tolerance && (
                <p className="text-gray-700">📈 Risk: {userContext.risk_tolerance}</p>
              )}
            </div>
            <button
              onClick={() => setShowContextForm(true)}
              className="w-full text-sm text-blue-600 hover:text-blue-700 py-2 border border-gray-300 rounded-md"
            >
              Update Profile
            </button>
          </div>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
          <h1 className="text-2xl font-bold text-gray-800">Financial Advisor AI</h1>
          <p className="text-gray-600 text-sm mt-1">
            Ask questions about investing, asset allocation, debt, tax strategy, and more.
          </p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && !showContextForm && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  Welcome to Your Financial Advisor
                </h2>
                <p className="text-gray-600 max-w-md">
                  Start by asking a question about your financial situation. I'll help you build a
                  decision framework grounded in financial principles.
                </p>
              </div>
            </div>
          )}

          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl px-4 py-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-gray-200 text-gray-800 rounded-bl-none'
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>

                {/* Sources for assistant messages */}
                {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                  <div className="mt-3 border-t border-gray-300 pt-2">
                    <p className="text-xs font-semibold text-gray-600 mb-2">Sources:</p>
                    {message.sources.map((source, sourceIdx) => (
                      <div key={sourceIdx} className="text-xs text-gray-600 mb-1">
                        <span className="font-semibold">{source.source_label}</span> -{' '}
                        {source.file}, page {source.page} (relevance: {source.relevance_score.toFixed(3)})
                      </div>
                    ))}
                  </div>
                )}

                <p className="text-xs mt-2 opacity-70">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-200 text-gray-800 px-4 py-3 rounded-lg rounded-bl-none">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 p-6">
          <form onSubmit={handleSendMessage} className="flex gap-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about asset allocation, taxes, debt, retirement, or other financial decisions..."
              disabled={isLoading || showContextForm}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
            />
            <button
              type="submit"
              disabled={isLoading || showContextForm || !inputValue.trim()}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition font-medium"
            >
              Send
            </button>
          </form>

          <p className="text-xs text-gray-500 mt-2">
            💡 Tip: Provide context about your situation for more personalized advice. This AI grounds
            recommendations in the Were-Talking-Millions financial guidance framework.
          </p>
        </div>
      </div>
    </div>
  );
}
