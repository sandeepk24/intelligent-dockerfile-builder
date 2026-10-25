import { Header } from "@/components/layout/Header";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/common/Card";
import { Badge } from "@/components/common/Badge";
import { Spinner } from "@/components/common/Spinner";
import { useHealth, useModels } from "@/api/queries";

export function Settings() {
  const { data: health, isLoading: healthLoading } = useHealth();
  const { data: modelsData, isLoading: modelsLoading } = useModels();

  return (
    <div>
      <Header
        title="Settings"
        description="Configure Ollama, Docker, and validation options"
      />
      <div className="space-y-6 p-8">
        {/* Ollama Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Ollama Configuration</CardTitle>
            <CardDescription>
              LLM server connection and model selection
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <SettingRow label="Endpoint" loading={healthLoading}>
              <code className="rounded bg-muted px-2 py-1 text-sm">
                {health?.ollama_url ?? "http://localhost:11434"}
              </code>
              <Badge
                variant={
                  health?.ollama_connected ? "success" : "destructive"
                }
              >
                {health?.ollama_connected ? "connected" : "disconnected"}
              </Badge>
            </SettingRow>

            <SettingRow label="Default Model" loading={modelsLoading}>
              <span className="text-sm">
                {modelsData?.default_model ?? "—"}
              </span>
            </SettingRow>

            <SettingRow label="Available Models" loading={modelsLoading}>
              <span className="text-sm">
                {modelsData?.models.length ?? 0} model(s)
              </span>
            </SettingRow>

            <SettingRow label="Timeout">
              <span className="text-sm">120 seconds</span>
            </SettingRow>
          </CardContent>
        </Card>

        {/* Docker Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Docker Validation</CardTitle>
            <CardDescription>
              Build environment and resource limits
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <SettingRow label="Build Timeout">
              <span className="text-sm">300 seconds</span>
            </SettingRow>
            <SettingRow label="CPU Limit">
              <span className="text-sm">2 cores</span>
            </SettingRow>
            <SettingRow label="Memory Limit">
              <span className="text-sm">2 GB</span>
            </SettingRow>
            <SettingRow label="Max Repair Attempts">
              <span className="text-sm">3</span>
            </SettingRow>
          </CardContent>
        </Card>

        <p className="text-xs text-muted-foreground">
          Settings persistence and editing will be available in Milestone 4.
          Currently using values from <code>.env</code>.
        </p>
      </div>
    </div>
  );
}

function SettingRow({
  label,
  loading,
  children,
}: {
  label: string;
  loading?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between border-b border-border pb-3 last:border-0 last:pb-0">
      <span className="text-sm font-medium text-muted-foreground">
        {label}
      </span>
      <div className="flex items-center gap-2">
        {loading ? <Spinner size={14} /> : children}
      </div>
    </div>
  );
}
