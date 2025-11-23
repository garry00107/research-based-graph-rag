"use client";

import { useState } from 'react';
import { useChatStore } from '@/lib/store';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, User, BookOpen } from 'lucide-react';

export function ChatInterface() {
    const { messages, addMessage, isLoading, setLoading } = useChatStore();
    const [input, setInput] = useState('');

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = input;
        setInput('');
        addMessage({ role: 'user', content: userMsg });
        setLoading(true);

        try {
            const res = await api.chat(userMsg);
            addMessage({
                role: 'assistant',
                content: res.data.response,
                citations: res.data.citations
            });
        } catch (error) {
            addMessage({ role: 'assistant', content: "Sorry, I encountered an error. Please check the backend connection." });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[600px] w-full max-w-4xl mx-auto border rounded-xl overflow-hidden bg-background shadow-lg">
            <div className="bg-muted p-4 border-b">
                <h2 className="font-semibold flex items-center gap-2">
                    <Bot className="w-5 h-5" /> Research Assistant
                </h2>
            </div>

            <ScrollArea className="flex-1 p-4 overflow-y-auto">
                <div className="space-y-4 min-h-full">
                    {messages.map((msg, i) => (
                        <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            {msg.role === 'assistant' && (
                                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                                    <Bot className="w-4 h-4 text-primary" />
                                </div>
                            )}

                            <div className={`max-w-[80%] space-y-2`}>
                                <div className={`p-3 rounded-lg ${msg.role === 'user'
                                    ? 'bg-primary text-primary-foreground'
                                    : 'bg-muted'
                                    }`}>
                                    {msg.content}
                                </div>

                                {msg.citations && msg.citations.length > 0 && (
                                    <div className="grid gap-2 mt-2">
                                        {msg.citations.map((cit, j) => (
                                            <Card key={j} className="text-xs bg-card/50">
                                                <CardHeader className="p-2 pb-0">
                                                    <CardTitle className="text-xs font-medium flex items-center gap-1">
                                                        <BookOpen className="w-3 h-3" /> Source (Score: {cit.score?.toFixed(2)})
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent className="p-2 text-muted-foreground">
                                                    {cit.text}
                                                </CardContent>
                                            </Card>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {msg.role === 'user' && (
                                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
                                    <User className="w-4 h-4 text-primary-foreground" />
                                </div>
                            )}
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex gap-3">
                            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                                <Bot className="w-4 h-4 text-primary" />
                            </div>
                            <div className="bg-muted p-3 rounded-lg animate-pulse">
                                Thinking...
                            </div>
                        </div>
                    )}
                </div>
            </ScrollArea>

            <div className="p-4 border-t bg-background flex gap-2">
                <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Ask a question about the papers..."
                    disabled={isLoading}
                />
                <Button onClick={handleSend} disabled={isLoading}>
                    <Send className="w-4 h-4" />
                </Button>
            </div>
        </div>
    );
}
