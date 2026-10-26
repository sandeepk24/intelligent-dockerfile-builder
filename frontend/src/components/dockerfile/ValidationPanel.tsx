import { Link } from "react-router-dom";
import { ShieldAlert, Wrench } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/common/Card";
import { Button } from "@/components/common/Button";
import { Badge } from "@/components/common/Badge";
import { Spinner } from "@/components/common/Spinner";
import { formatBytes, formatDuration } from "@/lib/utils";
import type { RepairListResponse, ValidationResult } from "@/types/api";

export function ValidationPanel({
  latest,
  history,
  repairs,
  approveBuild,
  confirmUntrusted,
  runTrivy,
  runStartup,
  busy,
  onApproveBuild,
  onConfirmUntrusted,
  onRunTrivy,
  onRunStartup,
  onValidate,
  onRepair,
}: {
  latest: ValidationResult | undefined;
  history: ValidationResult[];
  repairs: RepairListResponse | undefined;
  approveBuild: boolean;
  confirmUntrusted: boolean;
  runTrivy: boolean;
  runStartup: boolean;
  busy: boolean;
  onApproveBuild: (value: boolean) => void;
  onConfirmUntrusted: (value: boolean) => void;
  onRunTrivy: (value: boolean) => void;
  onRunStartup: (value: boolean) => void;
  onValidate: () => void;
  onRepair: () => void;
}) {
  const remaining = Math.max(
    0,
    (repairs?.max_attempts ?? 3) - (repairs?.attempts_used ?? 0)
  );
  const canRepair = latest?.status === "failed" && remaining > 0 && !busy;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Validate and repair</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-xs leading-5 text-muted-foreground">
          Lint always runs. Docker builds copy the scanned project into a sandbox
          and require explicit approval — the image is untrusted code.
        </p>

        <label className="flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            className="mt-1"
            checked={approveBuild}
            onChange={(event) => onApproveBuild(event.target.checked)}
          />
          <span>Approve isolated Docker build</span>
        </label>
        {approveBuild && (
          <>
            <label className="flex items-start gap-2 text-sm">
              <input
                type="checkbox"
                className="mt-1"
                checked={confirmUntrusted}
                onChange={(event) => onConfirmUntrusted(event.target.checked)}
              />
              <span>I understand this runs untrusted project code in Docker</span>
            </label>
            <label className="flex items-start gap-2 text-sm">
              <input
                type="checkbox"
                className="mt-1"
                checked={runStartup}
                onChange={(event) => onRunStartup(event.target.checked)}
              />
              <span>Startup check (no published ports, no network)</span>
            </label>
            <label className="flex items-start gap-2 text-sm">
              <input
                type="checkbox"
                className="mt-1"
                checked={runTrivy}
                onChange={(event) => onRunTrivy(event.target.checked)}
              />
              <span>Optional Trivy HIGH/CRITICAL scan</span>
            </label>
          </>
        )}

        <Button onClick={onValidate} disabled={busy} className="w-full">
          {busy ? <Spinner size={16} /> : <ShieldAlert className="h-4 w-4" />}
          {busy ? "Validating..." : approveBuild ? "Lint and build" : "Lint only"}
        </Button>

        {latest ? (
          <div className="space-y-3 rounded-md border border-border p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium">Latest result</span>
              <StatusBadge status={latest.status} />
            </div>
            <ResultRow label="Hadolint" value={latest.lint.status} />
            <ResultRow label="Build" value={latest.build.status} />
            <ResultRow label="Image size" value={formatBytes(latest.image_size_bytes)} />
            <ResultRow label="Build time" value={formatDuration(latest.build_duration_ms)} />
            {latest.trivy && <ResultRow label="Trivy" value={latest.trivy.status} />}
            {latest.startup && <ResultRow label="Startup" value={latest.startup.status} />}
            {latest.build.reason && (
              <p className="text-xs text-muted-foreground">{latest.build.reason}</p>
            )}
            <FindingList
              title="Lint findings"
              items={(latest.lint.findings ?? []).map((item) =>
                formatFinding(item)
              )}
            />
            {latest.error_log && (
              <pre className="max-h-40 overflow-auto rounded bg-muted/60 p-2 text-[11px] leading-4">
                {latest.error_log}
              </pre>
            )}
            {canRepair && (
              <Button variant="secondary" onClick={onRepair} className="w-full">
                <Wrench className="h-4 w-4" />
                Repair with AI ({remaining} left)
              </Button>
            )}
            {latest.status === "failed" && remaining === 0 && (
              <p className="text-xs text-warning">Maximum repair attempts used.</p>
            )}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">No validation runs yet.</p>
        )}

        {repairs && repairs.items.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Repair history</p>
            {repairs.items.map((item) => (
              <div key={item.id} className="rounded-md border border-border px-3 py-2 text-xs">
                <div className="flex items-center justify-between">
                  <span>Attempt {item.attempt}</span>
                  <Badge variant="outline">{item.status}</Badge>
                </div>
                <p className="mt-1 text-muted-foreground">{item.root_cause}</p>
                {item.result_dockerfile_id && (
                  <Link
                    to={`/workspace/${item.result_dockerfile_id}`}
                    className="mt-1 inline-block text-primary hover:underline"
                  >
                    Open repaired Dockerfile
                  </Link>
                )}
              </div>
            ))}
          </div>
        )}

        {history.length > 1 && (
          <p className="text-xs text-muted-foreground">
            {history.length} validation runs this session.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === "passed"
      ? "success"
      : status === "failed"
        ? "destructive"
        : "warning";
  return <Badge variant={variant}>{status}</Badge>;
}

function ResultRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function FindingList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) {
    return null;
  }
  return (
    <div>
      <p className="text-xs font-medium">{title}</p>
      <ul className="mt-1 list-disc space-y-1 pl-4 text-xs text-muted-foreground">
        {items.slice(0, 8).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function formatFinding(item: Record<string, unknown>): string {
  const code = String(item.code ?? item.id ?? "finding");
  const message = String(item.message ?? item.title ?? item.detail ?? "");
  const line = item.line != null ? ` L${item.line}` : "";
  return `${code}${line}: ${message}`.trim();
}
