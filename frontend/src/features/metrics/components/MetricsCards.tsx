import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { FileText, HardDrive, Layers, Activity } from "lucide-react";
import { useDocumentsQuery } from "@/features/documents/hooks/useDocumentsQuery";
import { useHealthQuery } from "@/features/health/hooks/useHealthQuery";
import { formatBytes } from "@/shared/lib/formatBytes";

/**
 * Derives live metrics from the documents query and health check.
 * Will be upgraded to use a dedicated metrics endpoint when the
 * backend provides one.
 */
export function MetricsCards() {
  const documentsQuery = useDocumentsQuery();
  const healthQuery = useHealthQuery();

  const docs = documentsQuery.data ?? [];
  const totalDocs = docs.length;
  const indexedDocs = docs.filter((d) => d.status === "indexed").length;
  const totalChunks = docs.reduce(
    (acc, d) => acc + (d.chunk_count_actual ?? 0),
    0,
  );
  const totalSize = docs.reduce((acc, d) => acc + d.file_size, 0);
  const healthStatus = healthQuery.data?.status === "ok" ? "Healthy" : "---";

  const cards = [
    {
      title: "Total Documents",
      value: totalDocs > 0 ? `${indexedDocs}/${totalDocs}` : "---",
      subtitle:
        totalDocs > 0 ? `${indexedDocs} indexed` : "No documents uploaded",
      icon: FileText,
    },
    {
      title: "Total Chunks",
      value: totalChunks > 0 ? totalChunks.toLocaleString() : "---",
      subtitle: "Indexed vectors",
      icon: Layers,
    },
    {
      title: "Storage Used",
      value: totalSize > 0 ? formatBytes(totalSize) : "---",
      subtitle: "Total file size",
      icon: HardDrive,
    },
    {
      title: "System Health",
      value: healthStatus,
      subtitle: healthQuery.isPending ? "Checking..." : "Backend status",
      icon: Activity,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{card.value}</p>
            <p className="text-xs text-muted-foreground">{card.subtitle}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
