import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/common/Card";
import { Badge } from "@/components/common/Badge";
import { Spinner } from "@/components/common/Spinner";
import { formatBytes } from "@/lib/utils";
import { useDockerfileHistory } from "@/api/queries";

export function History() {
  const [status, setStatus] = useState("");
  const [language, setLanguage] = useState("");
  const [query, setQuery] = useState("");
  const filters = useMemo(
    () => ({
      status: status || undefined,
      language: language || undefined,
      q: query.trim() || undefined,
    }),
    [status, language, query]
  );
  const { data, isLoading, error } = useDockerfileHistory(filters);
  const items = data?.items ?? [];

  return (
    <div>
      <Header
        title="History"
        description="Generated, optimized, and repaired Dockerfiles — persisted across restarts"
      />
      <div className="space-y-4 p-8">
        <div className="flex flex-wrap items-center gap-3">
          <input
            className="h-10 w-56 rounded-md border border-border bg-background px-3 text-sm"
            placeholder="Search project or model"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <select
            className="h-10 rounded-md border border-border bg-background px-3 text-sm"
            value={language}
            onChange={(event) => setLanguage(event.target.value)}
          >
            <option value="">All languages</option>
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
            <option value="go">Go</option>
          </select>
          <select
            className="h-10 rounded-md border border-border bg-background px-3 text-sm"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">All statuses</option>
            <option value="generated">generated</option>
            <option value="optimized">optimized</option>
            <option value="edited">edited</option>
            <option value="repaired">repaired</option>
          </select>
        </div>
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : error ? (
          <p className="text-sm text-destructive">
            {error instanceof Error ? error.message : "Could not load history"}
          </p>
        ) : items.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center text-sm text-muted-foreground">
              No Dockerfiles match these filters.
            </CardContent>
          </Card>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40 text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Project</th>
                  <th className="px-4 py-3 font-medium">Stack</th>
                  <th className="px-4 py-3 font-medium">Model</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Validation</th>
                  <th className="px-4 py-3 font-medium">Image</th>
                  <th className="px-4 py-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className="border-t border-border hover:bg-accent/30">
                    <td className="px-4 py-3">
                      <Link
                        to={`/workspace/${item.id}`}
                        className="font-medium text-primary hover:underline"
                      >
                        {item.project_name || item.project_id}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {[item.language, item.framework].filter(Boolean).join(" / ") || "—"}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{item.model}</td>
                    <td className="px-4 py-3">
                      <Badge variant={historyBadge(item.status)}>
                        {item.status}
                        {item.repair_attempt ? ` #${item.repair_attempt}` : ""}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      {item.last_validation_status ? (
                        <Badge variant={historyBadge(item.last_validation_status)}>
                          {item.last_validation_status}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {formatBytes(item.image_size_bytes)}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function historyBadge(status: string): "success" | "warning" | "destructive" | "default" {
  if (status === "failed") {
    return "destructive";
  }
  if (status === "edited" || status === "repaired" || status === "lint_only") {
    return "warning";
  }
  if (status === "optimized") {
    return "default";
  }
  return "success";
}
