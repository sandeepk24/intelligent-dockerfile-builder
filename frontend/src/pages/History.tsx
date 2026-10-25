import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/common/Card";
import { History as HistoryIcon } from "lucide-react";

export function History() {
  return (
    <div>
      <Header
        title="History"
        description="Previously generated Dockerfiles and their validation status"
      />
      <div className="p-8">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-20">
            <HistoryIcon className="mb-4 h-12 w-12 text-muted-foreground" />
            <p className="text-lg font-medium text-muted-foreground">
              No history yet
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Generated Dockerfiles will appear here.
              Full history with SQLite persistence comes in Milestone 4.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
