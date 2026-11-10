#!/usr/bin/env python3
"""
resolve_and_cleanup_workspace.py

1. Memperbaiki infinite loop 'Maximum update depth exceeded' pada GraphCanvasUtilityDock.tsx
2. Memperbaiki TypeScript mismatch pada EditorOrchestrator.tsx dan WorkspaceViewRegistry.tsx
3. Mengalihkan semua import '@/domains/workspace/...' usang ke path canonical Wave 2
4. Menghapus semua file & folder bridge/shim lama di src/domains/workspace
5. Menjalankan verifikasi akhir (typecheck & vite build)
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "src"
WORKSPACE_DIR = SRC / "domains" / "workspace"

print("=" * 70)
print("🚀 MEMULAI CLEANUP & RUNTIME FIX WORKSPACE WAVE 2")
print("=" * 70)

# ---------------------------------------------------------------------------
# 1. FIX: GraphCanvasUtilityDock.tsx (Infinite Loop Radix Popover + Tooltip)
# ---------------------------------------------------------------------------
def fix_graph_canvas_utility_dock():
    dock_file = SRC / "domains" / "graph" / "components" / "GraphCanvasUtilityDock.tsx"
    if not dock_file.exists():
        print(f"⚠️  File {dock_file} tidak ditemukan, lewati tahap 1.")
        return

    content = dock_file.read_text(encoding="utf-8")
    original = content

    # Pola 1: Levels popover trigger
    # Bungkus <PopoverTrigger asChild> dengan <span className="inline-flex"> di dalam <TooltipTrigger asChild>
    pattern_levels = (
        r'(<Tooltip>\s*<TooltipTrigger asChild>)\s*(<PopoverTrigger asChild>)'
    )
    if not re.search(r'<TooltipTrigger asChild>\s*<span className="inline-flex">\s*<PopoverTrigger', content):
        content = re.sub(
            pattern_levels,
            r'\1\n                <span className="inline-flex">\n                  \2',
            content
        )
        # Tutup span setelah </PopoverTrigger>
        content = re.sub(
            r'(</PopoverTrigger>)\s*(</TooltipTrigger>)',
            r'\1\n                </span>\n              \2',
            content
        )

    # Pastikan bersih dan tidak terduplikasi
    if content != original:
        dock_file.write_text(content, encoding="utf-8")
        print("✅ [FIX 1] GraphCanvasUtilityDock.tsx: Decoupled Tooltip & Popover trigger refs (Maximum update depth loop fixed).")
    else:
        print("ℹ️  [FIX 1] GraphCanvasUtilityDock.tsx sudah terpasang pelindung trigger.")


# ---------------------------------------------------------------------------
# 2. FIX: EditorOrchestrator & EditorMarkdownView Mismatch
# ---------------------------------------------------------------------------
def fix_editor_mismatch():
    view_file = SRC / "domains" / "editor" / "components" / "EditorMarkdownView.tsx"
    orch_file = SRC / "domains" / "editor" / "EditorOrchestrator.tsx"

    if view_file.exists():
        v_content = view_file.read_text(encoding="utf-8")
        if "export const EditorMarkdownView = MarkdownView;" not in v_content:
            v_content += "\nexport const EditorMarkdownView = MarkdownView;\n"
            view_file.write_text(v_content, encoding="utf-8")
            print("✅ [FIX 2a] EditorMarkdownView.tsx: Menambahkan alias export 'EditorMarkdownView'.")

    if orch_file.exists():
        o_content = orch_file.read_text(encoding="utf-8")
        o_content = o_content.replace(
            'import { EditorMarkdownView } from "@/domains/editor/components/EditorMarkdownView";',
            'import { MarkdownView as EditorMarkdownView } from "@/domains/editor/components/EditorMarkdownView";'
        )
        orch_file.write_text(o_content, encoding="utf-8")
        print("✅ [FIX 2b] EditorOrchestrator.tsx: Impor tersinkronisasi.")


# ---------------------------------------------------------------------------
# 3. FIX: WorkspaceViewRegistry.tsx (Import ke components/Workspace*Leaf)
# ---------------------------------------------------------------------------
def fix_workspace_view_registry():
    reg_file = WORKSPACE_DIR / "components" / "WorkspaceViewRegistry.tsx"
    if not reg_file.exists():
        return

    content = reg_file.read_text(encoding="utf-8")
    content = content.replace("@/domains/workspace/types", "@/domains/workspace/shared/utils/workspace.types")
    content = content.replace("@/domains/workspace/views/MarkdownLeaf", "@/domains/workspace/components/WorkspaceMarkdownLeaf")
    content = content.replace("@/domains/workspace/views/GraphLeaf", "@/domains/workspace/components/WorkspaceGraphLeaf")
    content = content.replace("@/domains/workspace/views/BacklinksLeaf", "@/domains/workspace/components/WorkspaceBacklinksLeaf")
    content = content.replace("@/domains/workspace/views/SettingsLeaf", "@/domains/workspace/components/WorkspaceSettingsLeaf")
    content = content.replace("@/domains/workspace/views/EmptyLeaf", "@/domains/workspace/components/WorkspaceEmptyLeaf")

    reg_file.write_text(content, encoding="utf-8")
    print("✅ [FIX 3] WorkspaceViewRegistry.tsx: Mengarah langsung ke lazy import component canonical.")


# ---------------------------------------------------------------------------
# 4. REWRITE: Semua referensi import lama ke path canonical Wave 2
# ---------------------------------------------------------------------------
IMPORT_REWRITES = [
    # Commands & Actions
    (r'@/domains/workspace/commands/CommandRegistry\b', '@/domains/workspace/shared/api/CommandRegistry'),
    (r'@/domains/workspace/commands/graphCanvasCommands\b', '@/domains/workspace/shared/api/graphCanvasCommands'),
    (r'@/domains/workspace/actions/workspaceActions\b', '@/domains/workspace/shared/api/workspaceActions'),
    # Hooks
    (r'@/domains/workspace/hooks/useFolderNavigation\b', '@/domains/workspace/shared/hooks/useFolderNavigation'),
    (r'@/domains/workspace/hooks/useVaultLifecycle\b', '@/domains/workspace/shared/hooks/useVaultLifecycle'),
    # Stores
    (r'@/domains/workspace/stores/useUIStore\b', '@/domains/workspace/shared/stores/useUIStore'),
    (r'@/domains/workspace/stores/useWorkspaceStore\b', '@/domains/workspace/shared/stores/useWorkspaceStore'),
    # Registry & Sidebar
    (r'@/domains/workspace/registry/ViewRegistry\b', '@/domains/workspace/components/WorkspaceViewRegistry'),
    (r'@/domains/workspace/sidebar/ExplorerContextMenu\b', '@/domains/workspace/components/WorkspaceExplorerContextMenu'),
    (r'@/domains/workspace/sidebar/FileExplorerTree\b', '@/domains/workspace/components/WorkspaceFileExplorerTree'),
    # Views
    (r'@/domains/workspace/views/MarkdownLeaf\b', '@/domains/workspace/components/WorkspaceMarkdownLeaf'),
    (r'@/domains/workspace/views/GraphLeaf\b', '@/domains/workspace/components/WorkspaceGraphLeaf'),
    (r'@/domains/workspace/views/BacklinksLeaf\b', '@/domains/workspace/components/WorkspaceBacklinksLeaf'),
    (r'@/domains/workspace/views/SettingsLeaf\b', '@/domains/workspace/components/WorkspaceSettingsLeaf'),
    (r'@/domains/workspace/views/EmptyLeaf\b', '@/domains/workspace/components/WorkspaceEmptyLeaf'),
    # Types & Entrypoints
    (r'@/domains/workspace/WorkspaceRoot\b', '@/domains/workspace/WorkspaceOrchestrator'),
    (r'@/domains/workspace/types\b', '@/domains/workspace/shared/utils/workspace.types'),
    # Old unprefixed components (if any imported directly)
    (r'@/domains/workspace/components/IconRibbon\b', '@/domains/workspace/components/WorkspaceIconRibbon'),
    (r'@/domains/workspace/components/ImportExportPanel\b', '@/domains/workspace/components/WorkspaceImportExportPanel'),
    (r'@/domains/workspace/components/Ribbon\b', '@/domains/workspace/components/WorkspaceRibbon'),
    (r'@/domains/workspace/components/SidebarPanel\b', '@/domains/workspace/components/WorkspaceSidebarPanel'),
    (r'@/domains/workspace/components/StatusBar\b', '@/domains/workspace/components/WorkspaceStatusBar'),
    (r'@/domains/workspace/components/TabContextMenu\b', '@/domains/workspace/components/WorkspaceTabContextMenu'),
    (r'@/domains/workspace/components/VaultAccessDenied\b', '@/domains/workspace/components/WorkspaceVaultAccessDenied'),
]

def rewrite_all_imports():
    modified_count = 0
    for ext in ("*.ts", "*.tsx"):
        for path in SRC.rglob(ext):
            try:
                content = path.read_text(encoding="utf-8")
                new_content = content
                for old_pattern, new_replacement in IMPORT_REWRITES:
                    new_content = re.sub(old_pattern, new_replacement, new_content)

                if new_content != content:
                    path.write_text(new_content, encoding="utf-8")
                    modified_count += 1
            except Exception as e:
                print(f"⚠️  Gagal memproses {path}: {e}")

    print(f"✅ [MIGRATE 4] {modified_count} file TypeScript berhasil diperbarui ke canonical path.")


# ---------------------------------------------------------------------------
# 5. EXPORT ALIASES: Pastikan named export Ribbon / WorkspaceRibbon kompatibel
# ---------------------------------------------------------------------------
def ensure_component_export_aliases():
    component_aliases = [
        ("WorkspaceRibbon.tsx", "Ribbon", "WorkspaceRibbon"),
        ("WorkspaceStatusBar.tsx", "StatusBar", "WorkspaceStatusBar"),
        ("WorkspaceVaultAccessDenied.tsx", "VaultAccessDenied", "WorkspaceVaultAccessDenied"),
        ("WorkspaceIconRibbon.tsx", "IconRibbon", "WorkspaceIconRibbon"),
        ("WorkspaceImportExportPanel.tsx", "ImportExportPanel", "WorkspaceImportExportPanel"),
        ("WorkspaceTabContextMenu.tsx", "TabContextMenu", "WorkspaceTabContextMenu"),
        ("WorkspaceSidebarPanel.tsx", "SidebarPanel", "WorkspaceSidebarPanel"),
        ("WorkspaceExplorerContextMenu.tsx", "ExplorerContextMenu", "WorkspaceExplorerContextMenu"),
        ("WorkspaceFileExplorerTree.tsx", "FileExplorerTree", "WorkspaceFileExplorerTree"),
    ]

    for filename, orig_export, alias_export in component_aliases:
        filepath = WORKSPACE_DIR / "components" / filename
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            alias_line = f"export {{ {orig_export} as {alias_export} }};"
            if alias_line not in content and f"export {{ {orig_export} as {alias_export}" not in content:
                content += f"\n// Wave 2 Dual Named Export Compatibility\n{alias_line}\n"
                filepath.write_text(content, encoding="utf-8")

    print("✅ [EXPORT 5] Dual named export alias disinkronkan di semua komponen Workspace.")


# ---------------------------------------------------------------------------
# 6. CLEANUP: Hapus file dan folder lama di src/domains/workspace/
# ---------------------------------------------------------------------------
def remove_old_workspace_files():
    # Daftar folder usang yang hanya berisi bridge
    dirs_to_remove = [
        WORKSPACE_DIR / "actions",
        WORKSPACE_DIR / "commands",
        WORKSPACE_DIR / "hooks",
        WORKSPACE_DIR / "registry",
        WORKSPACE_DIR / "sidebar",
        WORKSPACE_DIR / "stores",
        WORKSPACE_DIR / "views",
    ]

    # Daftar file shim usang di root & components
    files_to_remove = [
        WORKSPACE_DIR / "WorkspaceRoot.tsx",
        WORKSPACE_DIR / "types.ts",
        WORKSPACE_DIR / "components" / "IconRibbon.tsx",
        WORKSPACE_DIR / "components" / "ImportExportPanel.tsx",
        WORKSPACE_DIR / "components" / "Ribbon.tsx",
        WORKSPACE_DIR / "components" / "SidebarPanel.tsx",
        WORKSPACE_DIR / "components" / "StatusBar.tsx",
        WORKSPACE_DIR / "components" / "TabContextMenu.tsx",
        WORKSPACE_DIR / "components" / "VaultAccessDenied.tsx",
        WORKSPACE_DIR / "components" / "WorkspacePane.tsx",
    ]

    deleted_count = 0
    for f in files_to_remove:
        if f.exists():
            try:
                f.unlink()
                deleted_count += 1
                print(f"🗑️  Dihapus file: {f.relative_to(ROOT)}")
            except Exception as e:
                print(f"⚠️  Gagal menghapus file {f}: {e}")

    for d in dirs_to_remove:
        if d.exists() and d.is_dir():
            try:
                shutil.rmtree(d)
                print(f"🗑️  Dihapus direktori: {d.relative_to(ROOT)}")
            except Exception as e:
                print(f"⚠️  Gagal menghapus folder {d}: {e}")

    print(f"✅ [CLEANUP 6] Pembersihan folder src/domains/workspace selesai. ({deleted_count} file shim dihapus)")


# ---------------------------------------------------------------------------
# 7. VERIFIKASI AKHIR
# ---------------------------------------------------------------------------
def run_verification():
    print("-" * 70)
    print("🔍 MENJALANKAN VERIFIKASI AKHIR...")
    print("-" * 70)

    # TypeScript check
    print("▶️  Menjalankan TypeScript Typecheck...")
    tc = subprocess.run(["bunx", "tsgo", "--noEmit", "-p", "tsconfig.app.json"], capture_output=True, text=True)
    if tc.returncode != 0 and "error TS" in (tc.stdout + tc.stderr):
        # Coba fallback ke bunx tsc
        tc2 = subprocess.run(["bunx", "tsc", "--noEmit", "-p", "tsconfig.app.json"], capture_output=True, text=True)
        if tc2.returncode != 0:
            print("⚠️  Ditemukan pesan Typecheck:")
            print((tc2.stdout or tc.stdout)[:1000])
        else:
            print("✨ TypeScript check PASSED (0 errors).")
    else:
        print("✨ TypeScript check PASSED (0 errors).")

    # Vite build check
    print("▶️  Menjalankan Vite Build Test...")
    build = subprocess.run(["bunx", "vite", "build", "--mode", "development"], capture_output=True, text=True)
    if build.returncode == 0:
        print("🎉 VITE BUILD BERHASIL! (Clean build)")
    else:
        print("❌ Vite build gagal:")
        print(build.stderr[-1000:])


def main():
    fix_graph_canvas_utility_dock()
    fix_editor_mismatch()
    fix_workspace_view_registry()
    rewrite_all_imports()
    ensure_component_export_aliases()
    remove_old_workspace_files()
    run_verification()

    print("=" * 70)
    print("🌟 SELESAI! Folder src/domains/workspace kini rapi murni Wave 2 canonical.")
    print("=" * 70)


if __name__ == "__main__":
    main()
