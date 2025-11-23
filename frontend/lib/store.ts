import { create } from 'zustand';
import { Citation } from './api';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    citations?: Citation[];
}

interface ChatState {
    messages: Message[];
    addMessage: (msg: Message) => void;
    isLoading: boolean;
    setLoading: (loading: boolean) => void;
}

export const useChatStore = create<ChatState>((set) => ({
    messages: [],
    addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
    isLoading: false,
    setLoading: (loading) => set({ isLoading: loading }),
}));
