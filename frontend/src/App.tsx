import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { AssessmentProvider, useAssessment } from "@/context/AssessmentContext";
import PublicLayout from "@/layouts/PublicLayout";
import AppLayout from "@/layouts/AppLayout";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import ChatPage from "@/pages/ChatPage";
import IngestPage from "@/pages/IngestPage";
import AssessmentPage from "@/pages/AssessmentPage";
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

/** Blocks access to chat/ingest until assessments are done */
function RequireAssessment({ children }: { children: ReactNode }) {
  const { assessmentNeeded } = useAssessment();

  // Still loading — show spinner
  if (assessmentNeeded === null) {
    return (
      <div className="flex h-full items-center justify-center bg-page">
        <div className="flex gap-1">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    );
  }

  // Assessments pending — redirect
  if (assessmentNeeded) {
    return <Navigate to="/assessments" replace />;
  }

  return <>{children}</>;
}

function RootRedirect() {
  const { token, isLoading } = useAuth();
  if (isLoading) return null;
  return <Navigate to={token ? "/assessments" : "/login"} replace />;
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
              <AssessmentProvider>
                <AppLayout />
              </AssessmentProvider>
            </ProtectedRoute>
          }
        >
          <Route path="/assessments" element={<AssessmentPage />} />
          <Route path="/chat" element={<RequireAssessment><ChatPage /></RequireAssessment>} />
          <Route path="/ingest" element={<RequireAssessment><IngestPage /></RequireAssessment>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
