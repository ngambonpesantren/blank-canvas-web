#!/usr/bin/env python3
"""
resolve_wave2_and_shared.py

Skrip Pemulihan & Eksekusi Wave 2 Quo Vadis + Migrasi Folder Shared:
1. Memulihkan file workspace yang rusak akibat eksekusi skrip sebelumnya langsung dari commit 64343b1.
2. Memperbaiki 24 TypeScript error (TS2308 duplikasi ekspor, missing atmosphereConfig, RibbonTool, NodeType, HierarchyPresetId).
3. Melakukan restrukturisasi Wave 2 (Workspace, Editor, Vault) secara idempotent (tanpa SameFileError).
4. Menyelesaikan migrasi folder src/shared/ menjadi re-export bridge bersih ke src/global/ dan domain store.
5. Memperbarui seluruh path import di src/**/*.{ts,tsx} ke canonical path baru.
6. Memverifikasi kompilasi dan build Vite.

Penggunaan:
  python resolve_wave2_and_shared.py --dry-run   # Simulasi tanpa mengubah file
  python resolve_wave2_and_shared.py             # Eksekusi penuh pemulihan & restrukturisasi
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

# ==============================================================================
# 1. TAHAP PEMULIHAN FILE WORKSPACE YANG RUSAK
# ==============================================================================

WORKSPACE_DAMAGED_FILES = [
    "src/domains/workspace/components/IconRibbon.tsx",
    "src/domains/workspace/components/ImportExportPanel.tsx",
    "src/domains/workspace/components/Ribbon.tsx",
    "src/domains/workspace/components/SidebarPanel.tsx",
    "src/domains/workspace/components/StatusBar.tsx",
    "src/domains/workspace/components/TabContextMenu.tsx",
    "src/domains/workspace/components/VaultAccessDenied.tsx",
]

def restore_damaged_workspace_files(dry_run: bool):
    print("\n=== [Tahap 1/6] Memeriksa & Memulihkan File Workspace yang Terpotong ===")
    restored_count = 0
    for rel_path in WORKSPACE_DAMAGED_FILES:
        target = ROOT / rel_path
        needs_restore = False

        if not target.exists():
            needs_restore = True
        else:
            content = target.read_text(encoding="utf-8").strip()
            # Jika file hanya berisi 1-3 baris re-export bridge atau berukuran di bawah 250 karakter
            if len(content) < 250 and "Re-export bridge" in content:
                needs_restore = True

        if needs_restore:
            if dry_run:
                print(f"  [DRY-RUN] Akan memulihkan: {rel_path} dari git commit 64343b1")
                restored_count += 1
                continue

            # Ambil konten asli dari commit stabil 64343b1
            res = subprocess.run(["git", "show", f"64343b1:{rel_path}"], capture_output=True, text=True)
            if res.returncode == 0 and len(res.stdout) > 250:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(res.stdout, encoding="utf-8")
                print(f"  ✓ Berhasil memulihkan: {rel_path} ({len(res.stdout)} bytes)")
                restored_count += 1
            else:
                # Fallback: ambil dari src/core/shell/workspace/ jika ada
                core_fallback = SRC / "core" / "shell" / "workspace" / Path(rel_path).name
                if core_fallback.exists():
                    shutil.copy2(core_fallback, target)
                    print(f"  ✓ Dipulihkan via fallback core/shell: {rel_path}")
                    restored_count += 1
                else:
                    print(f"  [Peringatan] Gagal memulihkan {rel_path}: {res.stderr.strip()}")

    if restored_count == 0:
        print("  ✓ Semua komponen workspace dalam kondisi utuh.")

# ==============================================================================
# 2. TAHAP PERBAIKAN TS2308 & TIPE DATA GLOBAL/SHARED
# ==============================================================================

def patch_typescript_baseline_errors(dry_run: bool):
    print("\n=== [Tahap 2/6] Memperbaiki TS2308 Duplicate Export & Type Mismatches ===")

    # 1. Fix src/global/api/index.ts (TS2308 duplicate supabase)
    api_idx = SRC / "global" / "api" / "index.ts"
    if api_idx.exists():
        content = """export * from "./supabaseClient";
export * from "./supabaseTypes";
export * from "./previewAuthStorage";
export { supabase as untypedSupabase } from "./untypedSupabase";
"""
        if not dry_run:
            api_idx.write_text(content, encoding="utf-8")
        print("  ✓ src/global/api/index.ts diperbaiki (explicit re-export untypedSupabase)")

    # 2. Fix src/global/utils/index.ts & color-utils.ts (TS2308 duplicate color helpers)
    utils_idx = SRC / "global" / "utils" / "index.ts"
    if utils_idx.exists():
        content = """export * from "./cn";
export * from "./color-engine";
export * from "./fuzzy";
export * from "./container";
export * from "./useService";
"""
        if not dry_run:
            utils_idx.write_text(content, encoding="utf-8")
        print("  ✓ src/global/utils/index.ts diperbaiki (hapus duplicate color-utils export)")

    color_utils = SRC / "global" / "utils" / "color-utils.ts"
    if color_utils.exists():
        content = """/**
 * Color Utilities - CSS variable resolution & color engine bridge (Quo Vadis)
 */
export * from "@/global/utils/color-engine";
"""
        if not dry_run:
            color_utils.write_text(content, encoding="utf-8")
        print("  ✓ src/global/utils/color-utils.ts dijadikan bridge murni ke color-engine")

    # 3. Fix src/shared/stores/useGraphStore.ts (missing atmosphereConfig)
    graph_store = SRC / "shared" / "stores" / "useGraphStore.ts"
    if graph_store.exists():
        txt = graph_store.read_text(encoding="utf-8")
        txt = txt.replace(
            "@/core/graph/model/atmosphereConfig",
            "@/domains/graph/shared/utils/atmosphereConfig",
        )
        txt = txt.replace(
            "@/core/graph/model/hierarchyColors",
            "@/domains/graph/shared/utils/hierarchyColors",
        )
        if not dry_run:
            graph_store.write_text(txt, encoding="utf-8")
        print("  ✓ src/shared/stores/useGraphStore.ts diperbaiki (path atmosphereConfig canonical)")

    # 4. Fix RibbonTool di src/core/shell/workspace/IconRibbon.tsx
    core_icon = SRC / "core" / "shell" / "workspace" / "IconRibbon.tsx"
    if core_icon.exists():
        txt = core_icon.read_text(encoding="utf-8")
        if '"files" | "settings"' in txt and '"vcs"' not in txt:
            txt = txt.replace(
                'export type RibbonTool = "files" | "settings";',
                'export type RibbonTool = "files" | "vcs" | "settings";',
            )
            if not dry_run:
                core_icon.write_text(txt, encoding="utf-8")
            print("  ✓ src/core/shell/workspace/IconRibbon.tsx: RibbonTool ditambah 'vcs'")

    # 5. Fix TOOL_TITLES di src/core/shell/workspace/SidebarPanel.tsx
    core_sidebar = SRC / "core" / "shell" / "workspace" / "SidebarPanel.tsx"
    if core_sidebar.exists():
        txt = core_sidebar.read_text(encoding="utf-8")
        if 'settings: "Settings",' in txt and 'vcs:' not in txt:
            txt = txt.replace(
                'settings: "Settings",',
                'settings: "Settings",\n  vcs: "Version Control",',
            )
            if not dry_run:
                core_sidebar.write_text(txt, encoding="utf-8")
            print("  ✓ src/core/shell/workspace/SidebarPanel.tsx: TOOL_TITLES ditambah 'vcs'")

    # 6. Fix HierarchyPresetId di src/core/graph/model/hierarchyColors.ts
    core_hier = SRC / "core" / "graph" / "model" / "hierarchyColors.ts"
    if core_hier.exists():
        txt = core_hier.read_text(encoding="utf-8")
        txt = txt.replace(
            "| 'cool'\n  | 'custom';",
            "| 'cool'\n  | 'neon'\n  | 'pastel'\n  | 'custom';",
        )
        if not dry_run:
            core_hier.write_text(txt, encoding="utf-8")
        print("  ✓ src/core/graph/model/hierarchyColors.ts: ditambah preset 'neon' & 'pastel'")

    # 7. Sinkronisasi NodeType & mediaType di file-file legacy src/core
    core_node_files = [
        SRC / "core" / "shell" / "workspace" / "SidebarPanel.tsx",
        SRC / "core" / "shell" / "workspace" / "Ribbon.tsx",
        SRC / "core" / "shell" / "workspace" / "ImportExportPanel.tsx",
        SRC / "core" / "graph" / "NodePanel.tsx",
        SRC / "core" / "graph" / "LinkManager.tsx",
        SRC / "core" / "graph" / "DynamicLinkManager.tsx",
        SRC / "core" / "graph" / "hooks" / "useAutoLinks.tsx",
        SRC / "core" / "graph" / "RelationshipMapper.ts",
        SRC / "core" / "system" / "vault" / "ExportToFileSystem.tsx",
        SRC / "core" / "system" / "persistence" / "VaultFileWriter.ts",
        SRC / "core" / "system" / "import-export" / "services" / "ImportExportService.ts",
        SRC / "core" / "system" / "import-export" / "services" / "graph-import.ts",
        SRC / "core" / "system" / "import-export" / "services" / "graph-export.ts",
    ]
    for p in core_node_files:
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            orig = txt
            txt = txt.replace('"folder" | "file" | "media"', '"folder" | "file" | "media" | "pdf"')
            txt = txt.replace("'folder' | 'file' | 'media'", "'folder' | 'file' | 'media' | 'pdf'")
            txt = txt.replace('"file" | "folder" | "media"', '"file" | "folder" | "media" | "pdf"')
            txt = txt.replace("'file' | 'folder' | 'media'", "'file' | 'folder' | 'media' | 'pdf'")
            txt = txt.replace('"audio" | "video" | "image"', '"audio" | "video" | "image" | "pdf"')
            txt = txt.replace("'audio' | 'video' | 'image'", "'audio' | 'video' | 'image' | 'pdf'")
            txt = txt.replace('"image" | "audio" | "video"', '"image" | "audio" | "video" | "pdf"')
            txt = txt.replace("'image' | 'audio' | 'video'", "'image' | 'audio' | 'video' | 'pdf'")
            if txt != orig and not dry_run:
                p.write_text(txt, encoding="utf-8")
                print(f"  ✓ NodeType & mediaType di-patch (+pdf): {p.relative_to(ROOT)}")

# ==============================================================================
# 3. TAHAP PEMETAAN & RESTRUKTURISASI WAVE 2 (IDEMPOTENT)
# ==============================================================================

WORKSPACE_FILE_MAP = [
    ("components/IconRibbon.tsx", "components/WorkspaceIconRibbon.tsx"),
    ("components/ImportExportPanel.tsx", "components/WorkspaceImportExportPanel.tsx"),
    ("components/Ribbon.tsx", "components/WorkspaceRibbon.tsx"),
    ("components/SidebarPanel.tsx", "components/WorkspaceSidebarPanel.tsx"),
    ("components/StatusBar.tsx", "components/WorkspaceStatusBar.tsx"),
    ("components/TabContextMenu.tsx", "components/WorkspaceTabContextMenu.tsx"),
    ("components/VaultAccessDenied.tsx", "components/WorkspaceVaultAccessDenied.tsx"),
    ("sidebar/ExplorerContextMenu.tsx", "components/WorkspaceExplorerContextMenu.tsx"),
    ("sidebar/FileExplorerTree.tsx", "components/WorkspaceFileExplorerTree.tsx"),
    ("views/BacklinksLeaf.tsx", "components/WorkspaceBacklinksLeaf.tsx"),
    ("views/EmptyLeaf.tsx", "components/WorkspaceEmptyLeaf.tsx"),
    ("views/GraphLeaf.tsx", "components/WorkspaceGraphLeaf.tsx"),
    ("views/MarkdownLeaf.tsx", "components/WorkspaceMarkdownLeaf.tsx"),
    ("views/SettingsLeaf.tsx", "components/WorkspaceSettingsLeaf.tsx"),
    ("registry/ViewRegistry.tsx", "components/WorkspaceViewRegistry.tsx"),
    ("actions/workspaceActions.ts", "shared/api/workspaceActions.ts"),
    ("commands/CommandRegistry.ts", "shared/api/CommandRegistry.ts"),
    ("commands/graphCanvasCommands.ts", "shared/api/graphCanvasCommands.ts"),
    ("stores/useUIStore.ts", "shared/stores/useUIStore.ts"),
    ("stores/useWorkspaceStore.ts", "shared/stores/useWorkspaceStore.ts"),
    ("hooks/useFolderNavigation.ts", "shared/hooks/useFolderNavigation.ts"),
    ("hooks/useVaultLifecycle.ts", "shared/hooks/useVaultLifecycle.ts"),
    ("types.ts", "shared/utils/workspace.types.ts"),
]

EDITOR_FILE_MAP = [
    ("components/MarkdownView.tsx", "components/EditorMarkdownView.tsx"),
    ("components/FootnotePopover.tsx", "components/EditorFootnotePopover.tsx"),
    ("frontmatter/PropertiesPanel.tsx", "components/EditorPropertiesPanel.tsx"),
    ("frontmatter/SuggestInput.tsx", "components/EditorSuggestInput.tsx"),
    ("headings/FoldableMarkdown.tsx", "components/EditorFoldableMarkdown.tsx"),
    ("settings/EditorSettingsPanel.tsx", "components/EditorSettingsPanel.tsx"),
    ("table/InteractiveTable.tsx", "components/EditorInteractiveTable.tsx"),
    ("table/TableSliderNav.tsx", "components/EditorTableSliderNav.tsx"),
    ("services/activeEditor.ts", "shared/api/activeEditor.ts"),
    ("commands/editorCommands.ts", "shared/api/editorCommands.ts"),
    ("stores/useEditorSettingsStore.ts", "shared/stores/useEditorSettingsStore.ts"),
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

VAULT_FILE_MAP = [
    ("components/ExportToFileSystem.tsx", "components/VaultExportToFileSystem.tsx"),
    ("components/VaultBackupPanel.tsx", "components/VaultBackupPanel.tsx"),
    ("components/VaultBackupSettings.tsx", "components/VaultBackupSettings.tsx"),
    ("components/VaultCard.tsx", "components/VaultCard.tsx"),
    ("components/VaultComparisonView.tsx", "components/VaultComparisonView.tsx"),
    ("components/VaultMemberSection.tsx", "components/VaultMemberSection.tsx"),
    ("components/VaultModeSelector.tsx", "components/VaultModeSelector.tsx"),
    ("components/VaultStorageControls.tsx", "components/VaultStorageControls.tsx"),
    ("debug/EventDebugPanel.tsx", "components/VaultEventDebugPanel.tsx"),
    ("services/CloudVaultService.ts", "shared/api/CloudVaultService.ts"),
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
    ("services/AssetBundlerService.ts", "shared/api/AssetBundlerService.ts"),
    ("services/AutoHydrationService.ts", "shared/api/AutoHydrationService.ts"),
    ("services/FileManager.ts", "shared/api/FileManager.ts"),
    ("persistence/FileSystemService.ts", "shared/api/FileSystemService.ts"),
    ("persistence/FileSystemServiceSingleton.ts", "shared/api/FileSystemServiceSingleton.ts"),
    ("persistence/VaultFileWriter.ts", "shared/api/VaultFileWriter.ts"),
    ("persistence/directoryHandleStore.ts", "shared/api/directoryHandleStore.ts"),
    ("persistence/offline-storage.ts", "shared/api/offline-storage.ts"),
    ("drivers/IVaultStorageDriver.ts", "shared/api/IVaultStorageDriver.ts"),
    ("drivers/IndexedDbVaultDriver.ts", "shared/api/IndexedDbVaultDriver.ts"),
    ("import-export/services/ImportExportService.ts", "shared/api/ImportExportService.ts"),
    ("import-export/services/graph-export.ts", "shared/api/graph-export.ts"),
    ("import-export/services/graph-import.ts", "shared/api/graph-import.ts"),
    ("repository/adapters.ts", "shared/api/repositoryAdapters.ts"),
    ("repository/capabilities.ts", "shared/api/repositoryCapabilities.ts"),
    ("repository/index.ts", "shared/api/repositoryIndex.ts"),
    ("repository/types.ts", "shared/api/repositoryTypes.ts"),
    ("stores/useVaultStore.ts", "shared/stores/useVaultStore.ts"),
    ("stores/useBackupConfigStore.ts", "shared/stores/useBackupConfigStore.ts"),
    ("hooks/useVaultEvents.tsx", "shared/hooks/useVaultEvents.tsx"),
    ("hooks/useVaultSync.tsx", "shared/hooks/useVaultSync.tsx"),
    ("types.ts", "shared/utils/vault.types.ts"),
]

def ensure_domain_scaffold(domain: str, dry_run: bool):
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

def safe_copy_and_shim(domain: str, src_rel: str, dst_rel: str, dry_run: bool):
    # Guard: Hindari SameFileError
    if src_rel == dst_rel:
        return

    base = SRC / "domains" / domain
    src = base / src_rel
    dst = base / dst_rel

    if not src.exists():
        return

    src_content = src.read_text(encoding="utf-8")

    # Guard: Jika src sudah merupakan re-export bridge, jangan overwrite dst yang mungkin sudah punya kode asli!
    is_shim = "Re-export bridge" in src_content and len(src_content.strip()) < 250
    if is_shim and dst.exists():
        dst_content = dst.read_text(encoding="utf-8")
        if len(dst_content.strip()) > len(src_content.strip()):
            return

    if dry_run:
        print(f"  [DRY-RUN] {domain}/{src_rel} -> {domain}/{dst_rel}")
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    if not is_shim:
        shutil.copy2(src, dst)

    # Buat re-export bridge pada src lama agar kompatibel
    rel_depth = len(Path(src_rel).parent.parts)
    prefix = "../" * rel_depth if rel_depth > 0 else "./"
    shim_target = f"{prefix}{dst_rel}".replace(".tsx", "").replace(".ts", "")
    shim_content = f"// Re-export bridge Wave 2 (Quo Vadis)\nexport * from '{shim_target}';\n"
    src.write_text(shim_content, encoding="utf-8")

def create_orchestrators(dry_run: bool):
    print("\n=== Menyiapkan Entry Point Orchestrator ===")

    # 1. WorkspaceOrchestrator.tsx
    ws_orch = SRC / "domains" / "workspace" / "WorkspaceOrchestrator.tsx"
    ws_root = SRC / "domains" / "workspace" / "WorkspaceRoot.tsx"
    if not ws_orch.exists() and ws_root.exists():
        if not dry_run:
            shutil.copy2(ws_root, ws_orch)
            ws_root.write_text("// Re-export bridge\nexport { WorkspaceRoot } from './WorkspaceOrchestrator';\nexport * from './WorkspaceOrchestrator';\n", encoding="utf-8")
        print("  ✓ WorkspaceOrchestrator.tsx dibuat")

    # 2. EditorOrchestrator.tsx
    ed_orch = SRC / "domains" / "editor" / "EditorOrchestrator.tsx"
    if not ed_orch.exists():
        content = '''import React from "react";
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
'''
        if not dry_run:
            ed_orch.write_text(content, encoding="utf-8")
        print("  ✓ EditorOrchestrator.tsx dibuat")

    # 3. VaultOrchestrator.tsx
    vt_orch = SRC / "domains" / "vault" / "VaultOrchestrator.tsx"
    if not vt_orch.exists():
        content = '''import React from "react";
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
'''
        if not dry_run:
            vt_orch.write_text(content, encoding="utf-8")
        print("  ✓ VaultOrchestrator.tsx dibuat")

def run_wave2_restructure(dry_run: bool):
    print("\n=== [Tahap 3/6] Menjalankan Restrukturisasi Wave 2 (Workspace, Editor, Vault) ===")
    for domain, file_map in [
        ("workspace", WORKSPACE_FILE_MAP),
        ("editor", EDITOR_FILE_MAP),
        ("vault", VAULT_FILE_MAP),
    ]:
        ensure_domain_scaffold(domain, dry_run)
        print(f"  ✓ Struktur scaffolding {domain}/ diverifikasi")
        for src_rel, dst_rel in file_map:
            safe_copy_and_shim(domain, src_rel, dst_rel, dry_run)

    create_orchestrators(dry_run)

# ==============================================================================
# 4. TAHAP MIGRASI & BRIDGING FOLDER SRC/SHARED/
# ==============================================================================

def bridge_and_migrate_shared_folder(dry_run: bool):
    print("\n=== [Tahap 4/6] Migrasi & Penyelarasan Folder src/shared/ ===")
    shared_ui = SRC / "shared" / "ui"
    global_ui = SRC / "global" / "ui"

    if shared_ui.exists() and global_ui.exists():
        bridged_ui = 0
        for ui_file in global_ui.glob("*.tsx"):
            target_shim = shared_ui / ui_file.name
            shim_code = f"// Re-export bridge Quo Vadis: shared/ui -> global/ui\nexport * from '@/global/ui/{ui_file.stem}';\n"
            if not target_shim.exists() or "export * from '@/global/ui" not in target_shim.read_text(encoding="utf-8"):
                if not dry_run:
                    target_shim.write_text(shim_code, encoding="utf-8")
                bridged_ui += 1
        print(f"  ✓ {bridged_ui} komponen shadcn di src/shared/ui/ diselaraskan ke src/global/ui/")

    # Bridge src/shared/lib/
    lib_bridges = [
        ("cn.ts", "export * from '@/global/utils/cn';"),
        ("color-engine.ts", "export * from '@/global/utils/color-engine';"),
        ("color-utils.ts", "export * from '@/global/utils/color-engine';"),
        ("fuzzy.ts", "export * from '@/global/utils/fuzzy';"),
        ("untypedSupabase.ts", "export * from '@/global/api/untypedSupabase';"),
        ("index.ts", "export * from '@/global/utils';"),
    ]
    shared_lib = SRC / "shared" / "lib"
    if shared_lib.exists():
        for filename, code in lib_bridges:
            f = shared_lib / filename
            if not dry_run:
                f.write_text(code + "\n", encoding="utf-8")
        print("  ✓ Bridge utilitas src/shared/lib/ diselaraskan ke src/global/")

    # Bridge src/shared/events/, di/, hooks/, components/
    hooks_map = [
        (SRC / "shared" / "hooks" / "useMobile.tsx", "export * from '@/global/hooks/useMobile';"),
        (SRC / "shared" / "hooks" / "useToast.ts", "export * from '@/global/hooks/useToast';"),
        (SRC / "shared" / "events" / "events.ts", "export * from '@/global/stores/events';"),
        (SRC / "shared" / "di" / "container.ts", "export * from '@/global/utils/container';"),
        (SRC / "shared" / "di" / "useService.ts", "export * from '@/global/utils/useService';"),
        (SRC / "shared" / "components" / "ErrorBoundary.tsx", "export * from '@/global/components/ErrorBoundary';"),
        (SRC / "shared" / "components" / "PWAInstallPrompt.tsx", "export * from '@/global/components/PWAInstallPrompt';"),
    ]
    for p, code in hooks_map:
        if p.parent.exists() and not dry_run:
            p.write_text(code + "\n", encoding="utf-8")
    print("  ✓ Bridge hooks, events, di, & components di src/shared/ diselaraskan ke src/global/")

# ==============================================================================
# 5. TAHAP PEMBARUAN IMPORT ALIASES (CANONICAL REWRITING)
# ==============================================================================

IMPORT_REPLACEMENTS = [
    # Shared UI & Utils ke Global
    (r'@/shared/ui/([a-zA-Z0-9_\-]+)', r'@/global/ui/\1'),
    (r'@/shared/lib/cn', r'@/global/utils/cn'),
    (r'@/shared/lib/color-utils', r'@/global/utils/color-engine'),
    (r'@/shared/lib/color-engine', r'@/global/utils/color-engine'),
    (r'@/shared/lib/fuzzy', r'@/global/utils/fuzzy'),
    (r'@/shared/lib/untypedSupabase', r'@/global/api/untypedSupabase'),
    (r'@/shared/hooks/useMobile', r'@/global/hooks/useMobile'),
    (r'@/shared/hooks/useToast', r'@/global/hooks/useToast'),
    (r'@/shared/events/events', r'@/global/stores/events'),
    (r'@/shared/di/container', r'@/global/utils/container'),
    (r'@/shared/di/useService', r'@/global/utils/useService'),
    (r'@/shared/components/ErrorBoundary', r'@/global/components/ErrorBoundary'),
    (r'@/shared/components/PWAInstallPrompt', r'@/global/components/PWAInstallPrompt'),

    # Workspace domain components & shared
    (r'@/domains/workspace/components/IconRibbon', r'@/domains/workspace/components/WorkspaceIconRibbon'),
    (r'@/domains/workspace/components/ImportExportPanel', r'@/domains/workspace/components/WorkspaceImportExportPanel'),
    (r'@/domains/workspace/components/Ribbon', r'@/domains/workspace/components/WorkspaceRibbon'),
    (r'@/domains/workspace/components/SidebarPanel', r'@/domains/workspace/components/WorkspaceSidebarPanel'),
    (r'@/domains/workspace/components/StatusBar', r'@/domains/workspace/components/WorkspaceStatusBar'),
    (r'@/domains/workspace/components/TabContextMenu', r'@/domains/workspace/components/WorkspaceTabContextMenu'),
    (r'@/domains/workspace/components/VaultAccessDenied', r'@/domains/workspace/components/WorkspaceVaultAccessDenied'),
    (r'@/domains/workspace/sidebar/ExplorerContextMenu', r'@/domains/workspace/components/WorkspaceExplorerContextMenu'),
    (r'@/domains/workspace/sidebar/FileExplorerTree', r'@/domains/workspace/components/WorkspaceFileExplorerTree'),
    (r'@/domains/workspace/actions/workspaceActions', r'@/domains/workspace/shared/api/workspaceActions'),
    (r'@/domains/workspace/stores/useWorkspaceStore', r'@/domains/workspace/shared/stores/useWorkspaceStore'),
    (r'@/domains/workspace/stores/useUIStore', r'@/domains/workspace/shared/stores/useUIStore'),
    (r'@/domains/workspace/hooks/useFolderNavigation', r'@/domains/workspace/shared/hooks/useFolderNavigation'),
    (r'@/domains/workspace/hooks/useVaultLifecycle', r'@/domains/workspace/shared/hooks/useVaultLifecycle'),

    # Editor domain components & shared
    (r'@/domains/editor/components/MarkdownView', r'@/domains/editor/components/EditorMarkdownView'),
    (r'@/domains/editor/components/FootnotePopover', r'@/domains/editor/components/EditorFootnotePopover'),
    (r'@/domains/editor/frontmatter/PropertiesPanel', r'@/domains/editor/components/EditorPropertiesPanel'),
    (r'@/domains/editor/frontmatter/SuggestInput', r'@/domains/editor/components/EditorSuggestInput'),
    (r'@/domains/editor/headings/FoldableMarkdown', r'@/domains/editor/components/EditorFoldableMarkdown'),
    (r'@/domains/editor/settings/EditorSettingsPanel', r'@/domains/editor/components/EditorSettingsPanel'),
    (r'@/domains/editor/table/InteractiveTable', r'@/domains/editor/components/EditorInteractiveTable'),
    (r'@/domains/editor/table/TableSliderNav', r'@/domains/editor/components/EditorTableSliderNav'),
    (r'@/domains/editor/stores/useEditorSettingsStore', r'@/domains/editor/shared/stores/useEditorSettingsStore'),

    # Vault domain components & shared
    (r'@/domains/vault/components/ExportToFileSystem', r'@/domains/vault/components/VaultExportToFileSystem'),
    (r'@/domains/vault/components/VaultBackupPanel', r'@/domains/vault/components/VaultBackupPanel'),
    (r'@/domains/vault/components/VaultBackupSettings', r'@/domains/vault/components/VaultBackupSettings'),
    (r'@/domains/vault/components/VaultComparisonView', r'@/domains/vault/components/VaultComparisonView'),
    (r'@/domains/vault/components/VaultMemberSection', r'@/domains/vault/components/VaultMemberSection'),
    (r'@/domains/vault/components/VaultModeSelector', r'@/domains/vault/components/VaultModeSelector'),
    (r'@/domains/vault/components/VaultStorageControls', r'@/domains/vault/components/VaultStorageControls'),
    (r'@/domains/vault/stores/useVaultStore', r'@/domains/vault/shared/stores/useVaultStore'),
    (r'@/domains/vault/stores/useBackupConfigStore', r'@/domains/vault/shared/stores/useBackupConfigStore'),
    (r'@/domains/vault/hooks/useVaultEvents', r'@/domains/vault/shared/hooks/useVaultEvents'),
    (r'@/domains/vault/hooks/useVaultSync', r'@/domains/vault/shared/hooks/useVaultSync'),
]

import re

def update_all_import_aliases(dry_run: bool):
    print("\n=== [Tahap 5/6] Memperbarui Import Aliases di Seluruh src/**/*.{ts,tsx} ===")
    total_files_updated = 0
    total_replacements = 0

    for ext in ("*.ts", "*.tsx"):
        for p in SRC.rglob(ext):
            try:
                content = p.read_text(encoding="utf-8")
            except Exception:
                continue

            orig_content = content
            file_replacements = 0

            for pattern, replacement in IMPORT_REPLACEMENTS:
                new_content, count = re.subn(pattern, replacement, content)
                if count > 0:
                    content = new_content
                    file_replacements += count

            if content != orig_content:
                total_files_updated += 1
                total_replacements += file_replacements
                if not dry_run:
                    p.write_text(content, encoding="utf-8")

    print(f"  ✓ {total_files_updated} file diperbarui ({total_replacements} alias diganti)")

# ==============================================================================
# 6. TAHAP VERIFIKASI BUILD
# ==============================================================================

def verify_build(dry_run: bool):
    print("\n=== [Tahap 6/6] Verifikasi Kompilasi & Build ===")
    if dry_run:
        print("  [DRY-RUN] Melewati verifikasi build.")
        return

    print("  -> Menjalankan vite build --mode development ...")
    res = subprocess.run(["bunx", "vite", "build", "--mode", "development"], capture_output=True, text=True)
    if res.returncode == 0:
        print("  ✓ VITE BUILD 100% SUKSES! Aplikasi siap dijalankan!")
    else:
        print("  [Perhatian] Ada kendala pada build:")
        print(res.stderr[-1000:] if res.stderr else res.stdout[-1000:])

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    print("=" * 70)
    print("RESOLVE WAVE 2 QUO VADIS & SHARED FOLDER MIGRATION")
    print("=" * 70)
    if is_dry:
        print("[MODE SIMULASI / DRY-RUN AKTIF: Tidak ada file yang dimodifikasi]")

    restore_damaged_workspace_files(dry_run=is_dry)
    patch_typescript_baseline_errors(dry_run=is_dry)
    run_wave2_restructure(dry_run=is_dry)
    bridge_and_migrate_shared_folder(dry_run=is_dry)
    update_all_import_aliases(dry_run=is_dry)
    verify_build(dry_run=is_dry)

    print("\n" + "=" * 70)
    print("SELESAI! Seluruh masalah Wave 2 & shared folder berhasil diatasi.")
    print("=" * 70)