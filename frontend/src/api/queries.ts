import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type {
  AppSettings,
  DockerfileDetail,
  DockerfileHistoryResponse,
  HealthResponse,
  JobResponse,
  ModelsResponse,
  ProjectAnalysis,
  RepairListResponse,
  SessionStats,
  SettingsUpdate,
  ValidationListResponse,
  WorkspaceListResponse,
} from "@/types/api";

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: () => api.get<HealthResponse>("/health"),
    refetchInterval: 15000,
    retry: 1,
  });
}

export function useModels() {
  return useQuery<ModelsResponse>({
    queryKey: ["models"],
    queryFn: () => api.get<ModelsResponse>("/models"),
    retry: 1,
  });
}

export function useWorkspaceProjects() {
  return useQuery<WorkspaceListResponse>({
    queryKey: ["workspace-projects"],
    queryFn: () => api.get<WorkspaceListResponse>("/workspace/projects"),
  });
}

export function useAnalyzeDirectory() {
  return useMutation({
    mutationFn: (path: string) =>
      api.post<ProjectAnalysis>("/projects/analyze", {
        source_type: "directory",
        path,
      }),
  });
}

export function useAnalyzeZip() {
  return useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return api.postForm<ProjectAnalysis>("/projects/analyze", form);
    },
  });
}

export function useGenerateDockerfile() {
  return useMutation({
    mutationFn: (payload: {
      project_id: string;
      model?: string;
      instructions?: string;
    }) => api.post<JobResponse>("/dockerfiles/generate", payload),
  });
}

export function useAnalyzeDockerfile() {
  return useMutation({
    mutationFn: (payload: { dockerfile: string; name?: string }) =>
      api.post<ProjectAnalysis>("/projects/analyze", {
        source_type: "dockerfile",
        dockerfile: payload.dockerfile,
        name: payload.name,
      }),
  });
}

export function useOptimizeDockerfile() {
  return useMutation({
    mutationFn: (payload: {
      project_id: string;
      dockerfile?: string;
      model?: string;
      instructions?: string;
    }) => api.post<JobResponse>("/dockerfiles/optimize", payload),
  });
}

export function useJob(jobId: string | null) {
  return useQuery<JobResponse>({
    queryKey: ["job", jobId],
    queryFn: () => api.get<JobResponse>(`/jobs/${jobId}`),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "running" ? 700 : false;
    },
  });
}

export function useDockerfile(id: string | undefined) {
  return useQuery<DockerfileDetail>({
    queryKey: ["dockerfile", id],
    queryFn: () => api.get<DockerfileDetail>(`/dockerfiles/${id}`),
    enabled: Boolean(id),
  });
}

export function useSaveDockerfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      id: string;
      dockerfile?: string;
      dockerignore?: string;
    }) =>
      api.put<DockerfileDetail>(`/dockerfiles/${payload.id}`, {
        dockerfile: payload.dockerfile,
        dockerignore: payload.dockerignore,
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["dockerfile", data.id], data);
      queryClient.invalidateQueries({ queryKey: ["dockerfile-history"] });
    },
  });
}

export function useValidations(dockerfileId: string | undefined) {
  return useQuery<ValidationListResponse>({
    queryKey: ["validations", dockerfileId],
    queryFn: () =>
      api.get<ValidationListResponse>(`/dockerfiles/${dockerfileId}/validations`),
    enabled: Boolean(dockerfileId),
  });
}

export function useRepairs(dockerfileId: string | undefined) {
  return useQuery<RepairListResponse>({
    queryKey: ["repairs", dockerfileId],
    queryFn: () =>
      api.get<RepairListResponse>(`/dockerfiles/${dockerfileId}/repairs`),
    enabled: Boolean(dockerfileId),
  });
}

export function useValidateDockerfile() {
  return useMutation({
    mutationFn: (payload: {
      id: string;
      approve_build: boolean;
      confirm_untrusted_execution: boolean;
      run_trivy: boolean;
      run_startup_check: boolean;
    }) =>
      api.post<JobResponse>(`/dockerfiles/${payload.id}/validate`, {
        approve_build: payload.approve_build,
        confirm_untrusted_execution: payload.confirm_untrusted_execution,
        run_trivy: payload.run_trivy,
        run_startup_check: payload.run_startup_check,
      }),
  });
}

export function useRepairDockerfile() {
  return useMutation({
    mutationFn: (payload: {
      id: string;
      validation_id: string;
      model?: string;
      instructions?: string;
    }) =>
      api.post<JobResponse>(`/dockerfiles/${payload.id}/repair`, {
        validation_id: payload.validation_id,
        model: payload.model,
        instructions: payload.instructions,
      }),
  });
}

export function useSessionStats() {
  return useQuery<SessionStats>({
    queryKey: ["session-stats"],
    queryFn: () => api.get<SessionStats>("/stats"),
  });
}

export function useDockerfileHistory() {
  return useQuery<DockerfileHistoryResponse>({
    queryKey: ["dockerfile-history"],
    queryFn: () => api.get<DockerfileHistoryResponse>("/dockerfiles/history"),
  });
}

export function useSettings() {
  return useQuery<AppSettings>({
    queryKey: ["settings"],
    queryFn: () => api.get<AppSettings>("/settings"),
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SettingsUpdate) =>
      api.put<AppSettings>("/settings", payload),
    onSuccess: (data) => {
      queryClient.setQueryData(["settings"], data);
      queryClient.invalidateQueries({ queryKey: ["health"] });
      queryClient.invalidateQueries({ queryKey: ["models"] });
    },
  });
}
