export interface HealthResponse {
  status: string;
  version: string;
  ollama_connected: boolean;
  ollama_url: string;
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
  file_tree: string[];
  created_at: string;
}

export interface JobResponse {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed" | string;
  job_type: string | null;
  dockerfile_id: string | null;
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
}

export interface SettingsUpdate {
  ollama_base_url?: string;
  ollama_default_model?: string;
  ollama_timeout?: number;
  max_repair_attempts?: number;
}
