import { BrainCircuit } from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const time = message.timestamp.toLocaleTimeString("es", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className={cn("flex gap-3 px-4 py-2", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-white mt-1">
          <BrainCircuit size={16} />
        </div>
      )}

      <div className={cn("flex flex-col gap-1 max-w-[72%]", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
            isUser
              ? "bg-user-bubble text-slate-800 rounded-tr-sm whitespace-pre-wrap"
              : "bg-white border border-border-soft text-slate-700 rounded-tl-sm shadow-sm prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:my-2 prose-strong:text-slate-800 prose-code:bg-slate-100 prose-code:px-1 prose-code:rounded prose-code:text-slate-700 prose-pre:bg-slate-100 prose-pre:text-slate-700"
          )}
        >
          {isUser ? (
            message.content
          ) : message.isStreaming ? (
            <span className="whitespace-pre-wrap">{message.content}</span>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}
        </div>
        <span className="text-[11px] text-muted-text px-1">{time}</span>
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex gap-3 px-4 py-2">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-white mt-1">
        <BrainCircuit size={16} />
      </div>
      <div className="flex items-center gap-1 bg-white border border-border-soft rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </div>
  );
}
