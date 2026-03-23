import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
} from "react";
import type { ReactNode } from "react";

type ToastType = "success" | "info" | "error";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  toast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType>({
  toast: () => {},
});

export function useToast() {
  return useContext(ToastContext);
}

const COLORS: Record<ToastType, { bg: string; border: string; text: string }> =
  {
    success: {
      bg: "rgba(52, 211, 153, 0.12)",
      border: "rgba(52, 211, 153, 0.3)",
      text: "#34d399",
    },
    info: {
      bg: "rgba(34, 211, 238, 0.12)",
      border: "rgba(34, 211, 238, 0.3)",
      text: "#22d3ee",
    },
    error: {
      bg: "rgba(248, 113, 113, 0.12)",
      border: "rgba(248, 113, 113, 0.3)",
      text: "#f87171",
    },
  };

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const idRef = useRef(0);

  const toast = useCallback((message: string, type: ToastType = "info") => {
    const id = ++idRef.current;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div
        style={{
          position: "fixed",
          bottom: 20,
          right: 20,
          display: "flex",
          flexDirection: "column",
          gap: 8,
          zIndex: 9999,
          pointerEvents: "none",
        }}
      >
        {toasts.map((t) => {
          const c = COLORS[t.type];
          return (
            <div
              key={t.id}
              style={{
                background: c.bg,
                border: `1px solid ${c.border}`,
                borderRadius: "var(--radius-md)",
                padding: "10px 16px",
                fontSize: 13,
                color: c.text,
                fontFamily: "var(--font-body)",
                backdropFilter: "blur(12px)",
                animation: "toast-in 0.2s ease-out",
                maxWidth: 360,
              }}
            >
              {t.message}
            </div>
          );
        })}
      </div>
      <style>{`
        @keyframes toast-in {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </ToastContext.Provider>
  );
}
