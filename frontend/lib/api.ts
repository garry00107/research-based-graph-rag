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

export const api = {
    ingest: async (arxivId: string) => {
        return axios.post(`${API_URL}/ingest`, { arxiv_id: arxivId });
    },
    chat: async (message: string) => {
        return axios.post<ChatResponse>(`${API_URL}/chat`, { message });
    }
};
