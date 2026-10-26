import { Link } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/common/Card";
import { Badge } from "@/components/common/Badge";
import { Spinner } from "@/components/common/Spinner";
import { useDockerfileHistory } from "@/api/queries";

export function History() {
  const { data, isLoading, error } = useDockerfileHistory();
  const items = data?.items ?? [];

  return (
    <div>
      <Header
        title="History"
        description="Generated, optimized, and repaired Dockerfiles for this session"
      />
      <div className="p-8">
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
              No Dockerfiles generated yet. Create one from New Dockerfile.
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
  if (status === "edited" || status === "repaired") {
    return "warning";
  }
  if (status === "optimized") {
    return "default";
  }
  return "success";
}
