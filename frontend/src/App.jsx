
import React, { useState, useRef, useEffect } from 'react';
import { Send, Menu, Plus, User, Bot, AlertTriangle } from 'lucide-react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
    const [messages, setMessages] = useState([
        {
            role: 'bot',
            content: "Hello! I'm SafeWatch AI. You can ask me about drug adverse events or report an incident.",
            timestamp: new Date().toISOString()
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [pendingReport, setPendingReport] = useState(null);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage = {
            role: 'user',
            content: input,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            // If we have a pending report (waiting for age/gender), append this new input to the original message
            let messageToSend = userMessage.content;
            if (pendingReport) {
                messageToSend = `${pendingReport} ${userMessage.content}`;
            }

            const response = await axios.post('/api/chat', { message: messageToSend });

            const botMessage = {
                role: 'bot',
                content: response.data.response,
                data: response.data.data, // Accessing the list if present
                reportSaved: response.data.report_saved,
                timestamp: new Date().toISOString()
            };

            setMessages(prev => [...prev, botMessage]);

            if (response.data.missing_info) {
                // Keep the accumulated message as pending so next input adds to it
                // We store the accumulated message so we keep adding to it until complete
                setPendingReport(messageToSend);
            } else {
                // Clear pending if successful or not a report flow
                setPendingReport(null);
            }

        } catch (error) {
            console.error("Error sending message:", error);
            setMessages(prev => [...prev, {
                role: 'bot',
                content: "Sorry, I encountered an error connecting to the server.",
                isError: true,
                timestamp: new Date().toISOString()
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex h-screen text-gray-100 font-sans overflow-hidden">
            {/* Sidebar - Desktop */}
            <div className="hidden md:flex w-[260px] flex-col bg-[#0d1117] border-r border-[#30363d] p-4">
                <button className="flex items-center gap-2 p-3 rounded-lg border border-[#30363d] hover:bg-[#161b22] transition-colors mb-4 text-sm text-gray-300">
                    <Plus size={16} />
                    <span>New chat</span>
                </button>

                <div className="flex-1 overflow-y-auto">
                    <div className="text-xs font-semibold text-gray-500 mb-2 px-2">Recent</div>
                    <div className="p-2 hover:bg-[#161b22] rounded cursor-pointer text-sm truncate text-gray-400">
                        Adverse events for Aspirin
                    </div>
                </div>

                <div className="mt-auto border-t border-[#30363d] pt-4">
                    <div className="flex items-center gap-2 px-2 py-2 hover:bg-[#161b22] rounded cursor-pointer">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-xs font-bold">
                            U
                        </div>
                        <div className="text-sm font-medium">User</div>
                    </div>
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col relative bg-[#0d1117]">
                {/* Header - Mobile */}
                <div className="md:hidden flex items-center p-4 border-b border-[#30363d] justify-between">
                    <Menu size={20} className="text-gray-400" />
                    <span className="font-semibold text-gray-200">SafeWatch AI</span>
                    <Plus size={20} className="text-gray-400" />
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 md:p-0">
                    <div className="max-w-3xl mx-auto flex flex-col gap-6 py-8 md:py-12">
                        <AnimatePresence>
                            {messages.map((msg, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                >
                                    {msg.role === 'bot' && (
                                        <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${msg.isError ? 'bg-red-900/50 text-red-400' : 'bg-gradient-to-tr from-cyan-500 to-blue-600 text-white'}`}>
                                            {msg.isError ? <AlertTriangle size={16} /> : <Bot size={18} />}
                                        </div>
                                    )}

                                    <div className={`flex flex-col max-w-[80%] md:max-w-[70%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                        <div className={`text-sm ${msg.role === 'user' ? 'font-medium text-gray-300 mb-1' : 'font-semibold text-gray-200 mb-1'}`}>
                                            {msg.role === 'user' ? 'You' : 'SafeWatch AI'}
                                        </div>
                                        <div className={`px-4 py-3 rounded-2xl text-[15px] leading-relaxed shadow-sm ${msg.role === 'user'
                                            ? 'bg-[#21262d] text-gray-100 rounded-br-sm'
                                            : 'bg-transparent text-gray-300'
                                            }`}>
                                            {msg.content}

                                            {/* Render Report Data if available */}
                                            {msg.data && (
                                                <ul className="mt-3 space-y-2 bg-[#161b22] p-3 rounded-lg border border-[#30363d]">
                                                    {msg.data.slice(0, 5).map((item, i) => (
                                                        <li key={i} className="text-sm text-gray-300 flex gap-2">
                                                            <span className="text-cyan-500">•</span>
                                                            {item}
                                                        </li>
                                                    ))}
                                                </ul>
                                            )}

                                            {msg.reportSaved && (
                                                <div className="mt-2 text-xs text-green-400 flex items-center gap-1">
                                                    ✓ Report saved successfully
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {msg.role === 'user' && (
                                        <div className="w-8 h-8 rounded-full bg-[#30363d] flex-shrink-0 flex items-center justify-center text-gray-300">
                                            <User size={16} />
                                        </div>
                                    )}
                                </motion.div>
                            ))}
                        </AnimatePresence>
                        {isLoading && (
                            <div className="flex gap-4 justify-start">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex-shrink-0 flex items-center justify-center text-white">
                                    <Bot size={18} />
                                </div>
                                <div className="flex items-center gap-1 h-10 px-4">
                                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* Input Area */}
                <div className="p-4 bg-[#0d1117]">
                    <div className="max-w-3xl mx-auto relative">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask about a drug or report a symptom..."
                            className="w-full bg-[#161b22] border border-[#30363d] text-gray-200 rounded-full py-4 pl-6 pr-14 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-gray-500 shadow-lg"
                            disabled={isLoading}
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isLoading}
                            className={`absolute right-2 top-2 p-2 rounded-full transition-colors ${!input.trim() || isLoading
                                ? 'bg-[#21262d] text-gray-500 cursor-not-allowed'
                                : 'bg-white text-black hover:bg-gray-200'
                                }`}
                        >
                            <Send size={18} />
                        </button>
                    </div>
                    <div className="text-center text-xs text-gray-500 mt-2">
                        SafeWatch AI can make mistakes. Consider checking important information.
                    </div>
                </div>
            </div>
        </div>
    )
}

export default App
