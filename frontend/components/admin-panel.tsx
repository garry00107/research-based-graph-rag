"use client";

import { useState } from 'react';
import { api, Paper } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetDescription } from '@/components/ui/sheet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Settings, Search, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export function AdminPanel() {
    const [searchQuery, setSearchQuery] = useState('');
    const [category, setCategory] = useState('all');
    const [year, setYear] = useState('');
    const [searchResults, setSearchResults] = useState<Paper[]>([]);
    const [selectedPapers, setSelectedPapers] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [ingesting, setIngesting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [ingestSuccessMsg, setIngestSuccessMsg] = useState<string | null>(null);
    const [msg, setMsg] = useState(''); // Keeping for backward compatibility if needed, or remove if unused

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;

        setLoading(true);
        setError(null);
        setIngestSuccessMsg(null); // Clear ingest success message on new search
        setSearchResults([]); // Clear previous search results
        setSelectedPapers([]); // Clear selected papers
        try {
            const res = await api.search(searchQuery, 10, category, year);
            setSearchResults(res.data.results);
        } catch (error: any) {
            console.error('Error searching:', error);
            setError(error.response?.data?.detail || 'Failed to search papers');
        }
        setLoading(false);
    };

    const togglePaper = (arxivId: string) => {
        setSelectedPapers(prev => {
            if (prev.includes(arxivId)) {
                return prev.filter(id => id !== arxivId);
            } else {
                return [...prev, arxivId];
            }
        });
    };

    const handleIngest = async () => {
        if (selectedPapers.length === 0) return;

        setIngesting(true);
        setError(null);
        setIngestSuccessMsg(null);
        try {
            await api.ingestBatch(selectedPapers);
            setIngestSuccessMsg(`Successfully ingested ${selectedPapers.length} paper(s)!`);
            setSelectedPapers([]);
        } catch (error: any) {
            console.error('Error ingesting:', error);
            setError(error.response?.data?.detail || 'Failed to ingest papers');
        }
        setIngesting(false);
    };

    return (
        <Sheet>
            <SheetTrigger asChild>
                <Button variant="outline" size="icon">
                    <Settings className="w-4 h-4" />
                </Button>
            </SheetTrigger>
            <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
                <SheetHeader>
                    <SheetTitle>Admin Panel</SheetTitle>
                    <SheetDescription>
                        Search and ingest research papers from ArXiv.
                    </SheetDescription>
                </SheetHeader>

                <div className="py-6 space-y-6">
                    {/* Search Section */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-medium">Search Papers</h3>
                        <div className="flex gap-2">
                            <Input
                                placeholder="Search by title, author, or keyword..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                            />
                            <Button onClick={handleSearch} disabled={loading}>
                                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                            </Button>
                        </div>

                        {/* Filters */}
                        <div className="flex gap-2">
                            <select
                                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                            >
                                <option value="all">All Categories</option>
                                <option value="cs.AI">Artificial Intelligence</option>
                                <option value="cs.CL">Computation and Language</option>
                                <option value="cs.CV">Computer Vision</option>
                                <option value="cs.LG">Machine Learning</option>
                                <option value="cs.SE">Software Engineering</option>
                            </select>
                            <Input
                                placeholder="Year (e.g. 2024)"
                                className="w-32"
                                value={year}
                                onChange={(e) => setYear(e.target.value)}
                            />
                        </div>

                        {error && (
                            <div className="p-3 text-sm text-red-500 bg-red-50 rounded-md border border-red-200 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3" /> {error}
                            </div>
                        )}
                        {!error && !loading && searchResults.length > 0 && (
                            <div className="text-xs text-green-500 flex items-center gap-1">
                                <CheckCircle className="w-3 h-3" /> Found {searchResults.length} papers
                            </div>
                        )}
                    </div>

                    {searchResults.length > 0 && (
                        <>
                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-sm font-medium">Results ({selectedPapers.length} selected)</h3>
                                    <Button
                                        onClick={handleIngest}
                                        disabled={selectedPapers.length === 0 || ingesting}
                                        size="sm"
                                    >
                                        {ingesting ? (
                                            <>
                                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                                Ingesting...
                                            </>
                                        ) : (
                                            `Ingest Selected (${selectedPapers.length})`
                                        )}
                                    </Button>
                                </div>
                                {ingestSuccessMsg && (
                                    <div className="text-xs text-green-500 flex items-center gap-1">
                                        <CheckCircle className="w-3 h-3" /> {ingestSuccessMsg}
                                    </div>
                                )}
                            </div>

                            <ScrollArea className="h-[500px] pr-4">
                                <div className="space-y-3">
                                    {searchResults.map((paper) => (
                                        <Card
                                            key={paper.arxiv_id}
                                            className={`cursor-pointer transition-colors ${selectedPapers.includes(paper.arxiv_id)
                                                ? 'border-primary bg-primary/5'
                                                : 'hover:border-primary/50'
                                                }`}
                                            onClick={() => togglePaper(paper.arxiv_id)}
                                        >
                                            <CardHeader className="p-4 pb-2">
                                                <div className="flex items-start gap-2">
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedPapers.includes(paper.arxiv_id)}
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
                                                {paper.categories && paper.categories.length > 0 && (
                                                    <div className="flex gap-1 mt-2 flex-wrap">
                                                        {paper.categories.slice(0, 3).map(cat => (
                                                            <span key={cat} className="px-1.5 py-0.5 rounded-full bg-muted text-[10px] font-medium">
                                                                {cat}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
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
