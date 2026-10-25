import { Badge } from "@/components/common/Badge";
import type { DockerfileIssue } from "@/types/api";

export function IssueList({ issues }: { issues: DockerfileIssue[] }) {
  if (issues.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No static issues found. You can still ask the model to tighten the file.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {issues.map((issue) => (
        <div
          key={`${issue.code}-${issue.line ?? "x"}`}
          className="rounded-md border border-border px-3 py-3"
        >
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={severityVariant(issue.severity)}>{issue.severity}</Badge>
            {issue.line ? (
              <span className="text-xs text-muted-foreground">line {issue.line}</span>
            ) : null}
            <p className="text-sm font-medium">{issue.title}</p>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">{issue.detail}</p>
          <p className="mt-1 text-sm">Suggestion: {issue.suggestion}</p>
        </div>
      ))}
    </div>
  );
}

function severityVariant(severity: string) {
  if (severity === "high") {
    return "destructive" as const;
  }
  if (severity === "medium") {
    return "warning" as const;
  }
  return "outline" as const;
}
