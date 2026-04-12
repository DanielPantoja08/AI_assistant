import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { LogOut, MessageSquare, FileUp, BrainCircuit, Menu, X } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useAssessment } from "@/context/AssessmentContext";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/chat", icon: MessageSquare, label: "Chat" },
  { to: "/ingest", icon: FileUp, label: "Ingesta de documentos" },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const { assessmentNeeded } = useAssessment();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Hide sidebar entirely while assessments are pending
  const hideSidebar = assessmentNeeded === true || assessmentNeeded === null;

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const sidebar = (
    <aside className="flex h-full w-60 flex-col bg-sidebar border-r border-border-soft">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white">
          <BrainCircuit size={18} />
        </div>
        <span className="font-display text-sm font-semibold text-slate-800 leading-tight">
          Asistente<br />Psicológico
        </span>
      </div>

      <Separator />

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                isActive
                  ? "bg-primary-light text-primary font-medium"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-800"
              )
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User */}
      <div className="px-3 pb-4">
        <Separator className="mb-4" />
        <div className="flex items-center gap-3 px-3 mb-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/20 text-primary text-xs font-semibold">
            {user?.email?.[0]?.toUpperCase() ?? "U"}
          </div>
          <p className="truncate text-xs text-slate-600">{user?.email}</p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-2 text-slate-500 hover:text-danger"
          onClick={handleLogout}
        >
          <LogOut size={16} />
          Cerrar sesión
        </Button>
      </div>
    </aside>
  );

  return (
    <div className="flex h-screen bg-page overflow-hidden">
      {/* Desktop sidebar — hidden during assessments */}
      {!hideSidebar && (
        <div className="hidden lg:flex">{sidebar}</div>
      )}

      {/* Mobile sidebar overlay — hidden during assessments */}
      {!hideSidebar && sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full z-50">{sidebar}</div>
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile header — hidden during assessments */}
        {!hideSidebar && (
          <header className="flex items-center gap-3 border-b border-border-soft bg-white px-4 py-3 lg:hidden">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </Button>
            <div className="flex items-center gap-2">
              <BrainCircuit size={18} className="text-primary" />
              <span className="font-display font-semibold text-slate-800 text-sm">
                Asistente Psicológico
              </span>
            </div>
          </header>
        )}

        <main className="flex flex-1 flex-col overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
