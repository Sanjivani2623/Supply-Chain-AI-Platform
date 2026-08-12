"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Sidebar from "@/components/common/Sidebar";
import NotificationBell from "@/components/common/NotificationBell";
import { isLoggedIn } from "@/lib/api/client";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isLoginPage = pathname === "/login";
  const [checked, setChecked] = useState(false);

  // Client-side auth guard: bounce to /login immediately if there's no
  // token at all, instead of letting every card on the page fail with a
  // 401 first.
  useEffect(() => {
    if (isLoginPage) {
      setChecked(true);
      return;
    }
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    setChecked(true);
  }, [isLoginPage, pathname, router]);

  if (isLoginPage) {
    return <>{children}</>;
  }

  if (!checked) {
    return null;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <header className="h-16 border-b border-slate-200 bg-white flex items-center justify-end px-6 gap-4">
          <NotificationBell />
        </header>
        <main className="flex-1 p-8 max-w-7xl mx-auto w-full">{children}</main>
      </div>
    </div>
  );
}
