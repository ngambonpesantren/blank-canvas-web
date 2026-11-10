/**
 * Repository registry — the single entry point for vault storage.
 */

import type { VaultLocation } from "@/domains/vault/shared/utils/vault.types";
import type { VaultRepository, VaultRepositoryKind } from "@/domains/vault/shared/api/repositoryTypes";
import {
  CloudVaultRepository,
  FileSystemVaultRepository,
  IndexedDbVaultRepository,
  MemoryVaultRepository,
} from "@/domains/vault/shared/api/repositoryAdapters";

export * from "@/domains/vault/shared/api/repositoryTypes";
export * from "@/domains/vault/shared/api/repositoryCapabilities";

const repositories: Record<VaultRepositoryKind, VaultRepository> = {
  memory: new MemoryVaultRepository(),
  indexeddb: new IndexedDbVaultRepository(),
  filesystem: new FileSystemVaultRepository(),
  cloud: new CloudVaultRepository(),
};

export function getVaultRepository(kind: VaultRepositoryKind): VaultRepository {
  return repositories[kind];
}

/** Which adapter owns the notes of a vault at this location. */
export function repositoryForLocation(location: VaultLocation): VaultRepository {
  return location === "folder"
    ? repositories.filesystem
    : repositories.indexeddb;
}

/** What the UI is allowed to offer for a vault at this location. */
export function capabilitiesForLocation(location: VaultLocation) {
  return repositoryForLocation(location).capabilities;
}
