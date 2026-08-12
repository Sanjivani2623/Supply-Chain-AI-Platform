import type { Metadata } from "next";
import "./globals.css";
import AppShell from "@/components/common/AppShell";
import ToastContainer from "@/components/common/ToastContainer";

export const metadata: Metadata = {
  title: "Supply Chain AI Platform",
  description: "AI-Driven Supply Chain Disruption Predictor & Inventory Optimization",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="text-slate-900">
        <ToastContainer />
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
