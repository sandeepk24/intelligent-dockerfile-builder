import Editor from "@monaco-editor/react";

interface DockerfileEditorProps {
  value: string;
  language: "dockerfile" | "plaintext";
  onChange?: (value: string) => void;
  readOnly?: boolean;
}

export function DockerfileEditor({
  value,
  language,
  onChange,
  readOnly = false,
}: DockerfileEditorProps) {
  return (
    <div className="overflow-hidden rounded-md border border-border">
      <Editor
        height="520px"
        language={language}
        theme="vs-dark"
        value={value}
        onChange={(next) => onChange?.(next ?? "")}
        options={{
          minimap: { enabled: false },
          fontSize: 13,
          automaticLayout: true,
          scrollBeyondLastLine: false,
          wordWrap: "on",
          readOnly,
        }}
      />
    </div>
  );
}
