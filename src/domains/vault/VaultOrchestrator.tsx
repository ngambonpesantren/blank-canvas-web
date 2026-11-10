import React from "react";
import { VaultCard } from "@/domains/vault/components/VaultCard";
import { VaultModeSelector } from "@/domains/vault/components/VaultModeSelector";

export interface VaultOrchestratorProps {
  mode?: "card" | "selector";
  onSelectVault?: (vaultId: string) => void;
  className?: string;
}

export const VaultOrchestrator: React.FC<VaultOrchestratorProps> = ({ mode = "card", ...props }) => {
  if (mode === "selector") {
    return <VaultModeSelector {...(props as any)} />;
  }
  return <VaultCard {...(props as any)} />;
};

export default VaultOrchestrator;
