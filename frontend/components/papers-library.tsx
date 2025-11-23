"use client";

import { useState, useEffect } from 'react';
import { api, IngestedPaper } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Library, Search, Trash2, RefreshCw, BookOpen, FileDown, Copy } from 'lucide-react';

export function PapersLibrary() {
    const [papers, setPapers] = useState<IngestedPaper[]>([]);
    const [filteredPapers, setFilteredPapers] = useState<IngestedPaper[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState<any>(null);

    const loadPapers = async () => {
        setLoading(true);
        try {
            const res = await api.getPapers();
            setPapers(res.data.papers);
            setFilteredPapers(res.data.papers);
            setStats(res.data.stats);
        } catch (error) {
            console.error('Error loading papers:', error);
        }
        setLoading(false);
    };

    useEffect(() => {
        loadPapers();
    }, []);

    useEffect(() => {
        if (!searchQuery.trim()) {
            setFilteredPapers(papers);
            return;
        }

        const query = searchQuery.toLowerCase();
        const filtered = papers.filter(paper =>
            paper.title.toLowerCase().includes(query) ||
            paper.authors.some(author => author.toLowerCase().includes(query)) ||
            paper.summary.toLowerCase().includes(query)
        );
        setFilteredPapers(filtered);
    }, [searchQuery, papers]);

    const handleDelete = async (arxivId: string) => {
        if (!confirm('Remove this paper from library?')) return;

        try {
            await api.deletePaper(arxivId);
            await loadPapers();
        } catch (error) {
            console.error('Error deleting paper:', error);
        }
    };

    const handleCopyBibtex = async (arxivId: string) => {
        try {
            const res = await api.getBibtex(arxivId);
            await navigator.clipboard.writeText(res.data.bibtex);
            alert('BibTeX copied to clipboard!');
        } catch (error) {
            console.error('Error copying BibTeX:', error);
            alert('Failed to copy BibTeX');
        }
    };

    const handleExportAllBibtex = async () => {
        try {
            await api.exportAllBibtex();
        } catch (error) {
            console.error('Error exporting BibTeX:', error);
            alert('Failed to export BibTeX');
        }
    };

    return (
        <Sheet>
            <SheetTrigger asChild>
                <Button variant="outline" size="icon">
                    <Library className="w-4 h-4" />
                </Button>
            </SheetTrigger>
            <SheetContent className="w-full sm:max-w-2xl">
                <SheetHeader>
                    <div className="flex items-center justify-between">
                        <SheetTitle className="flex items-center gap-2">
                            <BookOpen className="w-5 h-5" />
                            Papers Library
                        </SheetTitle>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleExportAllBibtex}
                            disabled={papers.length === 0}
                        >
                            <FileDown className="w-4 h-4 mr-2" />
                            Export BibTeX
                        </Button>
                    </div>
                </SheetHeader>

                <div className="py-6 space-y-4">
                    {/* Stats */}
                    {stats && (
                        <div className="grid grid-cols-2 gap-4">
                            <Card>
                                <CardContent className="p-4">
                                    <div className="text-2xl font-bold">{stats.total_papers}</div>
                                    <div className="text-xs text-muted-foreground">Papers</div>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardContent className="p-4">
                                    <div className="text-2xl font-bold">{stats.total_pages}</div>
                                    <div className="text-xs text-muted-foreground">Pages</div>
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {/* Search */}
                    <div className="flex gap-2">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <Input
                                placeholder="Search library..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10"
                            />
                        </div>
                        <Button onClick={loadPapers} variant="outline" size="icon">
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        </Button>
                    </div>

                    {/* Papers List */}
                    <ScrollArea className="h-[500px] pr-4">
                        {filteredPapers.length === 0 ? (
                            <div className="text-center py-12 text-muted-foreground">
                                {papers.length === 0 ? 'No papers ingested yet' : 'No papers match your search'}
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {filteredPapers.map((paper) => (
                                    <Card key={paper.arxiv_id} className="hover:border-primary/50 transition-colors">
                                        <CardHeader className="p-4 pb-2">
                                            <div className="flex items-start justify-between gap-2">
                                                <div className="flex-1">
                                                    <CardTitle className="text-sm font-semibold line-clamp-2">
                                                        {paper.title}
                                                    </CardTitle>
                                                    <p className="text-xs text-muted-foreground mt-1">
                                                        {paper.authors.slice(0, 2).join(', ')}
                                                        {paper.authors.length > 2 && ` +${paper.authors.length - 2} more`}
                                                    </p>
                                                </div>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-8 w-8"
                                                    onClick={() => handleDelete(paper.arxiv_id)}
                                                >
                                                    <Trash2 className="w-4 h-4 text-destructive" />
                                                </Button>
                                            </div>
                                        </CardHeader>
                                        <CardContent className="p-4 pt-2">
                                            <p className="text-xs text-muted-foreground line-clamp-2">
                                                {paper.summary}
                                            </p>
                                            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                                <span>ArXiv: {paper.arxiv_id}</span>
                                                <span>•</span>
                                                <span>{paper.pages} pages</span>
                                                <span>•</span>
                                                <span>{new Date(paper.ingested_at).toLocaleDateString()}</span>
                                            </div>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                className="mt-2 w-full"
                                                onClick={() => handleCopyBibtex(paper.arxiv_id)}
                                            >
                                                <Copy className="w-3 h-3 mr-2" />
                                                Copy BibTeX
                                            </Button>
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
