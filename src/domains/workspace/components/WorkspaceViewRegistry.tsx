/**
 * Maps a leaf view type to the component that renders it.
 * Views are lazy so a leaf only pulls in the code it needs.
 */

import { lazy, Suspense, type ComponentType } from 'react';
import type { ViewType, WorkspaceLeaf } from '@/domains/workspace/shared/utils/workspace.types';

export type LeafViewProps = { leaf: WorkspaceLeaf; isActive?: boolean };

const registry: Record<ViewType, ComponentType<LeafViewProps>> = {
  markdown: lazy(() => import('@/domains/workspace/components/WorkspaceMarkdownLeaf')),
  graph: lazy(() => import('@/domains/workspace/components/WorkspaceGraphLeaf')),
  backlinks: lazy(() => import('@/domains/workspace/components/WorkspaceBacklinksLeaf')),
  settings: lazy(() => import('@/domains/workspace/components/WorkspaceSettingsLeaf')),
  empty: lazy(() => import('@/domains/workspace/components/WorkspaceEmptyLeaf')),
};

export function LeafView({ leaf, isActive = true }: LeafViewProps) {
  const Component = registry[leaf.view.type] ?? registry.empty;
  return (
    <Suspense
      fallback={<div className="h-full flex items-center justify-center text-sm text-muted-foreground">Loading…</div>}
    >
      <Component leaf={leaf} isActive={isActive} />
    </Suspense>
  );
}