"use client";

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, Clock, Server, BarChart3 } from 'lucide-react';

interface AnalyticsData {
    total_requests: number;
    avg_latency_ms: number;
    status_codes: Record<string, number>;
    endpoints: Record<string, number>;
    cache_stats: any;
}

export function AnalyticsDashboard() {
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await api.getAnalytics();
                setData(res.data);
            } catch (error) {
                console.error("Failed to fetch analytics:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        // Refresh every 30 seconds
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return <div className="p-8 text-center text-muted-foreground">Loading analytics...</div>;
    }

    if (!data) {
        return <div className="p-8 text-center text-red-500">Failed to load analytics data.</div>;
    }

    return (
        <div className="p-6 space-y-6 max-w-6xl mx-auto">
            <h2 className="text-2xl font-bold flex items-center gap-2">
                <BarChart3 className="w-6 h-6" /> System Analytics
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{data.total_requests}</div>
                        <p className="text-xs text-muted-foreground">Lifetime API calls</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
                        <Clock className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{data.avg_latency_ms}ms</div>
                        <p className="text-xs text-muted-foreground">Per request average</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Cache Hits</CardTitle>
                        <Server className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{data.cache_stats?.hits || 0}</div>
                        <p className="text-xs text-muted-foreground">
                            Misses: {data.cache_stats?.misses || 0}
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {(() => {
                                const errors = Object.entries(data.status_codes)
                                    .filter(([code]) => code.startsWith('4') || code.startsWith('5'))
                                    .reduce((acc, [, count]) => acc + count, 0);
                                const rate = data.total_requests > 0 ? (errors / data.total_requests) * 100 : 0;
                                return `${rate.toFixed(1)}%`;
                            })()}
                        </div>
                        <p className="text-xs text-muted-foreground">4xx/5xx responses</p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Top Endpoints</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {Object.entries(data.endpoints)
                                .sort(([, a], [, b]) => b - a)
                                .slice(0, 5)
                                .map(([endpoint, count]) => (
                                    <div key={endpoint} className="flex justify-between items-center text-sm">
                                        <span className="font-mono bg-muted px-2 py-1 rounded">{endpoint}</span>
                                        <span className="font-semibold">{count}</span>
                                    </div>
                                ))}
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Response Codes</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {Object.entries(data.status_codes)
                                .sort(([, a], [, b]) => b - a)
                                .map(([code, count]) => (
                                    <div key={code} className="flex justify-between items-center text-sm">
                                        <span className={`px-2 py-1 rounded font-mono ${code.startsWith('2') ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                                                code.startsWith('4') ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                                                    code.startsWith('5') ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                                                        'bg-muted'
                                            }`}>
                                            {code}
                                        </span>
                                        <span className="font-semibold">{count}</span>
                                    </div>
                                ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
