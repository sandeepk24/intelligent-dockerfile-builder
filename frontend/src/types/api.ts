export interface HealthResponse {
  status: string;
  version: string;
  ollama_connected: boolean;
  ollama_url: string;
  docker_available: boolean;
  hadolint_available: boolean;
  trivy_available: boolean;
}

export interface SessionStats {
  dockerfiles_generated: number;
  validations_run: number;
  successful_builds: number;
  failed_validations: number;
  repairs_applied: number;
  avg_build_time_ms: number | null;
}

export interface OllamaModel {
  name: string;
  size: number;
  modified_at: string | null;
}

export interface ModelsResponse {
  models: OllamaModel[];
  default_model: string;
}

export interface WorkspaceProject {
  name: string;
  path: string;
  has_dockerfile: boolean;
}

export interface WorkspaceListResponse {
  workspace_root: string;
  projects: WorkspaceProject[];
}

export interface DockerfileIssue {
  code: string;
  severity: "high" | "medium" | "low" | string;
  title: string;
  detail: string;
  suggestion: string;
  line: number | null;
}

export interface ProjectAnalysis {
  project_id: string;
  name: string;
  source_type: string;
  language: string | null;
  framework: string | null;
  entry_point: string | null;
  runtime_version: string | null;
  dependencies: string[];
  ports: number[];
  build_command: string | null;
  start_command: string | null;
  has_dockerfile: boolean;
  existing_dockerfile: string | null;
  dockerfile_issues: DockerfileIssue[];
  file_tree: string[];
  created_at: string;
}

export interface JobResponse {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed" | string;
  job_type: string | null;
  dockerfile_id: string | null;
  validation_id: string | null;
  error: string | null;
}

export interface DockerfileDetail {
  id: string;
  project_id: string;
  project_name: string | null;
  language: string | null;
  framework: string | null;
  dockerfile: string;
  dockerignore: string;
  explanation: string;
  decisions: string[];
  model: string;
  instructions: string | null;
  status: string;
  original_dockerfile: string | null;
  issues: DockerfileIssue[];
  parent_id: string | null;
  repair_attempt: number;
  created_at: string;
  updated_at: string;
}

export interface DockerfileSummary {
  id: string;
  project_id: string;
  project_name: string | null;
  language: string | null;
  framework: string | null;
  model: string;
  status: string;
  parent_id: string | null;
  repair_attempt: number;
  created_at: string;
}

export interface DockerfileHistoryResponse {
  items: DockerfileSummary[];
}

export interface AppSettings {
  ollama_base_url: string;
  ollama_default_model: string;
  ollama_timeout: number;
  workspace_root: string;
  docker_build_timeout: number;
  docker_build_cpu_limit: number;
  docker_build_memory_limit: string;
  max_repair_attempts: number;
  max_upload_size_mb: number;
  max_file_count: number;
  docker_allow_builds: boolean;
  startup_check_seconds: number;
  trivy_enabled: boolean;
}

export interface ToolStepResult {
  status: string;
  reason?: string | null;
  findings?: Record<string, unknown>[];
  static_findings?: Record<string, unknown>[];
  log?: string | null;
  image_tag?: string | null;
  duration_ms?: number | null;
  image_size_bytes?: number | null;
  finding_count?: number | null;
  returncode?: number | null;
  stderr?: string | null;
}

export interface ValidationResult {
  id: string;
  dockerfile_id: string;
  status: string;
  approved_build: boolean;
  lint: ToolStepResult;
  build: ToolStepResult;
  image_size_bytes: number | null;
  build_duration_ms: number | null;
  trivy: ToolStepResult | null;
  startup: ToolStepResult | null;
  error_log: string | null;
  created_at: string;
}

export interface ValidationListResponse {
  items: ValidationResult[];
}

export interface RepairResult {
  id: string;
  validation_id: string;
  source_dockerfile_id: string;
  result_dockerfile_id: string | null;
  attempt: number;
  root_cause: string;
  explanation: string;
  decisions: string[];
  status: string;
  created_at: string;
}

export interface RepairListResponse {
  items: RepairResult[];
  attempts_used: number;
  max_attempts: number;
}

export interface SettingsUpdate {
  ollama_base_url?: string;
  ollama_default_model?: string;
  ollama_timeout?: number;
  max_repair_attempts?: number;
}
