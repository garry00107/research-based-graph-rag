"use client";

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sparkles, ExternalLink } from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

interface Recommendation {
    arxiv_id: string;
    title: string;
    authors: string[];
    summary: string;
    score: number;
}

interface RecommendationsProps {
    query?: string;
    arxivId?: string;
    type: 'query' | 'similar' | 'citations';
}

export function Recommendations({ query, arxivId, type }: RecommendationsProps) {
    const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
    const [loading, setLoading] = useState(false);
    const [loaded, setLoaded] = useState(false);

    const loadRecommendations = async () => {
        setLoading(true);
        try {
            let url = '';
            if (type === 'query' && query) {
                url = `${API_URL}/recommendations/query?query=${encodeURIComponent(query)}&top_k=3`;
            } else if (type === 'similar' && arxivId) {
                url = `${API_URL}/recommendations/similar/${arxivId}?top_k=3`;
            } else if (type === 'citations' && arxivId) {
                url = `${API_URL}/recommendations/citations/${arxivId}?top_k=3`;
            }

            const response = await axios.get(url);
            setRecommendations(response.data.recommendations || []);
            setLoaded(true);
        } catch (error) {
            console.error('Error loading recommendations:', error);
        }
        setLoading(false);
    };

    if (!loaded) {
        return (
            <Button
                variant="outline"
                size="sm"
                onClick={loadRecommendations}
                disabled={loading}
                className="w-full"
            >
                <Sparkles className="w-4 h-4 mr-2" />
                {loading ? 'Loading...' : 'Show Related Papers'}
            </Button>
        );
    }

    if (recommendations.length === 0) {
        return (
            <div className="text-sm text-muted-foreground text-center py-4">
                No recommendations available
            </div>
        );
    }

    return (
        <div className="space-y-2">
            <p className="text-xs font-semibold flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> Related Papers
            </p>
            {recommendations.map((rec, idx) => (
                <Card key={idx} className="hover:border-primary/50 transition-colors">
                    <CardContent className="p-3">
                        <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                                <p className="text-sm font-medium line-clamp-2">{rec.title}</p>
                                <p className="text-xs text-muted-foreground mt-1">
                                    {rec.authors.slice(0, 2).join(', ')}
                                    {rec.authors.length > 2 && ' et al.'}
                                </p>
                            </div>
                            <a
                                href={`https://arxiv.org/abs/${rec.arxiv_id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline shrink-0"
                                title="View on ArXiv"
                            >
                                <ExternalLink className="w-4 h-4" />
                            </a>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                            {rec.summary}
                        </p>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}
