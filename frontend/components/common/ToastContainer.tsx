"use client";
import { useEffect, useState } from "react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";
import { subscribe, toast, type ToastItem } from "@/lib/toast/store";

const STYLES: Record<string, string> = {
  success: "bg-emerald-50 border-emerald-200 text-emerald-800",
  error: "bg-red-50 border-red-200 text-red-800",
  info: "bg-blue-50 border-blue-200 text-blue-800",
};

const ICONS: Record<string, any> = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

export default function ToastContainer() {
  const [items, setItems] = useState<ToastItem[]>([]);

  useEffect(() => subscribe(setItems), []);

  if (items.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-80">
      {items.map((t) => {
        const Icon = ICONS[t.variant];
        return (
          <div key={t.id} className={`flex items-start gap-2 border rounded-lg shadow-sm px-4 py-3 text-sm ${STYLES[t.variant]}`}>
            <Icon size={18} className="mt-0.5 shrink-0" />
            <div className="flex-1">{t.message}</div>
            <button onClick={() => toast.dismiss(t.id)} className="opacity-60 hover:opacity-100">
              <X size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
