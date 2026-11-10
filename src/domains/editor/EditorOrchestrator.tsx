import React from "react";
import { EditorMarkdownView } from "@/domains/editor/components/EditorMarkdownView";

export interface EditorOrchestratorProps {
  noteId?: string;
  initialContent?: string;
  className?: string;
}

export const EditorOrchestrator: React.FC<EditorOrchestratorProps> = (props) => {
  return <EditorMarkdownView {...props} />;
};

export default EditorOrchestrator;
