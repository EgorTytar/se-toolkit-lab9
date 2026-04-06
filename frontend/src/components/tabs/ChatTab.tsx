import { useEffect, useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAuth } from '../../contexts/AuthContext';
import { chatApi } from '../../services/api';
import type { ChatSession, ChatMessage } from '../../types/api';
import { Link } from 'react-router-dom';

export default function ChatTab() {
  const { isAuthenticated } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  // Persist pending sessions to localStorage so they survive page reloads
  const [pendingSessions, setPendingSessions] = useState<Set<number>>(() => {
    try {
      const stored = localStorage.getItem('f1_pending_sessions');
      if (stored) {
        return new Set(JSON.parse(stored));
      }
    } catch {}
    return new Set();
  });
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  // Ref to track current active session (not stale in closures)
  const activeSessionRef = useRef<number | null>(null);
  // Ref for polling to avoid re-render loops
  const pendingRef = useRef<Set<number>>(new Set());

  const isSessionTyping = activeSession !== null && pendingSessions.has(activeSession);

  useEffect(() => {
    if (isAuthenticated) {
      loadSessions();
    }
  }, [isAuthenticated]);

  // Keep refs in sync with state
  useEffect(() => {
    activeSessionRef.current = activeSession;
  }, [activeSession]);

  useEffect(() => {
    pendingRef.current = pendingSessions;
    // Persist to localStorage so they survive page reloads
    try {
      localStorage.setItem('f1_pending_sessions', JSON.stringify([...pendingSessions]));
    } catch {}
  }, [pendingSessions]);

  // Poll pending sessions every 1 second to check if AI has responded
  useEffect(() => {
    if (!isAuthenticated) return;

    const poll = async () => {
      const pending = pendingRef.current;
      if (pending.size === 0) return;

      for (const sessionId of [...pending]) {
        try {
          const session = await chatApi.getSession(sessionId);
          const lastMsg = session.messages?.[session.messages.length - 1];
          if (lastMsg && lastMsg.role === 'assistant') {
            console.log(`[poll] AI responded for session ${sessionId}, updating UI`);
            if (activeSessionRef.current === sessionId) {
              setMessages(session.messages || []);
            }
            setPendingSessions(prev => {
              const next = new Set(prev);
              next.delete(sessionId);
              return next;
            });
            // Reload sessions list
            const sessionsData = await chatApi.listSessions();
            setSessions(sessionsData);
          }
        } catch (e) {
          console.log(`[poll] error for session ${sessionId}:`, e);
        }
      }
    };

    const interval = setInterval(poll, 1000);
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  // Auto-scroll when messages or typing state changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSessionTyping]);

  const loadSessions = async () => {
    try {
      const data = await chatApi.listSessions();
      setSessions(data);
    } catch {
      // silently fail
    }
  };

  const openSession = async (id: number) => {
    setActiveSession(id);
    try {
      const session = await chatApi.getSession(id);
      setMessages(session.messages || []);
      // If this session was pending, check if AI has responded now
      if (pendingSessions.has(id)) {
        const lastMsg = session.messages?.[session.messages.length - 1];
        if (lastMsg && lastMsg.role === 'assistant') {
          setPendingSessions(prev => {
            const next = new Set(prev);
            next.delete(id);
            return next;
          });
        }
      }
    } catch {
      setMessages([]);
    }
  };

  const newChat = async () => {
    setActiveSession(null);
    setMessages([]);
    setInput('');
    inputRef.current?.focus();
  };

  const deleteSession = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await chatApi.deleteSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (activeSession === id) {
        setActiveSession(null);
        setMessages([]);
      }
    } catch {
      // silently fail
    }
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isSessionTyping) return;

    setInput('');

    let sessionId = activeSession;

    // If no active session, create one
    if (!sessionId) {
      try {
        const newSession = await chatApi.createSession(text);
        sessionId = newSession.id;
        setActiveSession(sessionId);
        await loadSessions();
      } catch {
        return;
      }
    }

    // Mark this session as pending
    setPendingSessions(prev => new Set(prev).add(sessionId));

    // Step 1: Save user message to DB immediately (fast, returns instantly)
    try {
      await chatApi.saveMessage(sessionId, text);
    } catch {
      setPendingSessions(prev => {
        const next = new Set(prev);
        next.delete(sessionId);
        return next;
      });
      return;
    }

    // Add user message to local state
    const userMsg: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages(prev => {
      if (prev.some(m => m.id === userMsg.id)) return prev;
      return [...prev, userMsg];
    });

    // Step 2: Generate AI response (this takes time but message is already saved)
    // Polling will detect when AI responds and update messages automatically
    try {
      await chatApi.generateResponse(sessionId);
      console.log(`[send] generateResponse succeeded for session ${sessionId}`);
      await loadSessions();
    } catch (err: any) {
      console.error(`[send] generateResponse FAILED for session ${sessionId}:`, err);
      // DON'T remove from pending - polling will still check
      // The AI might have failed but the polling will eventually give up or find the response
    }
    // Don't remove from pending here - polling will remove it when AI responds
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400 mb-4">
          Please log in to use the AI Assistant.
        </p>
        <Link
          to="/login"
          className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition"
        >
          Login
        </Link>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-12rem)] bg-gray-900 rounded-lg overflow-hidden border border-gray-700">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 bg-gray-800 border-r border-gray-700 flex flex-col overflow-hidden`}>
        <div className="p-3 border-b border-gray-700">
          <button
            onClick={newChat}
            className="w-full py-2 bg-purple-700 hover:bg-purple-600 text-white rounded-lg font-medium transition text-sm"
          >
            + New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {sessions.length === 0 && (
            <p className="text-gray-500 text-sm p-4 text-center">No chats yet</p>
          )}
          {sessions.map(session => (
            <div
              key={session.id}
              onClick={() => openSession(session.id)}
              className={`px-3 py-2 cursor-pointer hover:bg-gray-700 border-b border-gray-700/50 flex items-center group ${
                activeSession === session.id ? 'bg-gray-700' : ''
              }`}
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 truncate">{session.title}</p>
                <p className="text-xs text-gray-500">
                  {new Date(session.updated_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={(e) => deleteSession(session.id, e)}
                className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition text-xs px-1"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-gray-800">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-gray-400 hover:text-gray-200 transition"
            >
              ☰
            </button>
            <span className="font-medium text-gray-200">
              {activeSession
                ? sessions.find(s => s.id === activeSession)?.title || 'Chat'
                : 'New Chat'}
            </span>
          </div>
          <span className="text-xs text-gray-500">🤖 F1 AI Assistant</span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && !isSessionTyping && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <span className="text-5xl mb-4">🏎️</span>
              <h3 className="text-xl font-bold text-gray-200 mb-2">
                F1 AI Assistant
              </h3>
              <p className="text-gray-400 max-w-md">
                Ask me anything about Formula 1 — drivers, races, circuits, history, or championships.
              </p>
              <div className="mt-6 grid grid-cols-2 gap-2 max-w-md">
                {[
                  'Who won the 2024 championship?',
                  'Most wins at Monaco?',
                  'Tell me about Suzuka circuit',
                  'How did Hamilton do in 2021?',
                ].map(q => (
                  <button
                    key={q}
                    onClick={() => setInput(q)}
                    className="text-left px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition border border-gray-700"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(msg => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl px-4 py-3 rounded-2xl ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-md'
                    : 'bg-gray-700 text-gray-100 rounded-bl-md'
                }`}
              >
                {msg.role === 'user' ? (
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                ) : (
                  <div className="markdown-content text-sm leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isSessionTyping && (
            <div className="flex justify-start">
              <div className="max-w-2xl px-4 py-3 rounded-2xl bg-gray-700 text-gray-100 rounded-bl-md">
                <div className="flex items-center gap-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                  <span className="text-xs text-gray-400">AI is thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-4 py-3 border-t border-gray-700 bg-gray-800">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about F1..."
              disabled={isSessionTyping}
              className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-purple-500 disabled:opacity-50"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isSessionTyping}
              className="px-5 py-2 bg-purple-700 hover:bg-purple-600 disabled:bg-gray-600 text-white rounded-lg transition font-medium"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
