import React, { useState } from "react";
import { MarkdownView as EditorMarkdownView } from "@/domains/editor/components/EditorMarkdownView";
import type { EditorMode } from "@/domains/editor/shared/utils/editor.types";

export interface EditorOrchestratorProps {
  noteId?: string;
  initialContent?: string;
  className?: string;
  value?: string;
  onChange?: (next: string) => void;
  mode?: EditorMode;
  placeholder?: string;
  showToolbar?: boolean;
  showProperties?: boolean;
  onWikilinkClick?: (target: string) => void;
  onTagClick?: (tag: string) => void;
  onSave?: () => void;
  sideBySide?: boolean;
}

export const EditorOrchestrator: React.FC<EditorOrchestratorProps> = ({
  value: propValue,
  onChange: propOnChange,
  initialContent = "",
  ...rest
}) => {
  // Adapter controlled vs uncontrolled:
  // Jika parent tidak memasok value/onChange, orchestrator mengelola state string lokal.
  const [internalValue, setInternalValue] = useState(initialContent);

  const value = propValue !== undefined ? propValue : internalValue;
  const onChange = propOnChange ?? setInternalValue;

  return <EditorMarkdownView {...rest} value={value} onChange={onChange} />;
};

export default EditorOrchestrator;
