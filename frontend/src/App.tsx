import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import PublicLayout from "@/layouts/PublicLayout";
import AppLayout from "@/layouts/AppLayout";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import ChatPage from "@/pages/ChatPage";
import IngestPage from "@/pages/IngestPage";
import type { ReactNode } from "react";

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { token, isLoading } = useAuth();
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-page">
        <div className="flex gap-1">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    );
  }
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

function RootRedirect() {
  const { token, isLoading } = useAuth();
  if (isLoading) return null;
  return <Navigate to={token ? "/chat" : "/login"} replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route element={<PublicLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/ingest" element={<IngestPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
