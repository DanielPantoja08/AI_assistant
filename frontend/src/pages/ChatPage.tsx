import { useCallback, useEffect, useRef, useState } from "react";
import { Plus, StopCircle } from "lucide-react";
import {
  streamMessage,
  endSession,
  getChatHistory,
  getOrCreateSessionId,
  saveSessionId,
  clearSessionId,
  type HistoryMessage,
} from "@/lib/api";
import ChatMessage, { TypingIndicator, type Message } from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState(() => getOrCreateSessionId());
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    let cancelled = false;
    async function hydrateHistory() {
      try {
        const history = await getChatHistory(sessionId);
        if (!cancelled && history.length > 0) {
          const hydrated = history.map((m: HistoryMessage) => ({
            id: crypto.randomUUID(),
            role: m.role,
            content: m.content,
            timestamp: new Date(),
          }));
          setMessages(hydrated);
        }
      } catch {
        // silently ignore — new session has no history
      }
    }
    void hydrateHistory();
    return () => { cancelled = true; };
  }, [sessionId]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput("");

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    const botId = crypto.randomUUID();
    const botMsg: Message = {
      id: botId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isStreaming: true,
    };
    setMessages((prev) => [...prev, botMsg]);

    try {
      await streamMessage(text, sessionId, (chunk) => {
        setMessages((prev) =>
          prev.map((m) => (m.id === botId ? { ...m, content: m.content + chunk } : m))
        );
      });
      setMessages((prev) =>
        prev.map((m) => (m.id === botId ? { ...m, isStreaming: false } : m))
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === botId
            ? { ...m, content: "Lo siento, ocurrió un error. Por favor intenta de nuevo.", isStreaming: false }
            : m
        )
      );
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, sessionId]);

  async function handleNewSession() {
    const newId = crypto.randomUUID();
    saveSessionId(newId);
    setMessages([]);
    setSessionId(newId);
  }

  async function handleEndSession() {
    try {
      await endSession(sessionId);
    } catch {
      // session may already be ended
    }
    clearSessionId();
    const newId = crypto.randomUUID();
    saveSessionId(newId);
    setMessages([]);
    setSessionId(newId);
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <header className="hidden lg:flex items-center justify-between border-b border-border-soft bg-white px-6 py-3">
        <h1 className="font-display text-lg font-semibold text-slate-800">Chat</h1>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleNewSession}>
            <Plus size={16} />
            Nueva sesión
          </Button>
          <Button variant="ghost" size="sm" onClick={handleEndSession} className="text-muted-text">
            <StopCircle size={16} />
            Finalizar sesión
          </Button>
        </div>
      </header>

      {/* Mobile session controls */}
      <div className="flex gap-2 border-b border-border-soft bg-white px-4 py-2 lg:hidden">
        <Button variant="outline" size="sm" onClick={handleNewSession} className="flex-1">
          <Plus size={14} />
          Nueva sesión
        </Button>
        <Button variant="ghost" size="sm" onClick={handleEndSession} className="text-muted-text">
          <StopCircle size={14} />
          Finalizar
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <div className="text-center space-y-2 px-8">
              <p className="text-muted-text text-sm">
                Hola, estoy aquí para escucharte.
              </p>
              <p className="text-muted-text text-xs">
                Escribe tu mensaje para comenzar.
              </p>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={msg.id}>
            {i > 0 &&
              messages[i - 1].role !== msg.role && (
                <Separator className="my-1 mx-4 opacity-30" />
              )}
            <ChatMessage message={msg} />
          </div>
        ))}
        {isLoading && messages.at(-1)?.role !== "assistant" && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput
        value={input}
        onChange={setInput}
        onSend={handleSend}
        disabled={isLoading}
      />
    </div>
  );
}
