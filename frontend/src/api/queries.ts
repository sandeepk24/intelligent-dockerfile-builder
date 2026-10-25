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
  SettingsUpdate,
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
