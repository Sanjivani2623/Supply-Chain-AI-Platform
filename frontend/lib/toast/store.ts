/**
 * Minimal, dependency-free toast store.
 *
 * This is a plain pub-sub module (not a React context) on purpose: the API
 * client (lib/api/client.ts) is not a component and needs to be able to
 * fire toasts (e.g. "Session expired") from plain async functions. The
 * ToastContainer component subscribes to this store and renders whatever
 * is in it; any code anywhere can call toast.success/error/info.
 */
export type ToastVariant = "success" | "error" | "info";

export interface ToastItem {
  id: string;
  variant: ToastVariant;
  message: string;
}

type Listener = (toasts: ToastItem[]) => void;

let toasts: ToastItem[] = [];
const listeners = new Set<Listener>();

function emit() {
  listeners.forEach((l) => l(toasts));
}

function push(variant: ToastVariant, message: string, durationMs = 4500) {
  const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  toasts = [...toasts, { id, variant, message }];
  emit();
  if (durationMs > 0) {
    setTimeout(() => dismiss(id), durationMs);
  }
  return id;
}

function dismiss(id: string) {
  toasts = toasts.filter((t) => t.id !== id);
  emit();
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  listener(toasts);
  return () => listeners.delete(listener);
}

export const toast = {
  success: (message: string) => push("success", message),
  error: (message: string) => push("error", message, 6000),
  info: (message: string) => push("info", message),
  dismiss,
};
