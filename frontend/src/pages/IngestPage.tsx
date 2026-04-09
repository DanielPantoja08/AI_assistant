import { useState } from "react";
import { FileText } from "lucide-react";
import PdfUploader, { type UploadRecord } from "@/components/PdfUploader";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function formatDate(date: Date): string {
  return date.toLocaleString("es", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function IngestPage() {
  const [uploads, setUploads] = useState<UploadRecord[]>([]);

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="mx-auto max-w-2xl space-y-6">
        {/* Header */}
        <div className="hidden lg:block">
          <h1 className="font-display text-xl font-semibold text-slate-800">
            Ingesta de documentos
          </h1>
          <p className="mt-1 text-sm text-muted-text">
            Sube archivos PDF para indexarlos en las colecciones del asistente.
          </p>
        </div>

        {/* Upload card */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Nuevo documento</CardTitle>
          </CardHeader>
          <CardContent>
            <PdfUploader
              onUploaded={(record) =>
                setUploads((prev) => [record, ...prev])
              }
            />
          </CardContent>
        </Card>

        {/* Recent uploads */}
        {uploads.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Cargas recientes</CardTitle>
            </CardHeader>
            <CardContent className="px-0 pb-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border-soft">
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-text uppercase tracking-wide">
                        Archivo
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-text uppercase tracking-wide">
                        Colección
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-text uppercase tracking-wide">
                        Estado
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-text uppercase tracking-wide">
                        Fecha
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {uploads.map((u) => (
                      <tr
                        key={u.id}
                        className="border-b border-border-soft last:border-0 hover:bg-slate-50 transition-colors"
                      >
                        <td className="px-6 py-3">
                          <div className="flex items-center gap-2 text-slate-700">
                            <FileText size={14} className="text-primary shrink-0" />
                            <span className="truncate max-w-[160px]">{u.filename}</span>
                          </div>
                        </td>
                        <td className="px-6 py-3">
                          <Badge variant="default">{u.collection}</Badge>
                        </td>
                        <td className="px-6 py-3">
                          <Badge variant={u.status === "success" ? "success" : "danger"}>
                            {u.message}
                          </Badge>
                        </td>
                        <td className="px-6 py-3 text-muted-text text-xs">
                          {formatDate(u.date)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
