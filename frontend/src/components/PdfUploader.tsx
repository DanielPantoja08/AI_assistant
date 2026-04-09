import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { FileUp, X, CheckCircle, AlertCircle, Loader } from "lucide-react";
import { ingestPdf } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { cn } from "@/lib/utils";

const COLLECTIONS = [
  { value: "clinico", label: "Clínico" },
  { value: "pseudociencia", label: "Pseudociencia" },
  { value: "tecnicas_tcc", label: "Técnicas TCC" },
  { value: "emergencia", label: "Emergencia" },
] as const;

type UploadStatus = "idle" | "loading" | "success" | "error";

export interface UploadRecord {
  id: string;
  filename: string;
  collection: string;
  status: "success" | "error";
  message: string;
  date: Date;
}

interface PdfUploaderProps {
  onUploaded: (record: UploadRecord) => void;
}

export default function PdfUploader({ onUploaded }: PdfUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [collection, setCollection] = useState("clinico");
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [message, setMessage] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f && f.type === "application/pdf") {
      setFile(f);
      setStatus("idle");
      setMessage(null);
    }
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && f.type === "application/pdf") {
      setFile(f);
      setStatus("idle");
      setMessage(null);
    }
  }

  async function handleUpload() {
    if (!file) return;
    setStatus("loading");
    setMessage(null);
    try {
      const res = await ingestPdf(file, collection);
      setStatus("success");
      setMessage(`"${res.source_name}" subido a ${res.collection} (${res.chunks} chunks)`);
      onUploaded({
        id: crypto.randomUUID(),
        filename: res.source_name,
        collection: res.collection,
        status: "success",
        message: "Completado",
        date: new Date(),
      });
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Error al subir el archivo");
      onUploaded({
        id: crypto.randomUUID(),
        filename: file.name,
        collection,
        status: "error",
        message: "Fallido",
        date: new Date(),
      });
    }
  }

  const collectionLabel =
    COLLECTIONS.find((c) => c.value === collection)?.label ?? collection;

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={cn(
          "flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-10 cursor-pointer transition-colors",
          isDragging
            ? "border-primary bg-primary-light"
            : "border-border-soft bg-slate-50 hover:border-primary hover:bg-primary-light/50"
        )}
      >
        <FileUp
          size={36}
          className={isDragging ? "text-primary" : "text-slate-400"}
        />
        {file ? (
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <span>{file.name}</span>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
              className="text-slate-400 hover:text-danger"
            >
              <X size={14} />
            </button>
          </div>
        ) : (
          <>
            <p className="text-sm font-medium text-slate-600">
              Arrastra un PDF aquí o haz clic para seleccionar
            </p>
            <p className="text-xs text-muted-text">Solo archivos PDF · Máx. 25 MB</p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {/* Collection selector */}
      <div className="space-y-1.5">
        <Label htmlFor="collection">Colección de destino</Label>
        <Select
          id="collection"
          value={collection}
          onChange={(e) => setCollection(e.target.value)}
        >
          {COLLECTIONS.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </Select>
      </div>

      {/* Upload button */}
      <Button
        onClick={handleUpload}
        disabled={!file || status === "loading"}
        className="w-full"
        size="lg"
      >
        {status === "loading" ? (
          <>
            <Loader size={16} className="animate-spin" />
            Procesando...
          </>
        ) : (
          <>
            <FileUp size={16} />
            Subir documento a {collectionLabel}
          </>
        )}
      </Button>

      {/* Status */}
      {status === "success" && message && (
        <div className="flex items-center gap-2 rounded-lg bg-green-50 border border-green-200 px-4 py-3">
          <CheckCircle size={16} className="text-success shrink-0" />
          <span className="text-sm text-success font-medium">{message}</span>
        </div>
      )}
      {status === "error" && message && (
        <div className="flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 px-4 py-3">
          <AlertCircle size={16} className="text-danger shrink-0" />
          <span className="text-sm text-danger font-medium">{message}</span>
        </div>
      )}
    </div>
  );
}
