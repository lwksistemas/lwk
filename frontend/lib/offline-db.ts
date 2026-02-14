/**
 * IndexedDB para modo offline - Clínica da Beleza
 * Armazena pacientes, profissionais, procedimentos, agendamentos e fila de sync.
 */

import { openDB, DBSchema, IDBPDatabase } from "idb";

const DB_NAME = "clinica-beleza-offline";
const DB_VERSION = 1;

export interface OfflineDBSchema extends DBSchema {
  pacientes: { key: string; value: { lojaSlug: string; list: unknown[] } };
  profissionais: { key: string; value: { lojaSlug: string; list: unknown[] } };
  procedimentos: { key: string; value: { lojaSlug: string; list: unknown[] } };
  agendamentos: { key: string; value: { lojaSlug: string; list: unknown[] } };
  fila_sync: { key: number; value: FilaSyncItem };
}

export interface FilaSyncItem {
  tipo: "agendamento" | "paciente" | "profissional" | "procedimento";
  payload: unknown;
  lojaSlug?: string;
  createdAt: number;
}

function getLojaSlug(): string {
  if (typeof window === "undefined") return "";
  return sessionStorage.getItem("loja_slug") || (window.location.pathname.match(/\/loja\/([^/]+)\//)?.[1] ?? "") || "";
}

let dbPromise: Promise<IDBPDatabase<OfflineDBSchema>> | null = null;

export function getOfflineDB(): Promise<IDBPDatabase<OfflineDBSchema>> {
  if (!dbPromise) {
    dbPromise = openDB<OfflineDBSchema>(DB_NAME, DB_VERSION, {
      upgrade(database) {
        if (!database.objectStoreNames.contains("pacientes")) {
          database.createObjectStore("pacientes", { keyPath: "lojaSlug" });
        }
        if (!database.objectStoreNames.contains("profissionais")) {
          database.createObjectStore("profissionais", { keyPath: "lojaSlug" });
        }
        if (!database.objectStoreNames.contains("procedimentos")) {
          database.createObjectStore("procedimentos", { keyPath: "lojaSlug" });
        }
        if (!database.objectStoreNames.contains("agendamentos")) {
          database.createObjectStore("agendamentos", { keyPath: "lojaSlug" });
        }
        if (!database.objectStoreNames.contains("fila_sync")) {
          database.createObjectStore("fila_sync", { autoIncrement: true });
        }
      },
    });
  }
  return dbPromise;
}

// Fila_sync usa autoIncrement, então a key é number. Ajustar schema:
// idb com autoIncrement: keyPath pode ser "id" e autoIncrement true, então o valor pode ter id opcional.
// Na verdade createObjectStore("fila_sync", { autoIncrement: true }) não tem keyPath, então key é number.
// Vamos usar keyPath: "id" com autoIncrement para que cada item tenha id.
async function getDB() {
  const db = await getOfflineDB();
  return db;
}

export async function salvarPacientesOffline(list: unknown[]): Promise<void> {
  const slug = getLojaSlug();
  if (!slug) return;
  const database = await getDB();
  await database.put("pacientes", { lojaSlug: slug, list });
}

export async function buscarPacientesOffline(): Promise<unknown[]> {
  const slug = getLojaSlug();
  if (!slug) return [];
  const database = await getDB();
  const row = await database.get("pacientes", slug);
  return row?.list ?? [];
}

export async function salvarProfissionaisOffline(list: unknown[]): Promise<void> {
  const slug = getLojaSlug();
  if (!slug) return;
  const database = await getDB();
  await database.put("profissionais", { lojaSlug: slug, list });
}

export async function buscarProfissionaisOffline(): Promise<unknown[]> {
  const slug = getLojaSlug();
  if (!slug) return [];
  const database = await getDB();
  const row = await database.get("profissionais", slug);
  return row?.list ?? [];
}

export async function salvarProcedimentosOffline(list: unknown[]): Promise<void> {
  const slug = getLojaSlug();
  if (!slug) return;
  const database = await getDB();
  await database.put("procedimentos", { lojaSlug: slug, list });
}

export async function buscarProcedimentosOffline(): Promise<unknown[]> {
  const slug = getLojaSlug();
  if (!slug) return [];
  const database = await getDB();
  const row = await database.get("procedimentos", slug);
  return row?.list ?? [];
}

export async function salvarAgendamentosOffline(list: unknown[]): Promise<void> {
  const slug = getLojaSlug();
  if (!slug) return;
  const database = await getDB();
  await database.put("agendamentos", { lojaSlug: slug, list });
}

export async function buscarAgendamentosOffline(): Promise<unknown[]> {
  const slug = getLojaSlug();
  if (!slug) return [];
  const database = await getDB();
  const row = await database.get("agendamentos", slug);
  return row?.list ?? [];
}

export async function adicionarNaFilaSync(item: Omit<FilaSyncItem, "createdAt">): Promise<number> {
  const database = await getDB();
  const withMeta: FilaSyncItem = {
    ...item,
    lojaSlug: item.lojaSlug ?? getLojaSlug(),
    createdAt: Date.now(),
  };
  return database.add("fila_sync", withMeta);
}

export async function obterFilaSync(): Promise<Array<FilaSyncItem & { id: number }>> {
  const database = await getDB();
  const keys = await database.getAllKeys("fila_sync");
  const values = await database.getAll("fila_sync");
  return values.map((v, i) => ({ ...v, id: keys[i] as number }));
}

export async function limparFilaSync(): Promise<void> {
  const database = await getDB();
  const tx = database.transaction("fila_sync", "readwrite");
  await tx.store.clear();
  await tx.done;
}

export async function removerItemFilaSync(key: number): Promise<void> {
  const database = await getDB();
  await database.delete("fila_sync", key);
}

export { getLojaSlug };
