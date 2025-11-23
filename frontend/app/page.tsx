import { ChatInterface } from '@/components/chat-interface';
import { AdminPanel } from '@/components/admin-panel';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-slate-50 dark:bg-slate-950">
      <div className="absolute top-4 right-4">
        <AdminPanel />
      </div>
      <div className="w-full max-w-4xl mb-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight mb-2 bg-gradient-to-r from-green-500 to-emerald-700 bg-clip-text text-transparent">
          NVIDIA Graph RAG
        </h1>
        <p className="text-muted-foreground">
          Ask questions about research papers with graph-based retrieval.
        </p>
      </div>
      <ChatInterface />
    </main>
  );
}
