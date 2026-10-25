import { X } from "lucide-react";
import { useToast } from "@/hooks/useToast";
import { cn } from "@/lib/utils";

export function ToastViewport() {
  const { toasts, dismiss } = useToast();

  return (
    <div className="pointer-events-none fixed right-6 top-6 z-50 flex w-96 max-w-[calc(100%-2rem)] flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "pointer-events-auto flex items-start justify-between gap-3 rounded-md border px-4 py-3 text-sm shadow-lg",
            {
              "border-success/30 bg-card text-foreground":
                toast.variant === "success",
              "border-destructive/40 bg-card text-foreground":
                toast.variant === "error",
              "border-border bg-card text-foreground": toast.variant === "info",
            }
          )}
        >
          <p>{toast.message}</p>
          <button
            type="button"
            onClick={() => dismiss(toast.id)}
            className="text-muted-foreground hover:text-foreground"
            aria-label="Dismiss notification"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
