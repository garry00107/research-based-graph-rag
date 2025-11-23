"use client";

import { useState, useRef, useEffect } from 'react';
import { api, ChatResponse, Citation } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, User, FileText, ThumbsUp, ThumbsDown, Download } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    citations?: Citation[];
    id?: string;
    feedback?: 'up' | 'down';
}

export function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage: Message = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            // Use streaming endpoint
            const response = await fetch('/api/chat-stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMessage.content })
            });

            if (!response.ok) throw new Error('Failed to send message');

            const reader = response.body?.getReader();
            if (!reader) throw new Error('No reader available');

            const assistantMessage: Message = {
                role: 'assistant',
                content: '',
                citations: [],
                id: crypto.randomUUID() // Temporary ID until backend confirms (or use timestamp)
            };

            setMessages(prev => [...prev, assistantMessage]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const text = new TextDecoder().decode(value);
                const lines = text.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') break;

                        try {
                            const parsed = JSON.parse(data);
                            if (parsed.token) {
                                setMessages(prev => {
                                    const newMessages = [...prev];
                                    const lastIndex = newMessages.length - 1;
                                    const lastMsg = { ...newMessages[lastIndex] };
                                    lastMsg.content += parsed.token;
                                    newMessages[lastIndex] = lastMsg;
                                    return newMessages;
                                });
                            }
                            if (parsed.citations) {
                                setMessages(prev => {
                                    const newMessages = [...prev];
                                    const lastIndex = newMessages.length - 1;
                                    const lastMsg = { ...newMessages[lastIndex] };
                                    lastMsg.citations = parsed.citations;
                                    newMessages[lastIndex] = lastMsg;
                                    // Update ID if provided by backend (future improvement)
                                    return newMessages;
                                });
                            }
                        } catch (e) {
                            console.error('Error parsing SSE:', e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error.' }]);
        }
        setLoading(false);
    };

    const handleFeedback = async (index: number, feedback: 'up' | 'down') => {
        const msg = messages[index];
        // Only allow feedback on assistant messages that have content
        if (msg.role !== 'assistant' || !msg.content) return;

        // Optimistic update
        setMessages(prev => {
            const newMessages = [...prev];
            newMessages[index].feedback = feedback;
            return newMessages;
        });

        try {
            // We need a message ID. For now, we might not have the real backend ID if using streaming without full sync.
            // But let's assume we can use a generated ID or the one from history if we re-fetched.
            // For this implementation, we'll skip the API call if no ID, or use a placeholder.
            // Ideally, the streaming response should return the message ID.
            if (msg.id) {
                await api.submitFeedback(msg.id, feedback);
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            // Revert on error
            setMessages(prev => {
                const newMessages = [...prev];
                newMessages[index].feedback = undefined;
                return newMessages;
            });
        }
    };

    const handleExport = async () => {
        try {
            await api.exportChatMarkdown('default');
        } catch (error) {
            console.error('Error exporting chat:', error);
        }
    };

    return (
        <div className="flex flex-col h-[80vh] w-full mx-auto">
            <Card className="flex-1 mb-4 overflow-hidden flex flex-col shadow-lg border-muted">
                <div className="p-4 border-b bg-muted/30 flex justify-between items-center">
                    <h2 className="font-semibold flex items-center gap-2">
                        <Bot className="w-5 h-5 text-primary" />
                        Research Assistant
                    </h2>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleExport}
                        title="Export chat as Markdown"
                    >
                        <Download className="w-4 h-4" />
                    </Button>
                </div>

                <ScrollArea className="flex-1 p-4 min-h-0">
                    <div className="space-y-6">
                        {messages.length === 0 && (
                            <div className="text-center text-muted-foreground mt-20">
                                <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                <p>Ask me anything about the ingested papers!</p>
                            </div>
                        )}

                        {messages.map((msg, idx) => (
                            <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                {msg.role === 'assistant' && (
                                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                                        <Bot className="w-5 h-5 text-primary" />
                                    </div>
                                )}

                                <div className={`max-w-[85%] rounded-lg p-4 ${msg.role === 'user'
                                    ? 'bg-primary text-primary-foreground'
                                    : 'bg-muted/50'
                                    }`}>
                                    <div className="prose dark:prose-invert text-sm max-w-none">
                                        <ReactMarkdown>
                                            {msg.content}
                                        </ReactMarkdown>
                                    </div>

                                    {msg.citations && msg.citations.length > 0 && (
                                        <div className="mt-4 pt-4 border-t border-border/50">
                                            <p className="text-xs font-semibold mb-2 flex items-center gap-1">
                                                <FileText className="w-3 h-3" /> Sources
                                            </p>
                                            <div className="grid gap-2">
                                                {msg.citations.map((cit, cIdx) => {
                                                    // Use the clean arxiv_id from backend
                                                    const arxivId = cit.metadata?.arxiv_id;
                                                    const arxivUrl = arxivId ? `https://arxiv.org/abs/${arxivId}` : null;

                                                    return (
                                                        <div key={cIdx} className="text-xs bg-background/50 p-2 rounded border border-border/50">
                                                            <div className="flex items-start justify-between gap-2">
                                                                <p className="font-medium text-primary flex-1">{cit.metadata.title}</p>
                                                                {arxivUrl && (
                                                                    <a
                                                                        href={arxivUrl}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="text-primary hover:underline text-xs shrink-0"
                                                                        title="View on ArXiv"
                                                                    >
                                                                        🔗 ArXiv
                                                                    </a>
                                                                )}
                                                            </div>
                                                            <p className="text-muted-foreground mt-1 line-clamp-2">{cit.text}</p>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    )}

                                    {msg.role === 'assistant' && msg.content && (
                                        <div className="mt-2 flex gap-2 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className={`h-6 w-6 ${msg.feedback === 'up' ? 'text-green-500' : 'text-muted-foreground'}`}
                                                onClick={() => handleFeedback(idx, 'up')}
                                            >
                                                <ThumbsUp className="w-3 h-3" />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className={`h-6 w-6 ${msg.feedback === 'down' ? 'text-red-500' : 'text-muted-foreground'}`}
                                                onClick={() => handleFeedback(idx, 'down')}
                                            >
                                                <ThumbsDown className="w-3 h-3" />
                                            </Button>
                                        </div>
                                    )}
                                </div>

                                {msg.role === 'user' && (
                                    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
                                        <User className="w-5 h-5 text-primary-foreground" />
                                    </div>
                                )}
                            </div>
                        ))}
                        {loading && (
                            <div className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                                    <Bot className="w-5 h-5 text-primary" />
                                </div>
                                <div className="bg-muted/50 rounded-lg p-4 flex items-center gap-2">
                                    <div className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" />
                                    <div className="w-2 h-2 bg-primary/50 rounded-full animate-bounce delay-75" />
                                    <div className="w-2 h-2 bg-primary/50 rounded-full animate-bounce delay-150" />
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </ScrollArea>

                <div className="p-4 border-t bg-background">
                    <div className="flex gap-2">
                        <Input
                            placeholder="Ask a question about the papers..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            disabled={loading}
                            className="flex-1"
                        />
                        <Button onClick={handleSend} disabled={loading}>
                            <Send className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            </Card>
        </div>
    );
}
