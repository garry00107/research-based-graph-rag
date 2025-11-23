import axios from 'axios';

const API_URL = '/api';

export interface Citation {
    text: string;
    score: number;
    metadata: any;
}

export interface ChatResponse {
    response: string;
    citations: Citation[];
}

export interface Paper {
    arxiv_id: string;
    title: string;
    authors: string[];
    summary: string;
    published: string;
    pdf_url: string;
}

export const api = {
    search: async (query: string, maxResults: number = 10) => {
        return axios.post<{ status: string, results: Paper[] }>(`${API_URL}/search`, {
            query,
            max_results: maxResults
        });
    },
    ingest: async (arxivId: string) => {
        return axios.post(`${API_URL}/ingest`, { arxiv_id: arxivId });
    },
    ingestBatch: async (arxivIds: string[]) => {
        return axios.post(`${API_URL}/ingest-batch`, { arxiv_ids: arxivIds });
    },
    chat: async (message: string) => {
        return axios.post<ChatResponse>(`${API_URL}/chat`, { message });
    }
};
