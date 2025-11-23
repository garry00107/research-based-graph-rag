"use client";

import { useState } from 'react';
import { api, Paper } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Settings, Search, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export function AdminPanel() {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<Paper[]>([]);
    const [selectedPapers, setSelectedPapers] = useState<Set<string>>(new Set());
    const [searchStatus, setSearchStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
    const [ingestStatus, setIngestStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
    const [msg, setMsg] = useState('');

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;
        setSearchStatus('loading');
        setMsg('');
        setSearchResults([]);
        setSelectedPapers(new Set());

        try {
            const res = await api.search(searchQuery);
            setSearchResults(res.data.results);
            setSearchStatus('success');
            setMsg(`Found ${res.data.results.length} papers`);
        } catch (error: any) {
            setSearchStatus('error');
            const errorMsg = error.response?.data?.detail || error.message || 'Search failed.';
            setMsg(errorMsg);
        }
    };

    const togglePaper = (arxivId: string) => {
        const newSelected = new Set(selectedPapers);
        if (newSelected.has(arxivId)) {
            newSelected.delete(arxivId);
        } else {
            newSelected.add(arxivId);
        }
        setSelectedPapers(newSelected);
    };

    const handleIngest = async () => {
        if (selectedPapers.size === 0) return;
        setIngestStatus('loading');
        setMsg('');

        try {
            const arxivIds = Array.from(selectedPapers);
            await api.ingestBatch(arxivIds);
            setIngestStatus('success');
            setMsg(`Successfully ingested ${arxivIds.length} paper(s)`);
            setSelectedPapers(new Set());
        } catch (error: any) {
            setIngestStatus('error');
            const errorMsg = error.response?.data?.detail || error.message || 'Ingestion failed.';
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
            <SheetContent className="w-full sm:max-w-2xl">
                <SheetHeader>
                    <SheetTitle>Admin Panel</SheetTitle>
                </SheetHeader>
                <div className="py-6 space-y-6">
                    <div className="space-y-2">
                        <h3 className="text-sm font-medium">Search Papers</h3>
                        <div className="flex gap-2">
                            <Input
                                placeholder="Search by title or keywords..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                            />
                            <Button onClick={handleSearch} disabled={searchStatus === 'loading'}>
                                {searchStatus === 'loading' ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Search className="w-4 h-4" />
                                )}
                            </Button>
                        </div>
                        {searchStatus === 'success' && (
                            <div className="text-xs text-green-500 flex items-center gap-1">
                                <CheckCircle className="w-3 h-3" /> {msg}
                            </div>
                        )}
                        {searchStatus === 'error' && (
                            <div className="text-xs text-red-500 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3" /> {msg}
                            </div>
                        )}
                    </div>

                    {searchResults.length > 0 && (
                        <>
                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-sm font-medium">Results ({selectedPapers.size} selected)</h3>
                                    <Button
                                        onClick={handleIngest}
                                        disabled={selectedPapers.size === 0 || ingestStatus === 'loading'}
                                        size="sm"
                                    >
                                        {ingestStatus === 'loading' ? (
                                            <>
                                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                                Ingesting...
                                            </>
                                        ) : (
                                            `Ingest Selected (${selectedPapers.size})`
                                        )}
                                    </Button>
                                </div>
                                {ingestStatus === 'success' && (
                                    <div className="text-xs text-green-500 flex items-center gap-1">
                                        <CheckCircle className="w-3 h-3" /> {msg}
                                    </div>
                                )}
                                {ingestStatus === 'error' && (
                                    <div className="text-xs text-red-500 flex items-center gap-1">
                                        <AlertCircle className="w-3 h-3" /> {msg}
                                    </div>
                                )}
                            </div>

                            <ScrollArea className="h-[500px] pr-4">
                                <div className="space-y-3">
                                    {searchResults.map((paper) => (
                                        <Card
                                            key={paper.arxiv_id}
                                            className={`cursor-pointer transition-colors ${selectedPapers.has(paper.arxiv_id)
                                                    ? 'border-primary bg-primary/5'
                                                    : 'hover:border-primary/50'
                                                }`}
                                            onClick={() => togglePaper(paper.arxiv_id)}
                                        >
                                            <CardHeader className="p-4 pb-2">
                                                <div className="flex items-start gap-2">
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedPapers.has(paper.arxiv_id)}
                                                        onChange={() => togglePaper(paper.arxiv_id)}
                                                        className="mt-1"
                                                        onClick={(e) => e.stopPropagation()}
                                                    />
                                                    <div className="flex-1">
                                                        <CardTitle className="text-sm font-semibold">
                                                            {paper.title}
                                                        </CardTitle>
                                                        <p className="text-xs text-muted-foreground mt-1">
                                                            {paper.authors.slice(0, 3).join(', ')}
                                                            {paper.authors.length > 3 && ` +${paper.authors.length - 3} more`}
                                                        </p>
                                                    </div>
                                                </div>
                                            </CardHeader>
                                            <CardContent className="p-4 pt-2">
                                                <p className="text-xs text-muted-foreground line-clamp-3">
                                                    {paper.summary}
                                                </p>
                                                <p className="text-xs text-muted-foreground mt-2">
                                                    ArXiv ID: {paper.arxiv_id}
                                                </p>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            </ScrollArea>
                        </>
                    )}
                </div>
            </SheetContent>
        </Sheet>
    );
}
