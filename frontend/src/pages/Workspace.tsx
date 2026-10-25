import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/common/Card";
import { Code2 } from "lucide-react";

export function Workspace() {
  return (
    <div>
      <Header
        title="Dockerfile Workspace"
        description="View, edit, and validate generated Dockerfiles"
      />
      <div className="p-8">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-20">
            <Code2 className="mb-4 h-12 w-12 text-muted-foreground" />
            <p className="text-lg font-medium text-muted-foreground">
              No Dockerfile selected
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Generate a Dockerfile first, or select one from History.
              Monaco Editor will be available in Milestone 2.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
