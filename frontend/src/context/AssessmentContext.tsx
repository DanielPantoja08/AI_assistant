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

/** Returns today's date as YYYY-MM-DD in local time */
function todayLocal(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** User-scoped localStorage key so different users don't share assessment state */
function assessmentKey(userId: string): string {
  return `lg_assessment_done_${userId}`;
}

/** Check if assessments were already completed today for this user */
function isCompletedToday(userId: string): boolean {
  return localStorage.getItem(assessmentKey(userId)) === todayLocal();
}

/** Persist today's completion in localStorage for this user */
function saveCompletedToday(userId: string): void {
  localStorage.setItem(assessmentKey(userId), todayLocal());
}

interface AssessmentContextValue {
  /** null = still loading, true = needs to complete, false = already done today */
  assessmentNeeded: boolean | null;
  /** Call after successfully submitting assessments */
  markCompleted: () => void;
}

const AssessmentContext = createContext<AssessmentContextValue | null>(null);

export function AssessmentProvider({ children }: { children: ReactNode }) {
  const { token, user } = useAuth();
  const [assessmentNeeded, setAssessmentNeeded] = useState<boolean | null>(null);

  useEffect(() => {
    // Wait until we have both a token and the resolved user identity
    if (!token || !user) {
      setAssessmentNeeded(null);
      return;
    }

    // Fast path: already completed today for this specific user
    if (isCompletedToday(user.id)) {
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
          if (!status.needed) saveCompletedToday(user.id);
        }
      } catch {
        // If backend is unreachable, assume needed to be safe
        if (!cancelled) setAssessmentNeeded(true);
      }
    })();
    return () => { cancelled = true; };
  }, [token, user]);

  const markCompleted = useCallback(() => {
    if (user) saveCompletedToday(user.id);
    setAssessmentNeeded(false);
  }, [user]);

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
