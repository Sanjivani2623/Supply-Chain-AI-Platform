"use client";
import { useEffect, useRef, useState } from "react";
import { Bell } from "lucide-react";
import { apiFetch, isLoggedIn } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";
import Badge from "@/components/common/Badge";

interface AlertItem {
  id: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  status: string;
  created_at: string;
}

const POLL_MS = 30000;

export default function NotificationBell() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [open, setOpen] = useState(false);
  const seenIds = useRef<Set<string>>(new Set());
  const firstLoad = useRef(true);
  const containerRef = useRef<HTMLDivElement>(null);

  async function load() {
    if (!isLoggedIn()) return;
    try {
      const data = await apiFetch<AlertItem[]>("/api/v1/alerts");
      if (!firstLoad.current) {
        const newOnes = data.filter((a) => !seenIds.current.has(a.id));
        if (newOnes.length > 0) {
          toast.info(`${newOnes.length} new alert${newOnes.length > 1 ? "s" : ""}: ${newOnes[0].title}`);
        }
      }
      seenIds.current = new Set(data.map((a) => a.id));
      firstLoad.current = false;
      setAlerts(data);
    } catch {
      // silent - the global apiFetch error handling already deals with auth issues
    }
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, POLL_MS);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const openCount = alerts.filter((a) => a.status === "OPEN").length;

  return (
    <div className="relative" ref={containerRef}>
      <button onClick={() => setOpen((o) => !o)} className="relative p-2 rounded-lg hover:bg-slate-100">
        <Bell size={20} className="text-slate-600" />
        {openCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[10px] leading-none rounded-full min-w-[16px] h-4 flex items-center justify-center px-1">
            {openCount > 99 ? "99+" : openCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-96 max-h-[28rem] overflow-y-auto bg-white border border-slate-200 rounded-xl shadow-lg z-50">
          <div className="px-4 py-3 border-b text-sm font-medium">Notifications</div>
          {alerts.length === 0 && <div className="px-4 py-6 text-sm text-slate-400 text-center">No alerts yet</div>}
          {alerts.slice(0, 20).map((a) => (
            <div key={a.id} className="px-4 py-3 border-b last:border-0 hover:bg-slate-50">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium">{a.title}</span>
                <Badge level={a.severity} />
              </div>
              <div className="text-xs text-slate-500 mt-1">{a.message}</div>
              <div className="text-[11px] text-slate-400 mt-1">{new Date(a.created_at).toLocaleString()}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
