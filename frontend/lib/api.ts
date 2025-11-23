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
    categories?: string[];
}

export interface IngestedPaper {
    arxiv_id: string;
    title: string;
    authors: string[];
    summary: string;
    pages: number;
    ingested_at: string;
    updated_at: string;
}

export const api = {
    search: async (query: string, maxResults: number = 10, category?: string, year?: string) => {
        return axios.post<{ status: string, results: Paper[] }>(`${API_URL}/search`, {
            query,
            max_results: maxResults,
            category,
            year
        });
    },
    ingest: async (arxivId: string) => {
        return axios.post(`${API_URL}/ingest`, { arxiv_id: arxivId });
    },
    ingestBatch: async (arxivIds: string[]) => {
        return axios.post(`${API_URL}/ingest-batch`, { arxiv_ids: arxivIds });
    },
    chat: async (message: string, conversationId: string = 'default') => {
        return axios.post<ChatResponse>(`${API_URL}/chat`, { message, conversation_id: conversationId });
    },
    // Papers Library
    getPapers: async () => {
        return axios.get<{ papers: IngestedPaper[], stats: any }>(`${API_URL}/papers`);
    },
    getPaper: async (arxivId: string) => {
        return axios.get<IngestedPaper>(`${API_URL}/papers/${arxivId}`);
    },
    deletePaper: async (arxivId: string) => {
        return axios.delete(`${API_URL}/papers/${arxivId}`);
    },
    searchLibrary: async (query: string) => {
        return axios.get(`${API_URL}/papers/search/${query}`);
    },
    // Chat History
    getChatHistory: async (conversationId: string = 'default') => {
        return axios.get(`${API_URL}/chat-history/${conversationId}`);
    },
    clearChatHistory: async (conversationId: string = 'default') => {
        return axios.delete(`${API_URL}/chat-history/${conversationId}`);
    }
};
