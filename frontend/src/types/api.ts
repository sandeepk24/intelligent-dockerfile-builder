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
