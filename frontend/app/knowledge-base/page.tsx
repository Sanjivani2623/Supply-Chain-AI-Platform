"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";

interface Doc { id: string; name: string; type: string; status: string; created_at: string; }

export default function KnowledgeBasePage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    apiFetch<Doc[]>("/api/v1/documents")
      .then(setDocs)
      .catch((e: any) => {
        if (!e.handled) toast.error(`Couldn't load documents: ${e.message}`);
      })
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function upload() {
    if (!file) return;
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const result = await apiFetch<{ id?: string; name?: string; status?: string; error?: string }>(
        "/api/v1/documents/upload",
        { method: "POST", body: form }
      );
      if (result.error) {
        toast.error(result.error);
      } else {
        toast.success(`Uploaded ${result.name}`);
        setFile(null);
        load();
      }
    } catch (e: any) {
      if (!e.handled) toast.error(e.message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Knowledge Base</h1>
        <p className="text-slate-500 text-sm">Upload SOPs, contracts, and disruption reports for RAG retrieval</p>
      </div>

      <div className="kpi-card flex items-center gap-4">
        <input type="file" accept=".pdf,.docx,.txt,.csv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button onClick={upload} disabled={!file || uploading} className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50">
          {uploading ? "Uploading…" : "Upload"}
        </button>
      </div>
      <p className="text-xs text-slate-400 -mt-4">Note: only .txt and .csv are parsed for search today; .pdf/.docx are stored but not yet extracted.</p>

      <div className="kpi-card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b">
              <th className="py-2 pr-4">Name</th>
              <th className="py-2 pr-4">Type</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2 pr-4">Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id} className="border-b last:border-0">
                <td className="py-2 pr-4">{d.name}</td>
                <td className="py-2 pr-4 uppercase">{d.type}</td>
                <td className="py-2 pr-4">{d.status}</td>
                <td className="py-2 pr-4">{new Date(d.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {!loading && docs.length === 0 && (
              <tr><td colSpan={4} className="py-8 text-center text-slate-400">No documents uploaded yet.</td></tr>
            )}
            {loading && (
              <tr><td colSpan={4} className="py-8 text-center text-slate-400">Loading…</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
