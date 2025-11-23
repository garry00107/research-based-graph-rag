"use client";

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { History, Trash2, RefreshCw, User, Bot } from 'lucide-react';

interface Message {
    role: string;
    content: string;
    timestamp: string;
}

export function ChatHistory() {
    const [history, setHistory] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);
    const conversationId = 'default';

    const loadHistory = async () => {
        setLoading(true);
        try {
            const res = await api.getChatHistory(conversationId);
            setHistory(res.data.history || []);
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
        setLoading(false);
    };

    useEffect(() => {
        loadHistory();
    }, []);

    const handleClear = async () => {
        if (!confirm('Clear all chat history?')) return;

        try {
            await api.clearChatHistory(conversationId);
            setHistory([]);
        } catch (error) {
            console.error('Error clearing history:', error);
        }
    };

    return (
        <Sheet>
            <SheetTrigger asChild>
                <Button variant="outline" size="icon">
                    <History className="w-4 h-4" />
                </Button>
            </SheetTrigger>
            <SheetContent className="w-full sm:max-w-2xl">
                <SheetHeader>
                    <SheetTitle className="flex items-center gap-2">
                        <History className="w-5 h-5" />
                        Chat History
                    </SheetTitle>
                </SheetHeader>

                <div className="py-6 space-y-4">
                    {/* Actions */}
                    <div className="flex gap-2 justify-between items-center">
                        <div className="text-sm text-muted-foreground">
                            {history.length} messages
                        </div>
                        <div className="flex gap-2">
                            <Button onClick={loadHistory} variant="outline" size="sm">
                                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                                Refresh
                            </Button>
                            <Button
                                onClick={handleClear}
                                variant="destructive"
                                size="sm"
                                disabled={history.length === 0}
                            >
                                <Trash2 className="w-4 h-4 mr-2" />
                                Clear
                            </Button>
                        </div>
                    </div>

                    {/* History List */}
                    <ScrollArea className="h-[600px] pr-4">
                        {history.length === 0 ? (
                            <div className="text-center py-12 text-muted-foreground">
                                No chat history yet
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {history.map((msg, idx) => (
                                    <Card key={idx} className={msg.role === 'user' ? 'bg-primary/5' : 'bg-muted/50'}>
                                        <CardContent className="p-4">
                                            <div className="flex items-start gap-3">
                                                <div className={`p-2 rounded-full ${msg.role === 'user'
                                                        ? 'bg-primary text-primary-foreground'
                                                        : 'bg-muted'
                                                    }`}>
                                                    {msg.role === 'user' ? (
                                                        <User className="w-4 h-4" />
                                                    ) : (
                                                        <Bot className="w-4 h-4" />
                                                    )}
                                                </div>
                                                <div className="flex-1 space-y-1">
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-semibold text-sm capitalize">
                                                            {msg.role}
                                                        </span>
                                                        <span className="text-xs text-muted-foreground">
                                                            {new Date(msg.timestamp).toLocaleString()}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm whitespace-pre-wrap">
                                                        {msg.content}
                                                    </p>
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        )}
                    </ScrollArea>
                </div>
            </SheetContent>
        </Sheet>
    );
}
