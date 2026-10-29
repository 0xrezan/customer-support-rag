import { Button } from "@/shared/ui/button";
import { LogOut } from "lucide-react";
import { useAdminAuth } from "@/features/admin-auth/hooks/useAdminAuth";
import { HealthBadge } from "@/features/health/components/HealthBadge";
import { MetricsCards } from "@/features/metrics/components/MetricsCards";
import { DocumentsToolbar } from "@/features/documents/components/DocumentsToolbar";
import { UploadDropzone } from "@/features/documents/components/UploadDropzone";
import { DocumentsTable } from "@/features/documents/components/DocumentsTable";
import { DocumentsEmptyState } from "@/features/documents/components/DocumentsEmptyState";
import { DocumentsErrorState } from "@/features/documents/components/DocumentsErrorState";
import { useDocumentsQuery } from "@/features/documents/hooks/useDocumentsQuery";
import { useDocumentsSort } from "@/features/documents/hooks/useDocumentsSort";
import { useDocumentsUrlFilters } from "@/features/documents/hooks/useDocumentsUrlFilters";
import { Skeleton } from "@/shared/ui/skeleton";

function DocumentsSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  );
}

export function AdminDashboardPage() {
  const { logout } = useAdminAuth();
  const documentsQuery = useDocumentsQuery();
  const { filter: urlFilter, updateFilter: updateUrlFilter } =
    useDocumentsUrlFilters();

  const rawDocs = documentsQuery.data ?? [];
  const {
    sort,
    filter,
    toggleSort,
    updateFilter,
    documents: sortedDocs,
  } = useDocumentsSort({
    documents: rawDocs,
    externalFilter: urlFilter,
    onFilterChange: updateUrlFilter,
  });

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-6xl flex-col gap-6 p-6">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">Admin Dashboard</h1>
          <HealthBadge />
        </div>
        <Button variant="outline" size="sm" onClick={logout}>
          <LogOut className="mr-2 h-4 w-4" />
          Sign out
        </Button>
      </header>

      <MetricsCards />

      <section className="space-y-4">
        <DocumentsToolbar
          filter={filter}
          onFilterChange={updateFilter}
          total={rawDocs.length}
          filtered={sortedDocs.length}
        />
        <UploadDropzone />

        {documentsQuery.isPending && <DocumentsSkeleton />}
        {documentsQuery.isError && <DocumentsErrorState />}
        {documentsQuery.isSuccess && rawDocs.length === 0 && (
          <DocumentsEmptyState />
        )}
        {documentsQuery.isSuccess && rawDocs.length > 0 && (
          <DocumentsTable
            documents={sortedDocs}
            sort={sort}
            onSort={toggleSort}
          />
        )}
      </section>
    </main>
  );
}
