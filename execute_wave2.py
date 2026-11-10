#!/usr/bin/env python3
"""
execute_wave2.py

Eksekusi Wave 2 Arsitektur Quo Vadis:
1. Restrukturisasi 3 Domain Utama:
   - src/domains/workspace/ -> WorkspaceOrchestrator.tsx + flat components/ + shared/{api,stores,hooks,utils}
   - src/domains/editor/    -> EditorOrchestrator.tsx    + flat components/ + shared/{api,stores,hooks,utils}
   - src/domains/vault/     -> VaultOrchestrator.tsx     + flat components/ + shared/{api,stores,hooks,utils}
2. Pembaruan seluruh import alias di src/**/*.{ts,tsx} ke canonical path baru.
3. Pembuatan re-export bridge sementara untuk backward-compatibility.
4. Pembersihan folder lama setelah migrasi selesai.

Penggunaan:
  python execute_wave2.py --dry-run   # Simulasi pergerakan & remapping tanpa mengubah file
  python execute_wave2.py             # Eksekusi migrasi & pembaruan import alias
  python execute_wave2.py --clean     # Hapus shim bridge lama setelah verifikasi lulus
"""

import sys
import os
import shutil
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

# ==============================================================================
# 1. MANIFEST PEMETAAN WAVE 2 (LAMA -> CANONICAL BARU)
# ==============================================================================

# --- DOMAIN: WORKSPACE ---
WORKSPACE_FILE_MAP = [
    # Components (Semua flat ber-prefix Workspace*)
    ("components/IconRibbon.tsx", "components/WorkspaceIconRibbon.tsx"),
    ("components/ImportExportPanel.tsx", "components/WorkspaceImportExportPanel.tsx"),
    ("components/Ribbon.tsx", "components/WorkspaceRibbon.tsx"),
    ("components/SidebarPanel.tsx", "components/WorkspaceSidebarPanel.tsx"),
    ("components/StatusBar.tsx", "components/WorkspaceStatusBar.tsx"),
    ("components/TabContextMenu.tsx", "components/WorkspaceTabContextMenu.tsx"),
    ("components/VaultAccessDenied.tsx", "components/WorkspaceVaultAccessDenied.tsx"),
    ("components/WorkspaceGroup.tsx", "components/WorkspaceGroup.tsx"),
    ("components/WorkspacePane.tsx", "components/WorkspacePane.tsx"),
    ("components/WorkspaceTree.tsx", "components/WorkspaceTree.tsx"),
    ("sidebar/ExplorerContextMenu.tsx", "components/WorkspaceExplorerContextMenu.tsx"),
    ("sidebar/FileExplorerTree.tsx", "components/WorkspaceFileExplorerTree.tsx"),
    ("views/BacklinksLeaf.tsx", "components/WorkspaceBacklinksLeaf.tsx"),
    ("views/EmptyLeaf.tsx", "components/WorkspaceEmptyLeaf.tsx"),
    ("views/GraphLeaf.tsx", "components/WorkspaceGraphLeaf.tsx"),
    ("views/MarkdownLeaf.tsx", "components/WorkspaceMarkdownLeaf.tsx"),
    ("views/SettingsLeaf.tsx", "components/WorkspaceSettingsLeaf.tsx"),
    ("registry/ViewRegistry.tsx", "components/WorkspaceViewRegistry.tsx"),

    # Shared: API / I-O
    ("actions/workspaceActions.ts", "shared/api/workspaceActions.ts"),
    ("commands/CommandRegistry.ts", "shared/api/CommandRegistry.ts"),
    ("commands/graphCanvasCommands.ts", "shared/api/graphCanvasCommands.ts"),

    # Shared: Stores
    ("stores/useUIStore.ts", "shared/stores/useUIStore.ts"),
    ("stores/useWorkspaceStore.ts", "shared/stores/useWorkspaceStore.ts"),

    # Shared: Hooks
    ("hooks/useFolderNavigation.ts", "shared/hooks/useFolderNavigation.ts"),
    ("hooks/useVaultLifecycle.ts", "shared/hooks/useVaultLifecycle.ts"),

    # Shared: Utils & Types
    ("types.ts", "shared/utils/workspace.types.ts"),
]

# --- DOMAIN: EDITOR ---
EDITOR_FILE_MAP = [
    # Components (Semua flat ber-prefix Editor*)
    ("components/MarkdownView.tsx", "components/EditorMarkdownView.tsx"),
    ("components/FootnotePopover.tsx", "components/EditorFootnotePopover.tsx"),
    ("frontmatter/PropertiesPanel.tsx", "components/EditorPropertiesPanel.tsx"),
    ("frontmatter/SuggestInput.tsx", "components/EditorSuggestInput.tsx"),
    ("headings/FoldableMarkdown.tsx", "components/EditorFoldableMarkdown.tsx"),
    ("settings/EditorSettingsPanel.tsx", "components/EditorSettingsPanel.tsx"),
    ("table/InteractiveTable.tsx", "components/EditorInteractiveTable.tsx"),
    ("table/TableSliderNav.tsx", "components/EditorTableSliderNav.tsx"),

    # Shared: API
    ("services/activeEditor.ts", "shared/api/activeEditor.ts"),
    ("commands/editorCommands.ts", "shared/api/editorCommands.ts"),

    # Shared: Stores
    ("stores/useEditorSettingsStore.ts", "shared/stores/useEditorSettingsStore.ts"),

    # Shared: Utils & Types & CodeMirror
    ("types.ts", "shared/utils/editor.types.ts"),
    ("table/tableTypes.ts", "shared/utils/tableTypes.ts"),
    ("table/tableParser.ts", "shared/utils/tableParser.ts"),
    ("footnotes/footnoteParser.ts", "shared/utils/footnoteParser.ts"),
    ("frontmatter/frontmatter-utils.ts", "shared/utils/frontmatterUtils.ts"),
    ("headings/headingTree.ts", "shared/utils/headingTree.ts"),
    ("suggest/suggestions.ts", "shared/utils/suggestions.ts"),
    ("cm/setup.ts", "shared/utils/cmSetup.ts"),
    ("cm/theme.ts", "shared/utils/cmTheme.ts"),
    ("cm/state/editorApi.ts", "shared/utils/editorApi.ts"),
    ("cm/extensions/cmFootnoteWidget.ts", "shared/utils/cmFootnoteWidget.ts"),
    ("cm/extensions/cmTableWidget.ts", "shared/utils/cmTableWidget.ts"),
    ("cm/extensions/frontmatterField.ts", "shared/utils/frontmatterField.ts"),
    ("cm/extensions/headingFold.ts", "shared/utils/headingFold.ts"),
    ("cm/extensions/livePreview.ts", "shared/utils/livePreview.ts"),
    ("cm/extensions/wikilinkField.ts", "shared/utils/wikilinkField.ts"),
]

# --- DOMAIN: VAULT ---
VAULT_FILE_MAP = [
    # Components (Semua flat ber-prefix Vault*)
    ("components/ExportToFileSystem.tsx", "components/VaultExportToFileSystem.tsx"),
    ("components/VaultBackupPanel.tsx", "components/VaultBackupPanel.tsx"),
    ("components/VaultBackupSettings.tsx", "components/VaultBackupSettings.tsx"),
    ("components/VaultCard.tsx", "components/VaultCard.tsx"),
    ("components/VaultComparisonView.tsx", "components/VaultComparisonView.tsx"),
    ("components/VaultMemberSection.tsx", "components/VaultMemberSection.tsx"),
    ("components/VaultModeSelector.tsx", "components/VaultModeSelector.tsx"),
    ("components/VaultStorageControls.tsx", "components/VaultStorageControls.tsx"),
    ("debug/EventDebugPanel.tsx", "components/VaultEventDebugPanel.tsx"),

    # Shared: API (Services, Drivers, Repositories, Persistence)
    ("drivers/IVaultStorageDriver.ts", "shared/api/IVaultStorageDriver.ts"),
    ("drivers/IndexedDbVaultDriver.ts", "shared/api/IndexedDbVaultDriver.ts"),
    ("drivers/index.ts", "shared/api/vaultDrivers.ts"),
    ("import-export/services/ImportExportService.ts", "shared/api/ImportExportService.ts"),
    ("import-export/services/graph-export.ts", "shared/api/graphExport.ts"),
    ("import-export/services/graph-import.ts", "shared/api/graphImport.ts"),
    ("persistence/FileSystemService.ts", "shared/api/FileSystemService.ts"),
    ("persistence/FileSystemServiceSingleton.ts", "shared/api/FileSystemServiceSingleton.ts"),
    ("persistence/VaultFileWriter.ts", "shared/api/VaultFileWriter.ts"),
    ("persistence/directoryHandleStore.ts", "shared/api/directoryHandleStore.ts"),
    ("persistence/offline-storage.ts", "shared/api/offlineStorage.ts"),
    ("repository/adapters.ts", "shared/api/vaultAdapters.ts"),
    ("repository/capabilities.ts", "shared/api/vaultCapabilities.ts"),
    ("repository/index.ts", "shared/api/vaultRepository.ts"),
    ("services/AssetBundlerService.ts", "shared/api/AssetBundlerService.ts"),
    ("services/AutoHydrationService.ts", "shared/api/AutoHydrationService.ts"),
    ("services/CloudVaultService.ts", "shared/api/CloudVaultService.ts"),
    ("services/FileManager.ts", "shared/api/FileManager.ts"),
    ("services/NoteService.ts", "shared/api/NoteService.ts"),
    ("services/NoteSyncService.ts", "shared/api/NoteSyncService.ts"),
    ("services/VaultBackupService.ts", "shared/api/VaultBackupService.ts"),
    ("services/VaultHistory.ts", "shared/api/VaultHistory.ts"),
    ("services/VaultManager.ts", "shared/api/VaultManager.ts"),
    ("services/VaultManagerSingleton.ts", "shared/api/VaultManagerSingleton.ts"),
    ("services/VaultMemberService.ts", "shared/api/VaultMemberService.ts"),
    ("services/VaultStorage.ts", "shared/api/VaultStorage.ts"),
    ("services/VaultSyncService.ts", "shared/api/VaultSyncService.ts"),
    ("services/VaultValidationService.ts", "shared/api/VaultValidationService.ts"),

    # Shared: Stores
    ("stores/useBackupConfigStore.ts", "shared/stores/useBackupConfigStore.ts"),
    ("stores/useVaultStore.ts", "shared/stores/useVaultStore.ts"),

    # Shared: Hooks
    ("hooks/useVaultEvents.tsx", "shared/hooks/useVaultEvents.tsx"),
    ("hooks/useVaultSync.tsx", "shared/hooks/useVaultSync.tsx"),

    # Shared: Utils & Types
    ("types.ts", "shared/utils/vault.types.ts"),
    ("repository/types.ts", "shared/utils/vaultRepository.types.ts"),
]

# ==============================================================================
# 2. ATURAN PEMBARUAN ALIAS IMPORT (REGEX REMAPPING)
# ==============================================================================

ALIAS_REMAPPINGS = [
    # --- WORKSPACE ---
    (re.compile(r"@/domains/workspace/WorkspaceRoot\b"), "@/domains/workspace/WorkspaceOrchestrator"),
    (re.compile(r"@/domains/workspace/actions/workspaceActions\b"), "@/domains/workspace/shared/api/workspaceActions"),
    (re.compile(r"@/domains/workspace/commands/CommandRegistry\b"), "@/domains/workspace/shared/api/CommandRegistry"),
    (re.compile(r"@/domains/workspace/commands/graphCanvasCommands\b"), "@/domains/workspace/shared/api/graphCanvasCommands"),
    (re.compile(r"@/domains/workspace/stores/useUIStore\b"), "@/domains/workspace/shared/stores/useUIStore"),
    (re.compile(r"@/domains/workspace/stores/useWorkspaceStore\b"), "@/domains/workspace/shared/stores/useWorkspaceStore"),
    (re.compile(r"@/domains/workspace/hooks/useFolderNavigation\b"), "@/domains/workspace/shared/hooks/useFolderNavigation"),
    (re.compile(r"@/domains/workspace/hooks/useVaultLifecycle\b"), "@/domains/workspace/shared/hooks/useVaultLifecycle"),
    (re.compile(r"@/domains/workspace/types\b"), "@/domains/workspace/shared/utils/workspace.types"),
    (re.compile(r"@/domains/workspace/sidebar/ExplorerContextMenu\b"), "@/domains/workspace/components/WorkspaceExplorerContextMenu"),
    (re.compile(r"@/domains/workspace/sidebar/FileExplorerTree\b"), "@/domains/workspace/components/WorkspaceFileExplorerTree"),
    (re.compile(r"@/domains/workspace/registry/ViewRegistry\b"), "@/domains/workspace/components/WorkspaceViewRegistry"),
    (re.compile(r"@/domains/workspace/views/(\w+Leaf)\b"), r"@/domains/workspace/components/Workspace\1"),
    (re.compile(r"@/domains/workspace/components/(\w+)\b"), lambda m: f"@/domains/workspace/components/{m.group(1)}" if m.group(1).startswith("Workspace") else f"@/domains/workspace/components/Workspace{m.group(1)}"),

    # --- EDITOR ---
    (re.compile(r"@/domains/editor/services/activeEditor\b"), "@/domains/editor/shared/api/activeEditor"),
    (re.compile(r"@/domains/editor/commands/editorCommands\b"), "@/domains/editor/shared/api/editorCommands"),
    (re.compile(r"@/domains/editor/stores/useEditorSettingsStore\b"), "@/domains/editor/shared/stores/useEditorSettingsStore"),
    (re.compile(r"@/domains/editor/types\b"), "@/domains/editor/shared/utils/editor.types"),
    (re.compile(r"@/domains/editor/table/tableTypes\b"), "@/domains/editor/shared/utils/tableTypes"),
    (re.compile(r"@/domains/editor/table/tableParser\b"), "@/domains/editor/shared/utils/tableParser"),
    (re.compile(r"@/domains/editor/table/InteractiveTable\b"), "@/domains/editor/components/EditorInteractiveTable"),
    (re.compile(r"@/domains/editor/table/TableSliderNav\b"), "@/domains/editor/components/EditorTableSliderNav"),
    (re.compile(r"@/domains/editor/footnotes/footnoteParser\b"), "@/domains/editor/shared/utils/footnoteParser"),
    (re.compile(r"@/domains/editor/footnotes/FootnotePopover\b"), "@/domains/editor/components/EditorFootnotePopover"),
    (re.compile(r"@/domains/editor/frontmatter/frontmatter-utils\b"), "@/domains/editor/shared/utils/frontmatterUtils"),
    (re.compile(r"@/domains/editor/frontmatter/PropertiesPanel\b"), "@/domains/editor/components/EditorPropertiesPanel"),
    (re.compile(r"@/domains/editor/frontmatter/SuggestInput\b"), "@/domains/editor/components/EditorSuggestInput"),
    (re.compile(r"@/domains/editor/headings/headingTree\b"), "@/domains/editor/shared/utils/headingTree"),
    (re.compile(r"@/domains/editor/headings/FoldableMarkdown\b"), "@/domains/editor/components/EditorFoldableMarkdown"),
    (re.compile(r"@/domains/editor/settings/EditorSettingsPanel\b"), "@/domains/editor/components/EditorSettingsPanel"),
    (re.compile(r"@/domains/editor/suggest/suggestions\b"), "@/domains/editor/shared/utils/suggestions"),
    (re.compile(r"@/domains/editor/cm/setup\b"), "@/domains/editor/shared/utils/cmSetup"),
    (re.compile(r"@/domains/editor/cm/theme\b"), "@/domains/editor/shared/utils/cmTheme"),
    (re.compile(r"@/domains/editor/cm/state/editorApi\b"), "@/domains/editor/shared/utils/editorApi"),
    (re.compile(r"@/domains/editor/cm/extensions/(\w+)\b"), r"@/domains/editor/shared/utils/\1"),
    (re.compile(r"@/domains/editor/components/MarkdownView\b"), "@/domains/editor/components/EditorMarkdownView"),
    (re.compile(r"@/domains/editor/components/FootnotePopover\b"), "@/domains/editor/components/EditorFootnotePopover"),

    # --- VAULT ---
    (re.compile(r"@/domains/vault/drivers/IVaultStorageDriver\b"), "@/domains/vault/shared/api/IVaultStorageDriver"),
    (re.compile(r"@/domains/vault/drivers/IndexedDbVaultDriver\b"), "@/domains/vault/shared/api/IndexedDbVaultDriver"),
    (re.compile(r"@/domains/vault/drivers(?:/index)?\b"), "@/domains/vault/shared/api/vaultDrivers"),
    (re.compile(r"@/domains/vault/import-export/services/ImportExportService\b"), "@/domains/vault/shared/api/ImportExportService"),
    (re.compile(r"@/domains/vault/import-export/services/graph-export\b"), "@/domains/vault/shared/api/graphExport"),
    (re.compile(r"@/domains/vault/import-export/services/graph-import\b"), "@/domains/vault/shared/api/graphImport"),
    (re.compile(r"@/domains/vault/persistence/FileSystemService\b"), "@/domains/vault/shared/api/FileSystemService"),
    (re.compile(r"@/domains/vault/persistence/FileSystemServiceSingleton\b"), "@/domains/vault/shared/api/FileSystemServiceSingleton"),
    (re.compile(r"@/domains/vault/persistence/VaultFileWriter\b"), "@/domains/vault/shared/api/VaultFileWriter"),
    (re.compile(r"@/domains/vault/persistence/directoryHandleStore\b"), "@/domains/vault/shared/api/directoryHandleStore"),
    (re.compile(r"@/domains/vault/persistence/offline-storage(?:\.ts)?\b"), "@/domains/vault/shared/api/offlineStorage"),
    (re.compile(r"@/domains/vault/repository/adapters\b"), "@/domains/vault/shared/api/vaultAdapters"),
    (re.compile(r"@/domains/vault/repository/capabilities\b"), "@/domains/vault/shared/api/vaultCapabilities"),
    (re.compile(r"@/domains/vault/repository(?:/index)?\b"), "@/domains/vault/shared/api/vaultRepository"),
    (re.compile(r"@/domains/vault/repository/types\b"), "@/domains/vault/shared/utils/vaultRepository.types"),
    (re.compile(r"@/domains/vault/services/(\w+)\b"), r"@/domains/vault/shared/api/\1"),
    (re.compile(r"@/domains/vault/stores/useBackupConfigStore\b"), "@/domains/vault/shared/stores/useBackupConfigStore"),
    (re.compile(r"@/domains/vault/stores/useVaultStore\b"), "@/domains/vault/shared/stores/useVaultStore"),
    (re.compile(r"@/domains/vault/hooks/useVaultEvents\b"), "@/domains/vault/shared/hooks/useVaultEvents"),
    (re.compile(r"@/domains/vault/hooks/useVaultSync\b"), "@/domains/vault/shared/hooks/useVaultSync"),
    (re.compile(r"@/domains/vault/types\b"), "@/domains/vault/shared/utils/vault.types"),
    (re.compile(r"@/domains/vault/debug/EventDebugPanel\b"), "@/domains/vault/components/VaultEventDebugPanel"),
    (re.compile(r"@/domains/vault/components/ExportToFileSystem\b"), "@/domains/vault/components/VaultExportToFileSystem"),
    (re.compile(r"@/domains/vault/components/(\w+)\b"), lambda m: f"@/domains/vault/components/{m.group(1)}" if m.group(1).startswith("Vault") else f"@/domains/vault/components/Vault{m.group(1)}"),
]

# ==============================================================================
# 3. IMPLEMENTASI EKSEKUSI
# ==============================================================================

def ensure_domain_dirs(domain: str, dry_run: bool):
    d_path = SRC / "domains" / domain
    subdirs = [
        d_path / "components",
        d_path / "shared" / "api",
        d_path / "shared" / "stores",
        d_path / "shared" / "hooks",
        d_path / "shared" / "utils",
    ]
    for s in subdirs:
        if not dry_run:
            s.mkdir(parents=True, exist_ok=True)
    print(f"✓ [{domain}] Struktur direktori diverifikasi: components/ + shared/{{api,stores,hooks,utils}}")

def copy_and_shim(domain: str, src_rel: str, dst_rel: str, dry_run: bool):
    base = SRC / "domains" / domain
    src = base / src_rel
    dst = base / dst_rel

    if not src.exists():
        if dst.exists():
            return
        print(f"  [Peringatan] Sumber tidak ditemukan: {domain}/{src_rel}")
        return

    if dry_run:
        print(f"  [DRY-RUN] {domain}/{src_rel} -> {domain}/{dst_rel}")
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    # Buat re-export bridge pada file lama untuk keamanan transisi
    rel_depth = len(Path(src_rel).parent.parts)
    prefix = "../" * rel_depth if rel_depth > 0 else "./"
    shim_target = f"{prefix}{dst_rel}".replace(".tsx", "").replace(".ts", "")
    shim_content = f"// Re-export bridge Wave 2 (Quo Vadis)\nexport * from '{shim_target}';\n"
    src.write_text(shim_content, encoding="utf-8")

def create_orchestrators(dry_run: bool):
    """Membuat 3 Orchestrator resmi Wave 2"""
    print("\n=== Membuat Entry Point Orchestrator ===")

    # 1. WorkspaceOrchestrator.tsx
    ws_orch = SRC / "domains" / "workspace" / "WorkspaceOrchestrator.tsx"
    ws_root = SRC / "domains" / "workspace" / "WorkspaceRoot.tsx"
    if ws_root.exists() and not ws_orch.exists():
        if not dry_run:
            shutil.copy2(ws_root, ws_orch)
            # Re-export WorkspaceRoot untuk kompatibilitas
            ws_root.write_text("// Re-export bridge\nexport { WorkspaceRoot } from './WorkspaceOrchestrator';\n", encoding="utf-8")
        print("✓ WorkspaceOrchestrator.tsx dibuat (WorkspaceRoot didelegasikan)")

    # 2. EditorOrchestrator.tsx
    ed_orch = SRC / "domains" / "editor" / "EditorOrchestrator.tsx"
    if not ed_orch.exists():
        ed_content = '''import React from "react";
import { EditorMarkdownView } from "@/domains/editor/components/EditorMarkdownView";

export interface EditorOrchestratorProps {
  noteId?: string;
  initialContent?: string;
  className?: string;
}

/**
 * EditorOrchestrator
 * Entry point tunggal untuk domain editor (Markdown, CodeMirror, TOC, Frontmatter).
 */
export const EditorOrchestrator: React.FC<EditorOrchestratorProps> = (props) => {
  return <EditorMarkdownView {...props} />;
};

export default EditorOrchestrator;
'''
        if not dry_run:
            ed_orch.write_text(ed_content, encoding="utf-8")
        print("✓ EditorOrchestrator.tsx dibuat")

    # 3. VaultOrchestrator.tsx
    vault_orch = SRC / "domains" / "vault" / "VaultOrchestrator.tsx"
    if not vault_orch.exists():
        vault_content = '''import React from "react";
import { VaultModeSelector } from "@/domains/vault/components/VaultModeSelector";

export interface VaultOrchestratorProps {
  onSelect?: (vaultId: string) => void;
  className?: string;
}

/**
 * VaultOrchestrator
 * Entry point tunggal untuk manajemen vault, storage switcher, dan sinkronisasi.
 */
export const VaultOrchestrator: React.FC<VaultOrchestratorProps> = (props) => {
  return <VaultModeSelector {...props} />;
};

export default VaultOrchestrator;
'''
        if not dry_run:
            vault_orch.write_text(vault_content, encoding="utf-8")
        print("✓ VaultOrchestrator.tsx dibuat")

def update_all_import_aliases(dry_run: bool):
    """Memperbarui semua import alias @/domains/... di seluruh file src/"""
    print("\n=== Memperbarui Seluruh Import Alias di src/**/*.{ts,tsx} ===")
    ts_files = list(SRC.rglob("*.ts")) + list(SRC.rglob("*.tsx"))
    total_modified = 0

    for file_path in ts_files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            continue

        orig_content = content
        for pattern, replacement in ALIAS_REMAPPINGS:
            content = pattern.sub(replacement, content)

        if content != orig_content:
            total_modified += 1
            if not dry_run:
                file_path.write_text(content, encoding="utf-8")

    action = "Akan dimodifikasi" if dry_run else "Berhasil dimodifikasi"
    print(f"✓ {action}: {total_modified} file dengan alias canonical baru.")

def run_wave2(dry_run: bool):
    print("=" * 70)
    print("MEMULAI EKSEKUSI WAVE 2: WORKSPACE, EDITOR, & VAULT DOMAINS")
    print("=" * 70)

    # 1. Workspace
    ensure_domain_dirs("workspace", dry_run)
    for src_rel, dst_rel in WORKSPACE_FILE_MAP:
        copy_and_shim("workspace", src_rel, dst_rel, dry_run)

    # 2. Editor
    ensure_domain_dirs("editor", dry_run)
    for src_rel, dst_rel in EDITOR_FILE_MAP:
        copy_and_shim("editor", src_rel, dst_rel, dry_run)

    # 3. Vault
    ensure_domain_dirs("vault", dry_run)
    for src_rel, dst_rel in VAULT_FILE_MAP:
        copy_and_shim("vault", src_rel, dst_rel, dry_run)

    # 4. Orchestrators
    create_orchestrators(dry_run)

    # 5. Global Import Remap
    update_all_import_aliases(dry_run)

    print("\n" + "=" * 70)
    print("WAVE 2 RESTAGING SELESAI!")
    print("Silakan jalankan verifikasi: bunx tsgo --noEmit -p tsconfig.app.json")
    print("=" * 70)

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    run_wave2(dry_run=is_dry)
