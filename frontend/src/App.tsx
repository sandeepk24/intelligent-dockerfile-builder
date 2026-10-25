import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import { Dashboard } from "@/pages/Dashboard";
import { NewDockerfile } from "@/pages/NewDockerfile";
import { Workspace } from "@/pages/Workspace";
import { History } from "@/pages/History";
import { Settings } from "@/pages/Settings";
import { ToastProvider } from "@/hooks/useToast";
import { ToastViewport } from "@/components/common/Toast";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/new" element={<NewDockerfile />} />
              <Route path="/workspace" element={<Workspace />} />
              <Route path="/workspace/:id" element={<Workspace />} />
              <Route path="/history" element={<History />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <ToastViewport />
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;
