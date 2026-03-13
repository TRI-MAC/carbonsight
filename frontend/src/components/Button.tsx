import type { ButtonHTMLAttributes, CSSProperties } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
}

const variants: Record<string, CSSProperties> = {
  primary: {
    background: "var(--accent-blue)",
    color: "#fff",
    border: "1px solid var(--accent-blue)",
  },
  secondary: {
    background: "var(--bg-elevated)",
    color: "var(--text-primary)",
    border: "1px solid var(--border-default)",
  },
  ghost: {
    background: "transparent",
    color: "var(--text-secondary)",
    border: "1px solid transparent",
  },
  danger: {
    background: "rgba(248, 113, 113, 0.1)",
    color: "var(--accent-red)",
    border: "1px solid rgba(248, 113, 113, 0.3)",
  },
};

export default function Button({
  variant = "secondary",
  size = "md",
  style,
  ...props
}: ButtonProps) {
  return (
    <button
      style={{
        ...variants[variant],
        padding: size === "sm" ? "4px 10px" : "8px 16px",
        fontSize: size === "sm" ? 12 : 13,
        borderRadius: "var(--radius-md)",
        fontWeight: 500,
        cursor: "pointer",
        transition: "all 0.15s ease",
        opacity: props.disabled ? 0.5 : 1,
        ...style,
      }}
      {...props}
    />
  );
}
