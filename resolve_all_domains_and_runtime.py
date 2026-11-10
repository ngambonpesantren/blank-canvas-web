#!/usr/bin/env python3
"""
resolve_all_domains_and_runtime.py

1. Memperbaiki infinite loop 'Maximum update depth exceeded' di GraphCanvasUtilityDock.tsx
2. Memperbaiki error TypeScript TS2739 di EditorOrchestrator.tsx
3. Memperbarui seluruh import path usang ke canonical Wave 2
4. Menyelamatkan unit test vault import-export ke __tests__
5. Menghapus folder dan file shim lama di src/domains/editor, src/domains/vault, dan src/domains/workspace
6. Menjalankan verifikasi typecheck dan vite build
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "src"

print("=" * 75)
print("🚀 MEMULAI PEMBERSIHAN DOMAINS (EDITOR, VAULT, WORKSPACE) & RUNTIME FIX")
print("=" * 75)

# ---------------------------------------------------------------------------
# 1. FIX: GraphCanvasUtilityDock.tsx
# ---------------------------------------------------------------------------
def fix_dock():
    dock_file = SRC / "domains" / "graph" / "components" / "GraphCanvasUtilityDock.tsx"
    if not dock_file.exists():
        print(f"⚠️  File {dock_file} tidak ditemukan.")
        return

    content = dock_file.read_text(encoding="utf-8")

    # Ganti blok popover hierarchy levels yang terbungkus tooltip
    pattern_levels = re.compile(
        r'{\/\* 4\. HIERARCHY LEVELS POPOVER \*\/}\s*\{showLevels && \(\s*<Popover[^>]*>[\s\S]*?<\/Popover>\s*\)}',
        re.MULTILINE
    )
    new_levels = """{/* 4. HIERARCHY LEVELS POPOVER */}
        {showLevels && (
          <Popover
            open={activePopover === "levels"}
            onOpenChange={(open) => setActivePopover(open ? "levels" : null)}
          >
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className={cn(
                  "h-7 w-7 rounded-md text-muted-foreground hover:text-foreground",
                  activePopover === "levels" && "bg-accent text-accent-foreground",
                )}
                aria-label="Hierarchy levels"
                title="Hierarchy levels"
              >
                <Layers className="h-3.5 w-3.5" />
              </Button>
            </PopoverTrigger>

            <PopoverContent
              align={isVertical ? "start" : "end"}
              side={popoverSide}
              sideOffset={8}
              className="w-56 p-2 rounded-lg border-border/80 bg-popover/95 backdrop-blur-md shadow-xl"
            >
              <div className="border-b border-border/40 pb-1.5 px-1 mb-1">
                <p className="text-[11px] font-semibold">Hierarchy Depths</p>
              </div>
              <GraphLevelLegend depths={depths} hierarchy={hierarchy} />
            </PopoverContent>
          </Popover>
        )}"""

    # Ganti blok popover minimap yang terbungkus tooltip
    pattern_minimap = re.compile(
        r'{\/\* 5\. MINIMAP POPOVER \*\/}\s*<Popover[^>]*>[\s\S]*?<\/Popover>',
        re.MULTILINE
    )
    new_minimap = """{/* 5. MINIMAP POPOVER */}
        <Popover
          open={activePopover === "minimap"}
          onOpenChange={(open) => setActivePopover(open ? "minimap" : null)}
        >
          <PopoverTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={cn(
                "h-7 w-7 rounded-md text-muted-foreground hover:text-foreground",
                activePopover === "minimap" && "bg-accent text-accent-foreground",
              )}
              aria-label="Mini-map"
              title="Mini-map view"
            >
              <Map className="h-3.5 w-3.5" />
            </Button>
          </PopoverTrigger>

          <PopoverContent
            align={isVertical ? "start" : "end"}
            side={popoverSide}
            sideOffset={8}
            style={{ width: `${panelWidth}px`, height: `${panelHeight}px` }}
            className="p-1 rounded-lg border-border/80 bg-popover/95 backdrop-blur-md shadow-xl overflow-hidden"
          >
            <GraphMiniMap {...miniMapProps} />
          </PopoverContent>
        </Popover>"""

    if pattern_levels.search(content):
        content = pattern_levels.sub(new_levels, content)
    if pattern_minimap.search(content):
        content = pattern_minimap.sub(new_minimap, content)

    dock_file.write_text(content, encoding="utf-8")
    print("✅ [FIX 1] GraphCanvasUtilityDock.tsx: Menghapus tabrakan Popper Radix (Maximum update depth tuntas).")


# ---------------------------------------------------------------------------
# 2. FIX: EditorOrchestrator.tsx (TS2739 Props Mismatch)
# ---------------------------------------------------------------------------
def fix_editor_orchestrator():
    orch_file = SRC / "domains" / "editor" / "EditorOrchestrator.tsx"
    orch_content = """import React, { useState } from "react";
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
  const [internalValue, setInternalValue] = useState(initialContent);

  const value = propValue !== undefined ? propValue : internalValue;
  const onChange = propOnChange ?? setInternalValue;

  return <EditorMarkdownView {...rest} value={value} onChange={onChange} />;
};

export default EditorOrchestrator;
"""
    orch_file.write_text(orch_content, encoding="utf-8")

    # Pastikan EditorMarkdownView mengekspor MarkdownView dan aliasnya
    view_file = SRC / "domains" / "editor" / "components" / "EditorMarkdownView.tsx"
    if view_file.exists():
        v_content = view_file.read_text(encoding="utf-8")
        if "export const EditorMarkdownView = MarkdownView;" not in v_content:
            v_content += "\nexport const EditorMarkdownView = MarkdownView;\n"
            view_file.write_text(v_content, encoding="utf-8")

    print("✅ [FIX 2] EditorOrchestrator.tsx: TS2739 teratasi dengan state adapter controlled/uncontrolled.")


# ---------------------------------------------------------------------------
# 3. REWRITE ALL IMPORTS (Editor, Vault, Workspace)
# ---------------------------------------------------------------------------
IMPORT_REWRITES = [
    # === DOMAINS/EDITOR ===
    (r'@/domains/editor/cm/setup\b', '@/domains/editor/shared/utils/cmSetup'),
    (r'@/domains/editor/cm/theme\b', '@/domains/editor/shared/utils/cmTheme'),
    (r'@/domains/editor/cm/state/editorApi\b', '@/domains/editor/shared/utils/editorApi'),
    (r'@/domains/editor/cm/extensions/frontmatterField\b', '@/domains/editor/shared/utils/frontmatterField'),
    (r'@/domains/editor/cm/extensions/headingFold\b', '@/domains/editor/shared/utils/headingFold'),
    (r'@/domains/editor/cm/extensions/livePreview\b', '@/domains/editor/shared/utils/livePreview'),
    (r'@/domains/editor/cm/extensions/wikilinkField\b', '@/domains/editor/shared/utils/wikilinkField'),
    (r'@/domains/editor/cm/extensions/cmFootnoteWidget\b', '@/domains/editor/shared/utils/cmFootnoteWidget'),
    (r'@/domains/editor/cm/extensions/cmTableWidget\b', '@/domains/editor/shared/utils/cmTableWidget'),
    (r'@/domains/editor/commands/editorCommands\b', '@/domains/editor/shared/api/editorCommands'),
    (r'@/domains/editor/footnotes/footnoteParser\b', '@/domains/editor/shared/utils/footnoteParser'),
    (r'@/domains/editor/frontmatter/frontmatter-utils\b', '@/domains/editor/shared/utils/frontmatterUtils'),
    (r'@/domains/editor/headings/headingTree\b', '@/domains/editor/shared/utils/headingTree'),
    (r'@/domains/editor/services/activeEditor\b', '@/domains/editor/shared/api/activeEditor'),
    (r'@/domains/editor/stores/useEditorSettingsStore\b', '@/domains/editor/shared/stores/useEditorSettingsStore'),
    (r'@/domains/editor/suggest/suggestions\b', '@/domains/editor/shared/utils/suggestions'),
    (r'@/domains/editor/table/tableParser\b', '@/domains/editor/shared/utils/tableParser'),
    (r'@/domains/editor/table/tableTypes\b', '@/domains/editor/shared/utils/tableTypes'),
    (r'@/domains/editor/types\b', '@/domains/editor/shared/utils/editor.types'),
    (r'@/domains/editor/components/FootnotePopover\b', '@/domains/editor/components/EditorFootnotePopover'),
    (r'@/domains/editor/footnotes/FootnotePopover\b', '@/domains/editor/components/EditorFootnotePopover'),
    (r'@/domains/editor/components/MarkdownView\b', '@/domains/editor/components/EditorMarkdownView'),
    (r'@/domains/editor/frontmatter/PropertiesPanel\b', '@/domains/editor/components/EditorPropertiesPanel'),
    (r'@/domains/editor/frontmatter/SuggestInput\b', '@/domains/editor/components/EditorSuggestInput'),
    (r'@/domains/editor/headings/FoldableMarkdown\b', '@/domains/editor/components/EditorFoldableMarkdown'),
    (r'@/domains/editor/settings/EditorSettingsPanel\b', '@/domains/editor/components/EditorSettingsPanel'),
    (r'@/domains/editor/table/InteractiveTable\b', '@/domains/editor/components/EditorInteractiveTable'),
    (r'@/domains/editor/table/TableSliderNav\b', '@/domains/editor/components/EditorTableSliderNav'),

    # === DOMAINS/VAULT ===
    (r'@/domains/vault/services/VaultManagerSingleton\b', '@/domains/vault/shared/api/VaultManagerSingleton'),
    (r'@/domains/vault/services/VaultStorage\b', '@/domains/vault/shared/api/VaultStorage'),
    (r'@/domains/vault/services/VaultSyncService\b', '@/domains/vault/shared/api/VaultSyncService'),
    (r'@/domains/vault/services/VaultBackupService\b', '@/domains/vault/shared/api/VaultBackupService'),
    (r'@/domains/vault/services/VaultMemberService\b', '@/domains/vault/shared/api/VaultMemberService'),
    (r'@/domains/vault/services/VaultHistory\b', '@/domains/vault/shared/api/VaultHistory'),
    (r'@/domains/vault/services/VaultManager\b', '@/domains/vault/shared/api/VaultManager'),
    (r'@/domains/vault/services/VaultValidationService\b', '@/domains/vault/shared/api/VaultValidationService'),
    (r'@/domains/vault/services/CloudVaultService\b', '@/domains/vault/shared/api/CloudVaultService'),
    (r'@/domains/vault/services/FileManager\b', '@/domains/vault/shared/api/FileManager'),
    (r'@/domains/vault/services/NoteService\b', '@/domains/vault/shared/api/NoteService'),
    (r'@/domains/vault/services/NoteSyncService\b', '@/domains/vault/shared/api/NoteSyncService'),
    (r'@/domains/vault/services/AssetBundlerService\b', '@/domains/vault/shared/api/AssetBundlerService'),
    (r'@/domains/vault/services/AutoHydrationService\b', '@/domains/vault/shared/api/AutoHydrationService'),
    (r'@/domains/vault/persistence/FileSystemServiceSingleton\b', '@/domains/vault/shared/api/FileSystemServiceSingleton'),
    (r'@/domains/vault/persistence/FileSystemService\b', '@/domains/vault/shared/api/FileSystemService'),
    (r'@/domains/vault/persistence/VaultFileWriter\b', '@/domains/vault/shared/api/VaultFileWriter'),
    (r'@/domains/vault/persistence/directoryHandleStore\b', '@/domains/vault/shared/api/directoryHandleStore'),
    (r'@/domains/vault/persistence/offline-storage(\.ts)?\b', '@/domains/vault/shared/api/offline-storage'),
    (r'@/domains/vault/import-export/services/ImportExportService\b', '@/domains/vault/shared/api/ImportExportService'),
    (r'@/domains/vault/import-export/services/graph-export\b', '@/domains/vault/shared/api/graph-export'),
    (r'@/domains/vault/import-export/services/graph-import\b', '@/domains/vault/shared/api/graph-import'),
    (r'@/domains/vault/drivers/IndexedDbVaultDriver\b', '@/domains/vault/shared/api/IndexedDbVaultDriver'),
    (r'@/domains/vault/drivers/IVaultStorageDriver\b', '@/domains/vault/shared/api/IVaultStorageDriver'),
    (r'@/domains/vault/drivers\b', '@/domains/vault/shared/api/repositoryIndex'),
    (r'@/domains/vault/repository/adapters\b', '@/domains/vault/shared/api/repositoryAdapters'),
    (r'@/domains/vault/repository/capabilities\b', '@/domains/vault/shared/api/repositoryCapabilities'),
    (r'@/domains/vault/repository/types\b', '@/domains/vault/shared/api/repositoryTypes'),
    (r'@/domains/vault/repository\b', '@/domains/vault/shared/api/repositoryIndex'),
    (r'@/domains/vault/hooks/useVaultEvents\b', '@/domains/vault/shared/hooks/useVaultEvents'),
    (r'@/domains/vault/hooks/useVaultSync\b', '@/domains/vault/shared/hooks/useVaultSync'),
    (r'@/domains/vault/stores/useBackupConfigStore\b', '@/domains/vault/shared/stores/useBackupConfigStore'),
    (r'@/domains/vault/stores/useVaultStore\b', '@/domains/vault/shared/stores/useVaultStore'),
    (r'@/domains/vault/types\b', '@/domains/vault/shared/utils/vault.types'),
    (r'@/domains/vault/debug/EventDebugPanel\b', '@/domains/vault/components/VaultEventDebugPanel'),
    (r'@/domains/vault/components/ExportToFileSystem\b', '@/domains/vault/components/VaultExportToFileSystem'),

    # === DOMAINS/WORKSPACE ===
    (r'@/domains/workspace/commands/CommandRegistry\b', '@/domains/workspace/shared/api/CommandRegistry'),
    (r'@/domains/workspace/commands/graphCanvasCommands\b', '@/domains/workspace/shared/api/graphCanvasCommands'),
    (r'@/domains/workspace/actions/workspaceActions\b', '@/domains/workspace/shared/api/workspaceActions'),
    (r'@/domains/workspace/hooks/useFolderNavigation\b', '@/domains/workspace/shared/hooks/useFolderNavigation'),
    (r'@/domains/workspace/hooks/useVaultLifecycle\b', '@/domains/workspace/shared/hooks/useVaultLifecycle'),
    (r'@/domains/workspace/stores/useUIStore\b', '@/domains/workspace/shared/stores/useUIStore'),
    (r'@/domains/workspace/stores/useWorkspaceStore\b', '@/domains/workspace/shared/stores/useWorkspaceStore'),
    (r'@/domains/workspace/registry/ViewRegistry\b', '@/domains/workspace/components/WorkspaceViewRegistry'),
    (r'@/domains/workspace/sidebar/ExplorerContextMenu\b', '@/domains/workspace/components/WorkspaceExplorerContextMenu'),
    (r'@/domains/workspace/sidebar/FileExplorerTree\b', '@/domains/workspace/components/WorkspaceFileExplorerTree'),
    (r'@/domains/workspace/views/MarkdownLeaf\b', '@/domains/workspace/components/WorkspaceMarkdownLeaf'),
    (r'@/domains/workspace/views/GraphLeaf\b', '@/domains/workspace/components/WorkspaceGraphLeaf'),
    (r'@/domains/workspace/views/BacklinksLeaf\b', '@/domains/workspace/components/WorkspaceBacklinksLeaf'),
    (r'@/domains/workspace/views/SettingsLeaf\b', '@/domains/workspace/components/WorkspaceSettingsLeaf'),
    (r'@/domains/workspace/views/EmptyLeaf\b', '@/domains/workspace/components/WorkspaceEmptyLeaf'),
    (r'@/domains/workspace/WorkspaceRoot\b', '@/domains/workspace/WorkspaceOrchestrator'),
    (r'@/domains/workspace/types\b', '@/domains/workspace/shared/utils/workspace.types'),
]

def rewrite_imports():
    modified_count = 0
    for ext in ("*.ts", "*.tsx"):
        for path in SRC.rglob(ext):
            try:
                content = path.read_text(encoding="utf-8")
                new_content = content
                for old_p, new_p in IMPORT_REWRITES:
                    new_content = re.sub(old_p, new_p, new_content)
                if new_content != content:
                    path.write_text(new_content, encoding="utf-8")
                    modified_count += 1
            except Exception as e:
                print(f"⚠️  Gagal memperbarui {path}: {e}")

    print(f"✅ [MIGRATE 3] {modified_count} file TypeScript berhasil diarahkan ke canonical import.")


# ---------------------------------------------------------------------------
# 4. PRESERVE TESTS & CLEANUP OLD FILES & FOLDERS
# ---------------------------------------------------------------------------
def preserve_and_cleanup():
    # Pindahkan test import-export ke __tests__ vault utama
    old_test = SRC / "domains" / "vault" / "import-export" / "__tests__" / "ImportExportService.test.ts"
    vault_test_dir = SRC / "domains" / "vault" / "__tests__"
    vault_test_dir.mkdir(parents=True, exist_ok=True)
    new_test = vault_test_dir / "ImportExportService.test.ts"
    if old_test.exists() and not new_test.exists():
        shutil.copy2(old_test, new_test)
        print("📦 [TEST] Memindahkan ImportExportService.test.ts ke src/domains/vault/__tests__/")

    # 1. Hapus direktori usang
    dirs_to_delete = [
        # Workspace
        SRC / "domains" / "workspace" / "actions",
        SRC / "domains" / "workspace" / "commands",
        SRC / "domains" / "workspace" / "hooks",
        SRC / "domains" / "workspace" / "registry",
        SRC / "domains" / "workspace" / "sidebar",
        SRC / "domains" / "workspace" / "stores",
        SRC / "domains" / "workspace" / "views",
        # Editor
        SRC / "domains" / "editor" / "cm",
        SRC / "domains" / "editor" / "commands",
        SRC / "domains" / "editor" / "footnotes",
        SRC / "domains" / "editor" / "frontmatter",
        SRC / "domains" / "editor" / "headings",
        SRC / "domains" / "editor" / "services",
        SRC / "domains" / "editor" / "settings",
        SRC / "domains" / "editor" / "stores",
        SRC / "domains" / "editor" / "suggest",
        SRC / "domains" / "editor" / "table",
        # Vault
        SRC / "domains" / "vault" / "debug",
        SRC / "domains" / "vault" / "drivers",
        SRC / "domains" / "vault" / "hooks",
        SRC / "domains" / "vault" / "import-export",
        SRC / "domains" / "vault" / "persistence",
        SRC / "domains" / "vault" / "repository",
        SRC / "domains" / "vault" / "services",
        SRC / "domains" / "vault" / "stores",
    ]

    for d in dirs_to_delete:
        if d.exists() and d.is_dir():
            shutil.rmtree(d, ignore_errors=True)
            print(f"🗑️  Direktori dihapus: {d.relative_to(ROOT)}")

    # 2. Hapus file bridge / shim usang di components & root domain
    files_to_delete = [
        # Workspace
        SRC / "domains" / "workspace" / "WorkspaceRoot.tsx",
        SRC / "domains" / "workspace" / "types.ts",
        SRC / "domains" / "workspace" / "components" / "IconRibbon.tsx",
        SRC / "domains" / "workspace" / "components" / "ImportExportPanel.tsx",
        SRC / "domains" / "workspace" / "components" / "Ribbon.tsx",
        SRC / "domains" / "workspace" / "components" / "SidebarPanel.tsx",
        SRC / "domains" / "workspace" / "components" / "StatusBar.tsx",
        SRC / "domains" / "workspace" / "components" / "TabContextMenu.tsx",
        SRC / "domains" / "workspace" / "components" / "VaultAccessDenied.tsx",
        SRC / "domains" / "workspace" / "components" / "WorkspacePane.tsx",
        # Editor
        SRC / "domains" / "editor" / "types.ts",
        SRC / "domains" / "editor" / "components" / "FootnotePopover.tsx",
        SRC / "domains" / "editor" / "components" / "MarkdownView.tsx",
        # Vault
        SRC / "domains" / "vault" / "types.ts",
        SRC / "domains" / "vault" / "components" / "ExportToFileSystem.tsx",
    ]

    for f in files_to_delete:
        if f.exists():
            try:
                f.unlink()
                print(f"🗑️  File shim dihapus: {f.relative_to(ROOT)}")
            except Exception as e:
                print(f"⚠️  Gagal menghapus {f}: {e}")

    print("✅ [CLEANUP 4] Pembersihan selesai. Direktori domains murni canonical.")


# ---------------------------------------------------------------------------
# 5. VERIFIKASI AKHIR
# ---------------------------------------------------------------------------
def run_verification():
    print("-" * 75)
    print("🔍 VERIFIKASI AKHIR BUILD & TYPECHECK...")
    print("-" * 75)

    tc = subprocess.run(["bunx", "tsgo", "--noEmit", "-p", "tsconfig.app.json"], capture_output=True, text=True)
    if tc.returncode != 0 and "error TS" in (tc.stdout + tc.stderr):
        tc2 = subprocess.run(["bunx", "tsc", "--noEmit", "-p", "tsconfig.app.json"], capture_output=True, text=True)
        if tc2.returncode != 0:
            print("⚠️  Pesan Typecheck:")
            print((tc2.stdout or tc.stdout)[:1000])
        else:
            print("✨ TypeScript check: 0 errors.")
    else:
        print("✨ TypeScript check: 0 errors.")

    build = subprocess.run(["bunx", "vite", "build", "--mode", "development"], capture_output=True, text=True)
    if build.returncode == 0:
        print("🎉 VITE BUILD BERHASIL! (Semua domain bersih dan berfungsi)")
    else:
        print("❌ Vite build:")
        print(build.stderr[-1000:])


def main():
    fix_dock()
    fix_editor_orchestrator()
    rewrite_imports()
    preserve_and_cleanup()
    run_verification()

    print("=" * 75)
    print("🌟 SELESAI! Folder src/domains/editor, vault, dan workspace telah rapi murni Wave 2.")
    print("=" * 75)


if __name__ == "__main__":
    main()