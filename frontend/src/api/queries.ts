import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type { HealthResponse, ModelsResponse } from "@/types/api";

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
