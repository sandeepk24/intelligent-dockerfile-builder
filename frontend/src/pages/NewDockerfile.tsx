import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/common/Card";
import { FolderOpen, Upload } from "lucide-react";

export function NewDockerfile() {
  return (
    <div>
      <Header
        title="New Dockerfile"
        description="Analyze a project and generate an optimized Dockerfile"
      />
      <div className="p-8">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="border-dashed">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <FolderOpen className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>Workspace Project</CardTitle>
                  <CardDescription>
                    Select a project from the configured workspace
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Available in Milestone 2. Configure the workspace root in Settings.
              </p>
            </CardContent>
          </Card>

          <Card className="border-dashed">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <Upload className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>Upload ZIP</CardTitle>
                  <CardDescription>
                    Upload a project archive for analysis
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Available in Milestone 2. Supports ZIP files up to 50MB.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
