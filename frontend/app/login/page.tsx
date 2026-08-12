"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";

export default function LoginPage() {
  const [email, setEmail] = useState("admin@supplychain-ai.example.com");
  const [password, setPassword] = useState("Admin123!");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      toast.success("Welcome back!");
      router.push("/dashboard");
    } catch (err: any) {
      const msg = err.message || "Login failed";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm w-96">
        <h1 className="text-xl font-semibold mb-1">Supply Chain AI Platform</h1>
        <p className="text-sm text-slate-500 mb-6">Sign in to continue</p>
        {error && <div className="text-sm text-red-600 mb-4">{error}</div>}
        <label className="block text-sm font-medium mb-1">Email</label>
        <input className="w-full border rounded-lg px-3 py-2 mb-4" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label className="block text-sm font-medium mb-1">Password</label>
        <input type="password" className="w-full border rounded-lg px-3 py-2 mb-6" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button disabled={loading} className="w-full bg-brand-600 text-white rounded-lg py-2 font-medium hover:bg-brand-700 disabled:opacity-50">
          {loading ? "Signing in…" : "Sign in"}
        </button>
        <p className="text-xs text-slate-400 mt-4">Default seed admin: admin@supplychain-ai.example.com / Admin123!</p>
      </form>
    </div>
  );
}
