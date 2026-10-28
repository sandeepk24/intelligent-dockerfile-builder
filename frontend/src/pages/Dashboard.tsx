import {
  Container,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/common/Card";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Spinner } from "@/components/common/Spinner";
import { formatBytes, formatDuration } from "@/lib/utils";
import { useDockerfileHistory, useHealth, useModels, useSessionStats } from "@/api/queries";

export function Dashboard() {
  const { data: health, isLoading: healthLoading } = useHealth();
  const { data: modelsData, isLoading: modelsLoading } = useModels();
  const { data: history } = useDockerfileHistory();
  const { data: stats } = useSessionStats();
  const generatedCount = stats?.dockerfiles_generated ?? history?.items.length ?? 0;
  const recent = history?.items.slice(0, 5) ?? [];

  return (
    <div>
      <Header
        title="Dashboard"
        description="Generation, validation, and repair metrics"
      >
        <Link to="/new">
          <Button>
            <Container className="h-4 w-4" />
            New Dockerfile
          </Button>
        </Link>
      </Header>

      <div className="space-y-6 p-8">
        {/* Stats cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            icon={Container}
            title="Dockerfiles Generated"
            value={String(generatedCount)}
            description={stats?.persistence === "sqlite" ? "Stored in SQLite" : "This process"}
          />
          <StatsCard
            icon={CheckCircle2}
            title="Successful Builds"
            value={String(stats?.successful_builds ?? 0)}
            description={`${stats?.validations_run ?? 0} validation runs`}
          />
          <StatsCard
            icon={Clock}
            title="Avg Build Time"
            value={formatDuration(stats?.avg_build_time_ms)}
            description={
              stats?.build_success_rate != null
                ? `${Math.round(stats.build_success_rate * 100)}% approved builds passed`
                : "Approved Docker builds"
            }
          />
          <StatsCard
            icon={AlertTriangle}
            title="Repairs Applied"
            value={String(stats?.repairs_applied ?? 0)}
            description={
              stats?.avg_image_size_bytes
                ? `Avg image ${formatBytes(stats.avg_image_size_bytes)}`
                : `${stats?.failed_validations ?? 0} failed validations`
            }
          />
        </div>

        {/* System status */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>System Status</CardTitle>
            </CardHeader>
            <CardContent>
              {healthLoading ? (
                <div className="flex items-center gap-2 py-4">
                  <Spinner size={16} />
                  <span className="text-sm text-muted-foreground">
                    Checking connectivity...
                  </span>
                </div>
              ) : health ? (
                <div className="space-y-3">
                  <StatusRow
                    label="Backend API"
                    status="connected"
                    detail={`v${health.version}`}
                  />
                  <StatusRow
                    label="Ollama LLM"
                    status={
                      health.ollama_connected ? "connected" : "disconnected"
                    }
                    detail={health.ollama_url}
                  />
                  <StatusRow
                    label="Docker"
                    status={health.docker_available ? "connected" : "disconnected"}
                    detail={health.docker_available ? "CLI found" : "not installed"}
                  />
                  <StatusRow
                    label="Hadolint"
                    status={health.hadolint_available ? "connected" : "disconnected"}
                    detail={health.hadolint_available ? "ready" : "lint skipped"}
                  />
                  <StatusRow
                    label="Trivy"
                    status={health.trivy_available ? "connected" : "disconnected"}
                    detail={health.trivy_available ? "optional scan" : "not installed"}
                  />
                  <StatusRow
                    label="Persistence"
                    status={health.persistence === "sqlite" ? "connected" : "disconnected"}
                    detail={health.persistence === "sqlite" ? "SQLite" : "memory"}
                  />
                  {!health.ollama_connected && (
                    <div className="mt-3 rounded-md border border-warning/30 bg-warning/5 p-3">
                      <p className="text-sm text-warning">
                        Ollama is not connected. Start Ollama with{" "}
                        <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                          ollama serve
                        </code>{" "}
                        and pull a model with{" "}
                        <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                          ollama pull codellama:7b
                        </code>
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3">
                  <p className="text-sm text-destructive">
                    Backend is unreachable. Make sure the FastAPI server is
                    running on port 8000.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Available Models</CardTitle>
            </CardHeader>
            <CardContent>
              {modelsLoading ? (
                <div className="flex items-center gap-2 py-4">
                  <Spinner size={16} />
                  <span className="text-sm text-muted-foreground">
                    Loading models...
                  </span>
                </div>
              ) : modelsData && modelsData.models.length > 0 ? (
                <div className="space-y-2">
                  {modelsData.models.map((model) => (
                    <div
                      key={model.name}
                      className="flex items-center justify-between rounded-md border border-border px-3 py-2"
                    >
                      <span className="text-sm font-medium">{model.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {formatSize(model.size)}
                        </span>
                        {model.name === modelsData.default_model && (
                          <Badge variant="default">default</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-4 text-center">
                  <p className="text-sm text-muted-foreground">
                    No models available.{" "}
                    {!health?.ollama_connected
                      ? "Connect Ollama first."
                      : "Pull a model to get started."}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {(stats?.by_language.length || stats?.by_model.length) ? (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <BreakdownCard title="By language" items={stats?.by_language ?? []} />
            <BreakdownCard title="By model" items={stats?.by_model ?? []} />
          </div>
        ) : null}

        {recent.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Latest generation activity</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {recent.map((item) => (
                <Link
                  key={item.id}
                  to={`/workspace/${item.id}`}
                  className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm hover:bg-accent/40"
                >
                  <span>{item.project_name || item.project_id}</span>
                  <span className="text-xs text-muted-foreground">
                    {item.status} · {new Date(item.created_at).toLocaleTimeString()}
                  </span>
                </Link>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Quick actions */}
        <Card>
          <CardHeader>
            <CardTitle>Get Started</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <QuickAction
                title="Generate Dockerfile"
                description="Analyze a project and create an optimized Dockerfile"
                to="/new"
              />
              <QuickAction
                title="View History"
                description="Browse previously generated Dockerfiles"
                to="/history"
              />
              <QuickAction
                title="Configure Settings"
                description="Set up Ollama, Docker, and validation options"
                to="/settings"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatsCard({
  icon: Icon,
  title,
  value,
  description,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  value: string;
  description: string;
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="mt-1 text-3xl font-bold">{value}</p>
            <p className="mt-1 text-xs text-muted-foreground">{description}</p>
          </div>
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
            <Icon className="h-6 w-6 text-primary" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function StatusRow({
  label,
  status,
  detail,
}: {
  label: string;
  status: "connected" | "disconnected";
  detail?: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span
          className={`h-2 w-2 rounded-full ${
            status === "connected" ? "bg-success" : "bg-destructive"
          }`}
        />
        <span className="text-sm">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        {detail && (
          <span className="text-xs text-muted-foreground">{detail}</span>
        )}
        <Badge variant={status === "connected" ? "success" : "destructive"}>
          {status}
        </Badge>
      </div>
    </div>
  );
}

function QuickAction({
  title,
  description,
  to,
}: {
  title: string;
  description: string;
  to: string;
}) {
  return (
    <Link
      to={to}
      className="group flex items-center justify-between rounded-lg border border-border p-4 transition-colors hover:bg-accent/50"
    >
      <div>
        <p className="text-sm font-medium">{title}</p>
        <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      </div>
      <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-1" />
    </Link>
  );
}

function BreakdownCard({
  title,
  items,
}: {
  title: string;
  items: { key: string; count: number }[];
}) {
  const total = items.reduce((sum, item) => sum + item.count, 0) || 1;
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No data yet.</p>
        ) : (
          items.map((item) => (
            <div key={item.key}>
              <div className="mb-1 flex justify-between text-xs">
                <span>{item.key}</span>
                <span className="text-muted-foreground">{item.count}</span>
              </div>
              <div className="h-2 overflow-hidden rounded bg-muted">
                <div
                  className="h-full bg-primary"
                  style={{ width: `${Math.max(8, (item.count / total) * 100)}%` }}
                />
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function formatSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}
