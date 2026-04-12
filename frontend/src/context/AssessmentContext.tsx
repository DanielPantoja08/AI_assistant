import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { getAssessmentStatus } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const ASSESSMENT_DONE_KEY = "lg_assessment_done";

/** Returns today's date as YYYY-MM-DD in local time */
function todayLocal(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** Check if assessments were already completed today (cached in localStorage) */
function isCompletedToday(): boolean {
  return localStorage.getItem(ASSESSMENT_DONE_KEY) === todayLocal();
}

/** Persist today's completion in localStorage */
function saveCompletedToday(): void {
  localStorage.setItem(ASSESSMENT_DONE_KEY, todayLocal());
}

interface AssessmentContextValue {
  /** null = still loading, true = needs to complete, false = already done today */
  assessmentNeeded: boolean | null;
  /** Call after successfully submitting assessments */
  markCompleted: () => void;
}

const AssessmentContext = createContext<AssessmentContextValue | null>(null);

export function AssessmentProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const [assessmentNeeded, setAssessmentNeeded] = useState<boolean | null>(() => {
    // Fast path: if already completed today, skip the API call
    if (token && isCompletedToday()) return false;
    return null;
  });

  useEffect(() => {
    if (!token) {
      setAssessmentNeeded(null);
      return;
    }

    // Already completed today — no need to ask the backend
    if (isCompletedToday()) {
      setAssessmentNeeded(false);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const status = await getAssessmentStatus();
        if (!cancelled) {
          setAssessmentNeeded(status.needed);
          // If the backend says not needed, cache it locally too
          if (!status.needed) saveCompletedToday();
        }
      } catch {
        // If backend is unreachable, assume needed to be safe
        if (!cancelled) setAssessmentNeeded(true);
      }
    })();
    return () => { cancelled = true; };
  }, [token]);

  const markCompleted = useCallback(() => {
    saveCompletedToday();
    setAssessmentNeeded(false);
  }, []);

  return (
    <AssessmentContext.Provider value={{ assessmentNeeded, markCompleted }}>
      {children}
    </AssessmentContext.Provider>
  );
}

export function useAssessment() {
  const ctx = useContext(AssessmentContext);
  if (!ctx) throw new Error("useAssessment must be used within AssessmentProvider");
  return ctx;
}
