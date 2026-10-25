import { useEffect, useState, type ReactNode } from "react";
import { Header } from "@/components/layout/Header";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/common/Card";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Spinner } from "@/components/common/Spinner";
import { useToast } from "@/hooks/useToast";
import { useHealth, useModels, useSettings, useUpdateSettings } from "@/api/queries";

export function Settings() {
  const { push } = useToast();
  const { data: health, isLoading: healthLoading } = useHealth();
  const { data: modelsData } = useModels();
  const { data: settings, isLoading } = useSettings();
  const update = useUpdateSettings();

  const [endpoint, setEndpoint] = useState("");
  const [model, setModel] = useState("");
  const [timeout, setTimeoutSeconds] = useState("120");
  const [repairs, setRepairs] = useState("3");

  useEffect(() => {
    if (!settings) {
      return;
    }
    setEndpoint(settings.ollama_base_url);
    setModel(settings.ollama_default_model);
    setTimeoutSeconds(String(settings.ollama_timeout));
    setRepairs(String(settings.max_repair_attempts));
  }, [settings]);

  async function handleSave() {
    try {
      await update.mutateAsync({
        ollama_base_url: endpoint,
        ollama_default_model: model,
        ollama_timeout: Number(timeout),
        max_repair_attempts: Number(repairs),
      });
      push("Settings saved", "success");
    } catch (error) {
      push(error instanceof Error ? error.message : "Save failed", "error");
    }
  }

  return (
    <div>
      <Header
        title="Settings"
        description="Configure Ollama, Docker, and validation options"
      />
      <div className="space-y-6 p-8">
        <Card>
          <CardHeader>
            <CardTitle>Ollama Configuration</CardTitle>
            <CardDescription>
              LLM server connection and model selection
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? (
              <Spinner />
            ) : (
              <>
                <Field label="Endpoint">
                  <input
                    className="h-10 w-full max-w-md rounded-md border border-border bg-background px-3 text-sm"
                    value={endpoint}
                    onChange={(event) => setEndpoint(event.target.value)}
                  />
                  {healthLoading ? (
                    <Spinner size={14} />
                  ) : (
                    <Badge variant={health?.ollama_connected ? "success" : "destructive"}>
                      {health?.ollama_connected ? "connected" : "disconnected"}
                    </Badge>
                  )}
                </Field>
                <Field label="Default model">
                  <select
                    className="h-10 w-full max-w-md rounded-md border border-border bg-background px-3 text-sm"
                    value={model}
                    onChange={(event) => setModel(event.target.value)}
                  >
                    {model && (
                      <option value={model}>{model}</option>
                    )}
                    {modelsData?.models
                      .filter((item) => item.name !== model)
                      .map((item) => (
                        <option key={item.name} value={item.name}>
                          {item.name}
                        </option>
                      ))}
                  </select>
                </Field>
                <Field label="Timeout (seconds)">
                  <input
                    type="number"
                    min={10}
                    max={600}
                    className="h-10 w-32 rounded-md border border-border bg-background px-3 text-sm"
                    value={timeout}
                    onChange={(event) => setTimeoutSeconds(event.target.value)}
                  />
                </Field>
                <Button onClick={handleSave} disabled={update.isPending}>
                  {update.isPending ? <Spinner size={16} /> : null}
                  Save Ollama settings
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Docker Validation</CardTitle>
            <CardDescription>
              Build environment and resource limits used in Milestone 3
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Field label="Workspace root">
              <code className="rounded bg-muted px-2 py-1 text-xs">
                {settings?.workspace_root}
              </code>
            </Field>
            <Field label="Build timeout">
              <span className="text-sm">{settings?.docker_build_timeout} seconds</span>
            </Field>
            <Field label="CPU limit">
              <span className="text-sm">{settings?.docker_build_cpu_limit} cores</span>
            </Field>
            <Field label="Memory limit">
              <span className="text-sm">{settings?.docker_build_memory_limit}</span>
            </Field>
            <Field label="Max repair attempts">
              <input
                type="number"
                min={1}
                max={5}
                className="h-10 w-24 rounded-md border border-border bg-background px-3 text-sm"
                value={repairs}
                onChange={(event) => setRepairs(event.target.value)}
              />
            </Field>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3 last:border-0 last:pb-0">
      <span className="text-sm font-medium text-muted-foreground">{label}</span>
      <div className="flex items-center gap-2">{children}</div>
    </div>
  );
}
