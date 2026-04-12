import { useCallback, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BrainCircuit,
  ChevronRight,
  ChevronLeft,
  ClipboardCheck,
  ShieldCheck,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import {
  submitAssessments,
  type AssessmentResult,
} from "@/lib/api";
import { useAssessment } from "@/context/AssessmentContext";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// PHQ-9 Data
// ---------------------------------------------------------------------------

const PHQ9_QUESTIONS = [
  "Poco interés o placer en hacer cosas",
  "Sentirse desanimado/a, deprimido/a o sin esperanza",
  "Problemas para dormir o dormir demasiado",
  "Sentirse cansado/a o con poca energía",
  "Poco apetito o comer en exceso",
  "Sentirse mal consigo mismo/a, o sentir que es un fracaso o que se ha fallado a sí mismo/a o a su familia",
  "Dificultad para concentrarse en cosas como leer o ver televisión",
  "Moverse o hablar tan lento que otras personas lo notan, o lo contrario: estar tan inquieto/a que se mueve mucho más de lo normal",
  "Pensamientos de que estaría mejor muerto/a o de hacerse daño de alguna forma",
];

const PHQ9_OPTIONS = [
  { value: 0, label: "Nunca", description: "Ningún día" },
  { value: 1, label: "Varios días", description: "Menos de la mitad de los días" },
  { value: 2, label: "Más de la mitad", description: "Más de la mitad de los días" },
  { value: 3, label: "Casi todos los días", description: "Casi cada día" },
];

// ---------------------------------------------------------------------------
// ASQ Data
// ---------------------------------------------------------------------------

const ASQ_QUESTIONS = [
  "En las últimas semanas, ¿ha deseado estar muerto/a o poder dormirse y no despertar?",
  "En las últimas semanas, ¿ha tenido algún pensamiento de suicidarse?",
  "¿Alguna vez ha intentado suicidarse?",
  "¿Está teniendo pensamientos de suicidio en este momento?",
];

const ASQ_ACUITY_QUESTION =
  "En el último mes, ¿ha tenido algún pensamiento de suicidio con un plan o método específico?";

// ---------------------------------------------------------------------------
// Severity helpers
// ---------------------------------------------------------------------------

function severityLabel(severity: string): { text: string; color: string } {
  switch (severity) {
    case "minimal":
      return { text: "Mínima", color: "text-emerald-600" };
    case "mild":
      return { text: "Leve", color: "text-yellow-600" };
    case "moderate":
      return { text: "Moderada", color: "text-amber-600" };
    case "moderately_severe":
      return { text: "Moderadamente severa", color: "text-orange-600" };
    case "severe":
      return { text: "Severa", color: "text-red-600" };
    default:
      return { text: severity, color: "text-slate-600" };
  }
}

function asqLabel(result: string): { text: string; color: string; icon: typeof CheckCircle2 } {
  switch (result) {
    case "negative":
      return { text: "Negativo", color: "text-emerald-600", icon: CheckCircle2 };
    case "positive_non_acute":
      return { text: "Positivo — No agudo", color: "text-amber-600", icon: AlertTriangle };
    case "positive_acute":
      return { text: "Positivo — Agudo", color: "text-red-600", icon: AlertTriangle };
    default:
      return { text: result, color: "text-slate-600", icon: CheckCircle2 };
  }
}

// ---------------------------------------------------------------------------
// Steps: welcome → phq9 → asq → submitting → results
// ---------------------------------------------------------------------------

type Step = "welcome" | "phq9" | "asq" | "submitting" | "results";

export default function AssessmentPage() {
  const navigate = useNavigate();
  const { assessmentNeeded, markCompleted } = useAssessment();

  // Step tracking
  const [step, setStep] = useState<Step>("welcome");

  // PHQ-9 state: one answer per question (-1 = unanswered)
  const [phq9Answers, setPhq9Answers] = useState<number[]>(
    () => new Array(9).fill(-1) as number[]
  );
  const [phq9Index, setPhq9Index] = useState(0);

  // ASQ state
  const [asqAnswers, setAsqAnswers] = useState<boolean[]>(
    () => new Array(4).fill(false) as boolean[]
  );
  const [asqIndex, setAsqIndex] = useState(0);
  const [asqAcuity, setAsqAcuity] = useState<boolean | null>(null);
  const [showAcuity, setShowAcuity] = useState(false);

  // Result
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fade transition helper
  const [fade, setFade] = useState(true);

  // If assessments already done, redirect to chat
  if (assessmentNeeded === false) {
    navigate("/chat", { replace: true });
    return null;
  }

  // Progress calculation
  const progress = useMemo(() => {
    if (step === "welcome") return 0;
    if (step === "phq9") {
      const answered = phq9Answers.filter((a) => a >= 0).length;
      return (answered / 9) * 50; // PHQ-9 = first 50%
    }
    if (step === "asq") {
      const asqProgress = ((asqIndex + (showAcuity ? 0.5 : 0)) / (showAcuity ? 5 : 4)) * 50;
      return 50 + asqProgress; // ASQ = second 50%
    }
    return 100;
  }, [step, phq9Answers, asqIndex, showAcuity]);

  // Animated step transition
  const transitionTo = useCallback(
    (nextStep: Step) => {
      setFade(false);
      setTimeout(() => {
        setStep(nextStep);
        setFade(true);
      }, 250);
    },
    []
  );

  // PHQ-9 handlers
  function handlePhq9Answer(value: number) {
    const updated = [...phq9Answers];
    updated[phq9Index] = value;
    setPhq9Answers(updated);

    // Auto‑advance after a brief delay
    setTimeout(() => {
      if (phq9Index < 8) {
        setFade(false);
        setTimeout(() => {
          setPhq9Index(phq9Index + 1);
          setFade(true);
        }, 200);
      }
    }, 300);
  }

  function handlePhq9Next() {
    if (phq9Index < 8) {
      setFade(false);
      setTimeout(() => {
        setPhq9Index(phq9Index + 1);
        setFade(true);
      }, 200);
    } else {
      transitionTo("asq");
    }
  }

  function handlePhq9Back() {
    if (phq9Index > 0) {
      setFade(false);
      setTimeout(() => {
        setPhq9Index(phq9Index - 1);
        setFade(true);
      }, 200);
    } else {
      transitionTo("welcome");
    }
  }

  // ASQ handlers
  function handleAsqAnswer(value: boolean) {
    const updated = [...asqAnswers];
    updated[asqIndex] = value;
    setAsqAnswers(updated);

    setTimeout(() => {
      if (asqIndex < 3) {
        setFade(false);
        setTimeout(() => {
          setAsqIndex(asqIndex + 1);
          setFade(true);
        }, 200);
      } else {
        // Check if any positive → show acuity
        const any = updated.some(Boolean);
        if (any) {
          setFade(false);
          setTimeout(() => {
            setShowAcuity(true);
            setFade(true);
          }, 200);
        }
      }
    }, 300);
  }

  function handleAsqBack() {
    if (showAcuity) {
      setFade(false);
      setTimeout(() => {
        setShowAcuity(false);
        setAsqIndex(3);
        setFade(true);
      }, 200);
    } else if (asqIndex > 0) {
      setFade(false);
      setTimeout(() => {
        setAsqIndex(asqIndex - 1);
        setFade(true);
      }, 200);
    } else {
      setPhq9Index(8);
      transitionTo("phq9");
    }
  }

  // Submit assessments
  async function handleSubmit() {
    setError(null);
    transitionTo("submitting");
    try {
      const anyPositive = asqAnswers.some(Boolean);
      const res = await submitAssessments({
        phq9_answers: phq9Answers,
        asq_answers: asqAnswers,
        asq_acuity_answer: anyPositive ? asqAcuity : null,
      });
      setResult(res);
      markCompleted();
      transitionTo("results");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al enviar evaluaciones");
      transitionTo("asq");
    }
  }

  // Can the ASQ be submitted?
  const canSubmitAsq = useMemo(() => {
    const allAnswered = asqIndex >= 3;
    const anyPositive = asqAnswers.some(Boolean);
    if (anyPositive) return showAcuity && asqAcuity !== null;
    return allAnswered;
  }, [asqIndex, asqAnswers, showAcuity, asqAcuity]);

  // Loading state — context handles the initial check
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

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <header className="hidden lg:flex items-center justify-between border-b border-border-soft bg-white px-6 py-3">
        <h1 className="font-display text-lg font-semibold text-slate-800">
          Evaluación Diaria
        </h1>
        <div className="flex items-center gap-2 text-sm text-muted-text">
          <ClipboardCheck size={16} />
          Cuestionarios clínicos
        </div>
      </header>

      {/* Progress bar */}
      <div className="h-1 w-full bg-slate-200">
        <div
          className="assessment-progress-bar h-full"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:py-12">
          <div
            className={cn(
              "assessment-fade",
              fade ? "assessment-fade-in" : "assessment-fade-out"
            )}
          >
            {/* ───────────── WELCOME ───────────── */}
            {step === "welcome" && (
              <div className="assessment-card text-center">
                <div className="flex justify-center mb-6">
                  <div className="assessment-icon-ring">
                    <BrainCircuit size={32} className="text-primary" />
                  </div>
                </div>
                <h2 className="font-display text-2xl font-semibold text-slate-800 mb-3">
                  Evaluación de bienestar
                </h2>
                <p className="text-muted-text text-sm leading-relaxed max-w-md mx-auto mb-6">
                  Antes de iniciar tu sesión, completaremos dos breves cuestionarios
                  clínicos que nos ayudarán a entender mejor cómo te sientes hoy.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
                  <div className="assessment-info-chip">
                    <ClipboardCheck size={16} className="text-primary shrink-0" />
                    <div className="text-left">
                      <p className="text-sm font-medium text-slate-700">PHQ-9</p>
                      <p className="text-xs text-muted-text">
                        Cuestionario sobre estado anímico
                      </p>
                    </div>
                  </div>
                  <div className="assessment-info-chip">
                    <ShieldCheck size={16} className="text-secondary shrink-0" />
                    <div className="text-left">
                      <p className="text-sm font-medium text-slate-700">ASQ</p>
                      <p className="text-xs text-muted-text">
                        Detección rápida de seguridad
                      </p>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-muted-text mb-6">
                  Tus respuestas son confidenciales y se usan únicamente para
                  personalizar tu acompañamiento.
                </p>
                <Button
                  id="start-assessments"
                  size="lg"
                  onClick={() => transitionTo("phq9")}
                  className="assessment-btn-glow"
                >
                  Comenzar evaluación
                  <ArrowRight size={18} />
                </Button>
              </div>
            )}

            {/* ───────────── PHQ-9 ───────────── */}
            {step === "phq9" && (
              <div className="assessment-card">
                {/* Section label */}
                <div className="flex items-center gap-2 mb-6">
                  <span className="assessment-section-badge bg-primary/10 text-primary">
                    PHQ-9
                  </span>
                  <span className="text-xs text-muted-text">
                    Pregunta {phq9Index + 1} de 9
                  </span>
                </div>
                {/* Subtitle */}
                <p className="text-xs text-muted-text mb-4">
                  Durante las <strong>últimas 2 semanas</strong>, ¿con qué frecuencia le
                  han molestado los siguientes problemas?
                </p>
                {/* Question */}
                <h3 className="font-display text-lg font-semibold text-slate-800 mb-6 leading-snug">
                  {PHQ9_QUESTIONS[phq9Index]}
                </h3>
                {/* Options */}
                <div className="space-y-3 mb-8">
                  {PHQ9_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      id={`phq9-option-${opt.value}`}
                      type="button"
                      className={cn(
                        "assessment-option",
                        phq9Answers[phq9Index] === opt.value &&
                          "assessment-option-selected"
                      )}
                      onClick={() => handlePhq9Answer(opt.value)}
                    >
                      {/* Radio circle */}
                      <span
                        className={cn(
                          "assessment-radio",
                          phq9Answers[phq9Index] === opt.value &&
                            "assessment-radio-checked"
                        )}
                      />
                      <div className="text-left">
                        <p className="text-sm font-medium">{opt.label}</p>
                        <p className="text-xs text-muted-text">{opt.description}</p>
                      </div>
                    </button>
                  ))}
                </div>
                {/* Navigation */}
                <div className="flex justify-between">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handlePhq9Back}
                    className="gap-1"
                  >
                    <ChevronLeft size={16} />
                    Atrás
                  </Button>
                  <Button
                    id="phq9-next"
                    size="sm"
                    onClick={handlePhq9Next}
                    disabled={phq9Answers[phq9Index] < 0}
                    className="gap-1"
                  >
                    {phq9Index < 8 ? "Siguiente" : "Continuar al ASQ"}
                    <ChevronRight size={16} />
                  </Button>
                </div>
                {/* Mini dots for question progress */}
                <div className="flex justify-center gap-1.5 mt-6">
                  {PHQ9_QUESTIONS.map((_, i) => (
                    <span
                      key={i}
                      className={cn(
                        "assessment-dot",
                        i === phq9Index && "assessment-dot-active",
                        i !== phq9Index &&
                          phq9Answers[i] >= 0 &&
                          "assessment-dot-done"
                      )}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* ───────────── ASQ ───────────── */}
            {step === "asq" && (
              <div className="assessment-card">
                <div className="flex items-center gap-2 mb-6">
                  <span className="assessment-section-badge bg-secondary/10 text-secondary">
                    ASQ
                  </span>
                  <span className="text-xs text-muted-text">
                    {showAcuity
                      ? "Pregunta de seguimiento"
                      : `Pregunta ${asqIndex + 1} de 4`}
                  </span>
                </div>

                {!showAcuity ? (
                  <>
                    <h3 className="font-display text-lg font-semibold text-slate-800 mb-6 leading-snug">
                      {ASQ_QUESTIONS[asqIndex]}
                    </h3>
                    <div className="flex gap-3 mb-8">
                      <button
                        id="asq-yes"
                        type="button"
                        className={cn(
                          "assessment-bool-btn",
                          asqAnswers[asqIndex] === true &&
                            "assessment-bool-btn-selected-yes"
                        )}
                        onClick={() => handleAsqAnswer(true)}
                      >
                        Sí
                      </button>
                      <button
                        id="asq-no"
                        type="button"
                        className={cn(
                          "assessment-bool-btn",
                          asqAnswers[asqIndex] === false &&
                            "assessment-bool-btn-selected-no"
                        )}
                        onClick={() => handleAsqAnswer(false)}
                      >
                        No
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex items-start gap-3 mb-4 p-3 rounded-lg bg-amber-50 border border-amber-200">
                      <AlertTriangle size={18} className="text-amber-600 mt-0.5 shrink-0" />
                      <p className="text-xs text-amber-800 leading-relaxed">
                        Tu seguridad es nuestra prioridad. Esta pregunta adicional
                        nos ayuda a darte el mejor apoyo posible.
                      </p>
                    </div>
                    <h3 className="font-display text-lg font-semibold text-slate-800 mb-6 leading-snug">
                      {ASQ_ACUITY_QUESTION}
                    </h3>
                    <div className="flex gap-3 mb-8">
                      <button
                        id="asq-acuity-yes"
                        type="button"
                        className={cn(
                          "assessment-bool-btn",
                          asqAcuity === true &&
                            "assessment-bool-btn-selected-yes"
                        )}
                        onClick={() => setAsqAcuity(true)}
                      >
                        Sí
                      </button>
                      <button
                        id="asq-acuity-no"
                        type="button"
                        className={cn(
                          "assessment-bool-btn",
                          asqAcuity === false &&
                            "assessment-bool-btn-selected-no"
                        )}
                        onClick={() => setAsqAcuity(false)}
                      >
                        No
                      </button>
                    </div>
                  </>
                )}

                {error && (
                  <p className="text-xs text-danger mb-4">{error}</p>
                )}

                <div className="flex justify-between">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleAsqBack}
                    className="gap-1"
                  >
                    <ChevronLeft size={16} />
                    Atrás
                  </Button>
                  {((!showAcuity && asqIndex >= 3 && !asqAnswers.some(Boolean)) ||
                    canSubmitAsq) && (
                    <Button
                      id="submit-assessments"
                      size="sm"
                      onClick={handleSubmit}
                      className="gap-1 assessment-btn-glow"
                    >
                      Enviar evaluación
                      <ChevronRight size={16} />
                    </Button>
                  )}
                </div>

                {/* Mini dots */}
                {!showAcuity && (
                  <div className="flex justify-center gap-1.5 mt-6">
                    {ASQ_QUESTIONS.map((_, i) => (
                      <span
                        key={i}
                        className={cn(
                          "assessment-dot",
                          i === asqIndex && "assessment-dot-active",
                          i < asqIndex && "assessment-dot-done"
                        )}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ───────────── SUBMITTING ───────────── */}
            {step === "submitting" && (
              <div className="assessment-card text-center">
                <div className="flex justify-center mb-6">
                  <div className="assessment-spinner" />
                </div>
                <h3 className="font-display text-lg font-semibold text-slate-800 mb-2">
                  Procesando tus respuestas
                </h3>
                <p className="text-sm text-muted-text">
                  Estamos calculando tus resultados...
                </p>
              </div>
            )}

            {/* ───────────── RESULTS ───────────── */}
            {step === "results" && result && (
              <div className="assessment-card text-center">
                <div className="flex justify-center mb-6">
                  <div className="assessment-icon-ring assessment-icon-ring-success">
                    <CheckCircle2 size={32} className="text-emerald-600" />
                  </div>
                </div>
                <h2 className="font-display text-2xl font-semibold text-slate-800 mb-2">
                  Evaluación completada
                </h2>
                <p className="text-sm text-muted-text mb-8">
                  Aquí tienes un resumen de tus resultados de hoy
                </p>

                <div className="grid gap-4 sm:grid-cols-2 mb-8">
                  {/* PHQ-9 result card */}
                  <div className="assessment-result-card">
                    <p className="text-xs text-muted-text mb-1">
                      PHQ-9 — Estado anímico
                    </p>
                    <p className="text-3xl font-bold text-slate-800 mb-1">
                      {result.phq9_score}
                      <span className="text-sm font-normal text-muted-text">
                        /27
                      </span>
                    </p>
                    <p
                      className={cn(
                        "text-sm font-medium",
                        severityLabel(result.phq9_severity).color
                      )}
                    >
                      Severidad: {severityLabel(result.phq9_severity).text}
                    </p>
                  </div>

                  {/* ASQ result card */}
                  <div className="assessment-result-card">
                    <p className="text-xs text-muted-text mb-1">
                      ASQ — Seguridad
                    </p>
                    {(() => {
                      const info = asqLabel(result.asq_result);
                      const IconComp = info.icon;
                      return (
                        <>
                          <IconComp
                            size={28}
                            className={cn(info.color, "mx-auto mb-1")}
                          />
                          <p className={cn("text-sm font-medium", info.color)}>
                            {info.text}
                          </p>
                        </>
                      );
                    })()}
                  </div>
                </div>

                <Button
                  id="go-to-chat"
                  size="lg"
                  onClick={() => navigate("/chat", { replace: true })}
                  className="assessment-btn-glow"
                >
                  Continuar al chat
                  <ArrowRight size={18} />
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
