"use client";
import { useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";
import { Send } from "lucide-react";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  toolTrace?: any[];
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Ask me about disruptions, supplier risk, inventory, or reorder recommendations. I only answer using live data from the platform's tools." },
  ]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  async function send() {
    if (!input.trim()) return;
    const userMsg: ChatMessage = { role: "user", content: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const data = await apiFetch<{ conversation_id: string; response: string; tool_trace: any[] }>("/api/v1/chat", {
        method: "POST",
        body: JSON.stringify({ conversation_id: conversationId, message: userMsg.content }),
      });
      setConversationId(data.conversation_id);
      setMessages((m) => [...m, { role: "assistant", content: data.response, toolTrace: data.tool_trace }]);
      if (data.response?.includes("not configured")) {
        toast.info("No LLM provider configured — set LLM_PROVIDER + the matching API key in backend/.env");
      } else if (data.response?.includes("API error")) {
        toast.error("The LLM provider returned an error — check backend/.env and the backend logs.");
      }
    } catch (e: any) {
      if (!e.handled) {
        toast.error(e.message);
        setMessages((m) => [...m, { role: "assistant", content: `Error: ${e.message}` }]);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div>
        <h1 className="text-2xl font-semibold">AI Supply Chain Assistant</h1>
        <p className="text-slate-500 text-sm mb-4">Tool-calling agent grounded in live database + RAG evidence</p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 kpi-card">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-lg rounded-xl px-4 py-3 text-sm ${m.role === "user" ? "bg-brand-600 text-white" : "bg-slate-100"}`}>
              <div className="whitespace-pre-wrap">{m.content}</div>
              {m.toolTrace && m.toolTrace.length > 0 && (
                <details className="mt-2 text-xs opacity-80">
                  <summary className="cursor-pointer">Tool calls ({m.toolTrace.length})</summary>
                  <pre className="mt-1 overflow-x-auto">{JSON.stringify(m.toolTrace, null, 2)}</pre>
                </details>
              )}
            </div>
          </div>
        ))}
        {loading && <div className="text-sm text-slate-400">Thinking…</div>}
      </div>

      <div className="mt-4 flex gap-2">
        <input
          className="flex-1 border rounded-lg px-4 py-2"
          placeholder="e.g. Why is SKU-1004 at risk?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button onClick={send} disabled={loading} className="bg-brand-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-brand-700 disabled:opacity-50">
          <Send size={16} /> Send
        </button>
      </div>
    </div>
  );
}
