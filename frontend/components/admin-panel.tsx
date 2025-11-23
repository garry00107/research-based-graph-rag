"use client";

import { useState } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Settings, Upload, CheckCircle, AlertCircle } from 'lucide-react';

export function AdminPanel() {
    const [arxivId, setArxivId] = useState('');
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
    const [msg, setMsg] = useState('');

    const handleIngest = async () => {
        if (!arxivId) return;
        setStatus('loading');
        setMsg('');
        try {
            await api.ingest(arxivId);
            setStatus('success');
            setMsg(`Successfully ingested ${arxivId}`);
            setArxivId('');
        } catch (error: any) {
            setStatus('error');
            const errorMsg = error.response?.data?.detail || error.message || 'Failed to ingest paper.';
            setMsg(errorMsg);
        }
    };

    return (
        <Sheet>
            <SheetTrigger asChild>
                <Button variant="outline" size="icon">
                    <Settings className="w-4 h-4" />
                </Button>
            </SheetTrigger>
            <SheetContent>
                <SheetHeader>
                    <SheetTitle>Admin Panel</SheetTitle>
                </SheetHeader>
                <div className="py-6 space-y-6">
                    <div className="space-y-2">
                        <h3 className="text-sm font-medium">Ingest Paper</h3>
                        <div className="flex gap-2">
                            <Input
                                placeholder="ArXiv ID (e.g., 1706.03762)"
                                value={arxivId}
                                onChange={(e) => setArxivId(e.target.value)}
                            />
                            <Button onClick={handleIngest} disabled={status === 'loading'}>
                                <Upload className="w-4 h-4" />
                            </Button>
                        </div>
                        {status === 'success' && (
                            <div className="text-xs text-green-500 flex items-center gap-1">
                                <CheckCircle className="w-3 h-3" /> {msg}
                            </div>
                        )}
                        {status === 'error' && (
                            <div className="text-xs text-red-500 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3" /> {msg}
                            </div>
                        )}
                        {status === 'loading' && (
                            <div className="text-xs text-muted-foreground">Processing...</div>
                        )}
                    </div>
                </div>
            </SheetContent>
        </Sheet>
    );
}
