import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Copy, Download, RefreshCw, Save, ScanSearch } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/common/Card";
import { Button } from "@/components/common/Button";
import { Badge } from "@/components/common/Badge";
import { Spinner } from "@/components/common/Spinner";
import { DockerfileEditor } from "@/components/dockerfile/DockerfileEditor";
import { copyText, downloadText } from "@/lib/download";
import { useToast } from "@/hooks/useToast";
import {
  useDockerfile,
  useGenerateDockerfile,
  useJob,
  useOptimizeDockerfile,
  useSaveDockerfile,
} from "@/api/queries";
import { IssueList } from "@/components/dockerfile/IssueList";

type Tab = "dockerfile" | "original" | "dockerignore" | "explanation" | "issues";

export function Workspace() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { push } = useToast();
  const { data, isLoading, error } = useDockerfile(id);
  const save = useSaveDockerfile();
  const generate = useGenerateDockerfile();
  const optimize = useOptimizeDockerfile();

  const [tab, setTab] = useState<Tab>("dockerfile");
  const [dockerfile, setDockerfile] = useState("");
  const [dockerignore, setDockerignore] = useState("");
  const [instructions, setInstructions] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const job = useJob(jobId);

  useEffect(() => {
    if (!data) {
      return;
    }
    setDockerfile(data.dockerfile);
    setDockerignore(data.dockerignore);
  }, [data]);

  useEffect(() => {
    if (job.data?.status === "completed" && job.data.dockerfile_id) {
      const nextId = job.data.dockerfile_id;
      setJobId(null);
      push(
        job.data.job_type === "optimize"
          ? "Dockerfile optimized"
          : "Regenerated Dockerfile",
        "success"
      );
      navigate(`/workspace/${nextId}`);
    }
    if (job.data?.status === "failed") {
      push(job.data.error || "Regeneration failed", "error");
      setJobId(null);
    }
  }, [job.data, navigate, push]);

  async function handleCopy() {
    await copyText(tab === "dockerignore" ? dockerignore : dockerfile);
    push("Copied to clipboard", "success");
  }

  function handleDownload() {
    if (!data) {
      return;
    }
    downloadText("Dockerfile", dockerfile);
    downloadText(".dockerignore", dockerignore);
    push("Downloaded Dockerfile and .dockerignore", "success");
  }

  async function handleSave() {
    if (!id) {
      return;
    }
    try {
      await save.mutateAsync({ id, dockerfile, dockerignore });
      push("Saved edits", "success");
    } catch (err) {
      push(err instanceof Error ? err.message : "Save failed", "error");
    }
  }

  async function handleRegenerate() {
    if (!data) {
      return;
    }
    try {
      const jobResponse = await generate.mutateAsync({
        project_id: data.project_id,
        model: data.model,
        instructions: instructions.trim() || undefined,
      });
      setJobId(jobResponse.job_id);
    } catch (err) {
      push(err instanceof Error ? err.message : "Regeneration failed", "error");
    }
  }

  async function handleOptimize() {
    if (!data) {
      return;
    }
    try {
      const jobResponse = await optimize.mutateAsync({
        project_id: data.project_id,
        dockerfile: dockerfile,
        model: data.model,
        instructions: instructions.trim() || undefined,
      });
      setJobId(jobResponse.job_id);
    } catch (err) {
      push(err instanceof Error ? err.message : "Optimize failed", "error");
    }
  }

  const generating =
    generate.isPending ||
    optimize.isPending ||
    job.data?.status === "pending" ||
    job.data?.status === "running";

  if (!id) {
    return (
      <EmptyState message="Generate a Dockerfile first, or open one from History." />
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner size={28} />
      </div>
    );
  }

  if (error || !data) {
    return (
      <EmptyState message="Dockerfile not found. It may have been generated in another session." />
    );
  }

  return (
    <div>
      <Header
        title="Dockerfile Workspace"
        description={`${data.project_name ?? data.project_id} · ${data.language ?? "unknown"}`}
      >
        <Button variant="outline" onClick={handleCopy}>
          <Copy className="h-4 w-4" />
          Copy
        </Button>
        <Button variant="outline" onClick={handleDownload}>
          <Download className="h-4 w-4" />
          Download
        </Button>
        <Button variant="secondary" onClick={handleSave} disabled={save.isPending}>
          {save.isPending ? <Spinner size={16} /> : <Save className="h-4 w-4" />}
          Save
        </Button>
      </Header>

      <div className="grid grid-cols-1 gap-6 p-8 xl:grid-cols-[minmax(0,1.6fr)_minmax(20rem,1fr)]">
        <div className="space-y-4">
          <div className="flex gap-2">
            <TabButton
              active={tab === "dockerfile"}
              onClick={() => setTab("dockerfile")}
            >
              Dockerfile
            </TabButton>
            {data.original_dockerfile && (
              <TabButton
                active={tab === "original"}
                onClick={() => setTab("original")}
              >
                Original
              </TabButton>
            )}
            <TabButton
              active={tab === "dockerignore"}
              onClick={() => setTab("dockerignore")}
            >
              .dockerignore
            </TabButton>
            <TabButton
              active={tab === "explanation"}
              onClick={() => setTab("explanation")}
            >
              Explanation
            </TabButton>
            <TabButton
              active={tab === "issues"}
              onClick={() => setTab("issues")}
            >
              Issues{data.issues.length ? ` (${data.issues.length})` : ""}
            </TabButton>
            <Badge variant="outline">{data.status}</Badge>
          </div>

          {tab === "explanation" ? (
            <Card>
              <CardHeader>
                <CardTitle>Why this Dockerfile</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm leading-6">{data.explanation || "No explanation returned."}</p>
                <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {data.decisions.map((decision) => (
                    <li key={decision}>{decision}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ) : tab === "issues" ? (
            <Card>
              <CardHeader>
                <CardTitle>Findings and suggestions</CardTitle>
              </CardHeader>
              <CardContent>
                <IssueList issues={data.issues} />
              </CardContent>
            </Card>
          ) : tab === "original" && data.original_dockerfile ? (
            <DockerfileEditor
              language="dockerfile"
              value={data.original_dockerfile}
              readOnly
            />
          ) : (
            <DockerfileEditor
              language={tab === "dockerfile" ? "dockerfile" : "plaintext"}
              value={tab === "dockerfile" ? dockerfile : dockerignore}
              onChange={tab === "dockerfile" ? setDockerfile : setDockerignore}
            />
          )}
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Project</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <Row label="Language" value={data.language} />
              <Row label="Framework" value={data.framework} />
              <Row label="Model" value={data.model} />
              <Row label="Status" value={data.status} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Regenerate</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <textarea
                className="min-h-24 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                placeholder="Additional instructions for the next generation"
                value={instructions}
                onChange={(event) => setInstructions(event.target.value)}
              />
              <Button onClick={handleRegenerate} disabled={generating}>
                {generating ? <Spinner size={16} /> : <RefreshCw className="h-4 w-4" />}
                {generating ? "Working..." : "Regenerate from source"}
              </Button>
              <Button
                variant="secondary"
                onClick={handleOptimize}
                disabled={generating}
              >
                {generating ? <Spinner size={16} /> : <ScanSearch className="h-4 w-4" />}
                Review and optimize this file
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div>
      <Header
        title="Dockerfile Workspace"
        description="View, edit, and download generated Dockerfiles"
      />
      <div className="p-8">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-20 text-center">
            <p className="text-sm text-muted-foreground">{message}</p>
            <Link to="/new" className="mt-4">
              <Button>New Dockerfile</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md px-3 py-1.5 text-sm ${
        active ? "bg-accent text-foreground" : "text-muted-foreground hover:bg-accent/50"
      }`}
    >
      {children}
    </button>
  );
}

function Row({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value || "—"}</span>
    </div>
  );
}
