import { type KeyboardEvent, useRef } from "react";
import { Send } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
}

export default function ChatInput({ value, onChange, onSend, disabled }: ChatInputProps) {
  const ref = useRef<HTMLTextAreaElement>(null);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && value.trim()) onSend();
    }
  }

  return (
    <div className="border-t border-border-soft bg-white px-4 py-3">
      <p className="text-center text-[11px] text-muted-text mb-2">
        Este asistente es una herramienta de apoyo y no sustituye el diagnóstico de un profesional.
      </p>
      <div className="flex gap-3 items-end">
        <Textarea
          ref={ref}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribe tu mensaje... (Enter para enviar)"
          rows={2}
          disabled={disabled}
          className="flex-1 min-h-[52px] max-h-[140px]"
        />
        <Button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          size="icon"
          className="h-[52px] w-11 shrink-0"
        >
          <Send size={18} />
        </Button>
      </div>
    </div>
  );
}
