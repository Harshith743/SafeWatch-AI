
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
        <div className="flex h-screen text-gray-100 font-sans overflow-hidden bg-transparent">
            {/* Sidebar - Desktop */}
            <div className="hidden md:flex w-[280px] flex-col glass-panel m-4 rounded-2xl p-4 z-10">
                <button className="flex items-center justify-center gap-2 p-3 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/10 transition-all duration-300 mb-6 text-sm text-gray-200 shadow-sm hover:shadow-md font-medium">
                    <Plus size={16} />
                    <span>New chat</span>
                </button>

                <div className="flex-1 overflow-y-auto pr-2">
                    <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 px-2">Recent</div>
                    <div className="p-3 bg-white/[0.02] hover:bg-white/[0.06] rounded-xl cursor-pointer text-sm truncate text-gray-300 transition-colors border border-transparent hover:border-white/5">
                        Adverse events for Aspirin
                    </div>
                </div>

                <div className="mt-auto border-t border-white/10 pt-4">
                    <div className="flex items-center gap-3 px-3 py-2 hover:bg-white/[0.05] rounded-xl cursor-pointer transition-colors">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-sm font-bold shadow-lg ring-2 ring-white/10">
                            U
                        </div>
                        <div className="text-sm font-medium tracking-wide">User</div>
                    </div>
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col relative bg-transparent z-10 md:p-4 md:pl-0">
                {/* Header - Mobile */}
                <div className="md:hidden flex items-center p-4 glass-panel justify-between z-20">
                    <Menu size={20} className="text-gray-400" />
                    <span className="font-semibold text-gray-100 tracking-wide">SafeWatch AI</span>
                    <Plus size={20} className="text-gray-400" />
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 md:p-6 md:bg-black/20 md:backdrop-blur-3xl md:border md:border-white/5 md:rounded-2xl md:shadow-2xl">
                    <div className="max-w-4xl mx-auto flex flex-col gap-8 py-8 md:py-12">
                        <AnimatePresence>
                            {messages.map((msg, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    transition={{ type: "spring", stiffness: 260, damping: 20 }}
                                    className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                >
                                    {msg.role === 'bot' && (
                                        <div className={`w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center shadow-lg ring-1 ring-white/10 ${msg.isError ? 'bg-red-500/20 text-red-400' : 'bg-gradient-to-tr from-cyan-400 to-blue-600 text-white'}`}>
                                            {msg.isError ? <AlertTriangle size={18} /> : <Bot size={20} />}
                                        </div>
                                    )}

                                    <div className={`flex flex-col max-w-[85%] md:max-w-[75%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                        <div className={`px-5 py-4 text-[15px] leading-relaxed shadow-sm ${msg.role === 'user'
                                            ? 'glass-message-user rounded-2xl rounded-tr-sm'
                                            : 'glass-message-bot rounded-2xl rounded-tl-sm text-gray-200'
                                            }`}>
                                            {msg.content}

                                            {/* Render Report Data if available */}
                                            {msg.data && (
                                                <motion.ul
                                                    initial={{ opacity: 0, marginTop: 0 }}
                                                    animate={{ opacity: 1, marginTop: 16 }}
                                                    className="space-y-2 glass-card p-4">
                                                    {msg.data.slice(0, 5).map((item, i) => (
                                                        <motion.li
                                                            initial={{ opacity: 0, x: -10 }}
                                                            animate={{ opacity: 1, x: 0 }}
                                                            transition={{ delay: i * 0.1 }}
                                                            key={i}
                                                            className="text-sm text-gray-300 flex gap-3 items-start">
                                                            <span className="text-cyan-400 mt-1 flex-shrink-0">•</span>
                                                            <span className="leading-snug">{item}</span>
                                                        </motion.li>
                                                    ))}
                                                </motion.ul>
                                            )}

                                            {msg.reportSaved && (
                                                <motion.div
                                                    initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                                    className="mt-3 text-xs text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full font-medium tracking-wide">
                                                    ✓ Report securely saved to cloud
                                                </motion.div>
                                            )}
                                        </div>
                                    </div>

                                    {msg.role === 'user' && (
                                        <div className="w-10 h-10 rounded-full glass-panel flex-shrink-0 flex items-center justify-center text-gray-300 ring-1 ring-white/10">
                                            <User size={18} />
                                        </div>
                                    )}
                                </motion.div>
                            ))}
                        </AnimatePresence>
                        {isLoading && (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4 justify-start">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-cyan-400 to-blue-600 flex-shrink-0 flex items-center justify-center text-white shadow-lg ring-1 ring-white/10">
                                    <Bot size={20} />
                                </div>
                                <div className="flex items-center gap-1.5 h-10 px-5 glass-message-bot rounded-2xl rounded-tl-sm">
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></div>
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></div>
                                </div>
                            </motion.div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* Input Area */}
                <div className="p-4 md:p-6 md:pb-8 bg-transparent z-20">
                    <div className="max-w-4xl mx-auto relative group">
                        <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask SafeWatch about a drug or report a symptom..."
                            className="relative w-full glass-input text-gray-100 rounded-full py-4 pl-6 pr-14 transition-all placeholder:text-gray-400"
                            disabled={isLoading}
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isLoading}
                            className={`absolute right-2 top-2 p-2 rounded-full transition-all duration-300 ${!input.trim() || isLoading
                                ? 'bg-white/5 text-gray-500 cursor-not-allowed border border-white/5'
                                : 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:shadow-lg hover:shadow-indigo-500/25 hover:scale-105'
                                }`}
                        >
                            <Send size={18} className={input.trim() && !isLoading ? "ml-0.5" : ""} />
                        </button>
                    </div>
                    <div className="text-center text-xs font-medium tracking-wide text-gray-500 mt-4 opacity-70">
                        SafeWatch AI can make mistakes. Consider checking important medical information with a doctor.
                    </div>
                </div>
            </div>
        </div>
    )
}

export default App
