import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: "~" },
  { to: "/graph", label: "Causal Graph", icon: "\u25C7" },
  { to: "/scenarios", label: "Scenarios", icon: "\u25A1" },
  { to: "/compare", label: "Compare", icon: "\u2194" },
  { to: "/sensitivity", label: "Sensitivity", icon: "\u2261" },
  { to: "/demo", label: "Demo", icon: "\u25B6" },
];

export default function Layout() {
  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      <nav
        style={{
          width: 220,
          minWidth: 220,
          background: "var(--bg-secondary)",
          borderRight: "1px solid var(--border-subtle)",
          display: "flex",
          flexDirection: "column",
          padding: "0",
        }}
      >
        <div
          style={{
            padding: "24px 20px 20px",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 22,
              fontWeight: 700,
              color: "var(--text-primary)",
              letterSpacing: "-0.5px",
              lineHeight: 1.2,
            }}
          >
            Carbon
            <span style={{ color: "var(--accent-cyan)" }}>Sight</span>
          </h1>
          <p
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              color: "var(--text-muted)",
              marginTop: 4,
              letterSpacing: "0.5px",
              textTransform: "uppercase",
            }}
          >
            Fleet Carbon Observatory
          </p>
        </div>
        <div style={{ padding: "12px 8px", flex: 1 }}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              style={({ isActive }) => ({
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 12px",
                borderRadius: "var(--radius-md)",
                color: isActive
                  ? "var(--text-primary)"
                  : "var(--text-secondary)",
                background: isActive ? "var(--bg-elevated)" : "transparent",
                textDecoration: "none",
                fontSize: 13,
                fontWeight: isActive ? 500 : 400,
                marginBottom: 2,
                transition: "all 0.15s ease",
              })}
            >
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 14,
                  width: 20,
                  textAlign: "center",
                  opacity: 0.7,
                }}
              >
                {item.icon}
              </span>
              {item.label}
            </NavLink>
          ))}
        </div>
        <div
          style={{
            padding: "12px 16px",
            borderTop: "1px solid var(--border-subtle)",
            fontFamily: "var(--font-mono)",
            fontSize: 10,
            color: "var(--text-muted)",
          }}
        >
          v0.1.0 / 2024-2034
        </div>
      </nav>
      <main
        style={{
          flex: 1,
          overflow: "auto",
          background: "var(--bg-primary)",
        }}
      >
        <Outlet />
      </main>
    </div>
  );
}
