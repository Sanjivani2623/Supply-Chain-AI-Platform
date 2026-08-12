"use client";
import { useEffect, useState } from "react";
import { apiFetch, logout } from "@/lib/api/client";
import { toast } from "@/lib/toast/store";
import { useRouter } from "next/navigation";

export default function SettingsPage() {
  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    apiFetch("/api/v1/auth/me")
      .then(setUser)
      .catch((e: any) => {
        if (!e.handled) toast.error(`Couldn't load profile: ${e.message}`);
      });
  }, []);

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-slate-500 text-sm">Account and platform configuration</p>
      </div>
      {user && (
        <div className="kpi-card space-y-2 text-sm">
          <div><span className="text-slate-500">Name:</span> {user.name}</div>
          <div><span className="text-slate-500">Email:</span> {user.email}</div>
          <div><span className="text-slate-500">Role:</span> {user.role}</div>
        </div>
      )}
      <button
        onClick={() => { logout(); toast.info("Logged out"); router.push("/login"); }}
        className="bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-900"
      >
        Log out
      </button>
    </div>
  );
}
