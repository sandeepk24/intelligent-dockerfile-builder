import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FolderOpen, Upload, Sparkles } from "lucide-react";
import { Header } from "@/components/layout/Header";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/common/Card";
import { Button } from "@/components/common/Button";
import { Badge } from "@/components/common/Badge";
import { Spinner } from "@/components/common/Spinner";
import { useToast } from "@/hooks/useToast";
import {
  useAnalyzeDirectory,
  useAnalyzeZip,
  useGenerateDockerfile,
  useHealth,
  useJob,
  useModels,
  useWorkspaceProjects,
} from "@/api/queries";
import type { ProjectAnalysis } from "@/types/api";

export function NewDockerfile() {
  const navigate = useNavigate();
  const { push } = useToast();
  const { data: health } = useHealth();
  const { data: modelsData, isLoading: modelsLoading } = useModels();
  const { data: workspace, isLoading: workspaceLoading } =
    useWorkspaceProjects();
  const analyzeDirectory = useAnalyzeDirectory();
  const analyzeZip = useAnalyzeZip();
  const generate = useGenerateDockerfile();

  const [selectedPath, setSelectedPath] = useState("");
  const [model, setModel] = useState("");
  const [instructions, setInstructions] = useState("");
  const [analysis, setAnalysis] = useState<ProjectAnalysis | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const job = useJob(jobId);

  useEffect(() => {
    if (modelsData?.default_model && !model) {
      setModel(modelsData.default_model);
    }
  }, [modelsData, model]);

  useEffect(() => {
    if (job.data?.status === "completed" && job.data.dockerfile_id) {
      const dockerfileId = job.data.dockerfile_id;
      setJobId(null);
      push("Dockerfile generated", "success");
      navigate(`/workspace/${dockerfileId}`);
    }
    if (job.data?.status === "failed") {
      push(job.data.error || "Generation failed", "error");
      setJobId(null);
    }
  }, [job.data, navigate, push]);

  async function handleAnalyzeDirectory() {
    if (!selectedPath) {
      push("Select a workspace project first", "error");
      return;
    }
    try {
      const result = await analyzeDirectory.mutateAsync(selectedPath);
      setAnalysis(result);
      push(`Analyzed ${result.name}`, "success");
    } catch (error) {
      push(error instanceof Error ? error.message : "Analysis failed", "error");
    }
  }

  async function handleUpload(file: File | undefined) {
    if (!file) {
      return;
    }
    try {
      const result = await analyzeZip.mutateAsync(file);
      setAnalysis(result);
      push(`Analyzed ${result.name}`, "success");
    } catch (error) {
      push(error instanceof Error ? error.message : "Upload failed", "error");
    }
  }

  async function handleGenerate() {
    if (!analysis) {
      push("Analyze a project before generating", "error");
      return;
    }
    if (!health?.ollama_connected) {
      push("Ollama is offline. Start it before generating.", "error");
      return;
    }
    try {
      const jobResponse = await generate.mutateAsync({
        project_id: analysis.project_id,
        model: model || undefined,
        instructions: instructions.trim() || undefined,
      });
      setJobId(jobResponse.job_id);
    } catch (error) {
      push(error instanceof Error ? error.message : "Generation failed", "error");
    }
  }

  const analyzing = analyzeDirectory.isPending || analyzeZip.isPending;
  const generating =
    generate.isPending ||
    job.data?.status === "pending" ||
    job.data?.status === "running";

  return (
    <div>
      <Header
        title="New Dockerfile"
        description="Analyze a project and generate an optimized Dockerfile"
      />
      <div className="space-y-6 p-8">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <FolderOpen className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>Workspace Project</CardTitle>
                  <CardDescription>
                    Select a project from {workspace?.workspace_root ?? "WORKSPACE_ROOT"}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {workspaceLoading ? (
                <Spinner />
              ) : (
                <select
                  className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm"
                  value={selectedPath}
                  onChange={(event) => setSelectedPath(event.target.value)}
                >
                  <option value="">Choose a project</option>
                  {workspace?.projects.map((project) => (
                    <option key={project.path} value={project.path}>
                      {project.name}
                      {project.has_dockerfile ? " (has Dockerfile)" : ""}
                    </option>
                  ))}
                </select>
              )}
              <Button
                onClick={handleAnalyzeDirectory}
                disabled={analyzing || !selectedPath}
              >
                {analyzeDirectory.isPending ? <Spinner size={16} /> : null}
                Analyze project
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <Upload className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>Upload ZIP</CardTitle>
                  <CardDescription>
                    Archives are scanned for traversal, symlinks, and zip bombs
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <label className="flex cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-border px-4 py-8 text-sm text-muted-foreground hover:bg-accent/40">
                {analyzeZip.isPending ? (
                  <Spinner />
                ) : (
                  <>
                    <Upload className="mb-2 h-5 w-5" />
                    Drop a .zip here or click to browse
                  </>
                )}
                <input
                  type="file"
                  accept=".zip"
                  className="hidden"
                  onChange={(event) =>
                    handleUpload(event.target.files?.[0]).catch(() => undefined)
                  }
                />
              </label>
            </CardContent>
          </Card>
        </div>

        {analysis && (
          <Card>
            <CardHeader>
              <CardTitle>Detected project</CardTitle>
              <CardDescription>
                {analysis.name} · {analysis.source_type}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <Meta label="Language" value={analysis.language} />
                <Meta label="Framework" value={analysis.framework} />
                <Meta label="Entry point" value={analysis.entry_point} />
                <Meta label="Runtime" value={analysis.runtime_version} />
              </div>
              <div className="flex flex-wrap gap-2">
                {analysis.dependencies.slice(0, 12).map((dep) => (
                  <Badge key={dep} variant="outline">
                    {dep}
                  </Badge>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                {analysis.file_tree.length} files scanned · ports{" "}
                {analysis.ports.join(", ") || "none detected"}
              </p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Generation</CardTitle>
            <CardDescription>
              Choose a local Ollama model and optional extra instructions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <label className="space-y-2 text-sm">
                <span className="text-muted-foreground">Model</span>
                <select
                  className="h-10 w-full rounded-md border border-border bg-background px-3"
                  value={model}
                  onChange={(event) => setModel(event.target.value)}
                  disabled={modelsLoading}
                >
                  {!modelsData?.models.length && (
                    <option value={model || "codellama:7b"}>
                      {model || "codellama:7b"}
                    </option>
                  )}
                  {modelsData?.models.map((item) => (
                    <option key={item.name} value={item.name}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-2 text-sm">
                <span className="text-muted-foreground">
                  Additional instructions
                </span>
                <input
                  className="h-10 w-full rounded-md border border-border bg-background px-3"
                  placeholder="e.g. Prefer distroless, expose 8080"
                  value={instructions}
                  onChange={(event) => setInstructions(event.target.value)}
                />
              </label>
            </div>
            {!health?.ollama_connected && (
              <p className="rounded-md border border-warning/30 bg-warning/5 px-3 py-2 text-sm text-warning">
                Ollama is disconnected. Generation will not start until the
                local LLM is running.
              </p>
            )}
            <Button onClick={handleGenerate} disabled={!analysis || generating}>
              {generating ? <Spinner size={16} /> : <Sparkles className="h-4 w-4" />}
              {generating ? "Generating Dockerfile..." : "Generate Dockerfile"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="rounded-md border border-border px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium">{value || "—"}</p>
    </div>
  );
}
