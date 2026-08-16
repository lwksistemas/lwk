'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { logger } from '@/lib/logger';

interface MidiaTenant {
  tenant: string;
  documento: string;
  nome: string;
  loja_id: number | null;
  slug: string | null;
  is_active: boolean;
  tipo: 'loja' | 'sistema' | 'orfao';
  folders: string[];
  folder_count: number;
}

interface MidiaFolder {
  folder: string;
  file_count: number;
  subfolder_count?: number;
}

interface MidiaSubfolder {
  name: string;
  path: string;
  file_count: number;
}

interface MidiaArquivo {
  filename: string;
  size: number;
  mtime: number;
  url: string;
  public_url: string;
}

function formatBytes(size: number): string {
  if (!size || size < 0) return '0 B';
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(ts: number): string {
  if (!ts) return '—';
  try {
    return new Date(ts * 1000).toLocaleString('pt-BR');
  } catch {
    return '—';
  }
}

export default function ServidorMidiaPage() {
  const router = useRouter();
  const [tenants, setTenants] = useState<MidiaTenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filtro, setFiltro] = useState('');
  const [tenantSel, setTenantSel] = useState<MidiaTenant | null>(null);
  const [folders, setFolders] = useState<MidiaFolder[]>([]);
  const [folderSel, setFolderSel] = useState<string | null>(null);
  const [files, setFiles] = useState<MidiaArquivo[]>([]);
  const [subfolders, setSubfolders] = useState<MidiaSubfolder[]>([]);
  const [truncated, setTruncated] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    if (!authService.isAuthenticated() || authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    carregarTenants();
  }, [router]);

  const carregarTenants = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/superadmin/midia/');
      setTenants(response.data?.tenants || []);
      setError('');
    } catch (err) {
      logger.warn('Erro ao listar mídia:', err);
      setError('Não foi possível carregar as pastas do servidor de mídia.');
    } finally {
      setLoading(false);
    }
  };

  const abrirTenant = useCallback(async (item: MidiaTenant) => {
    try {
      setLoadingDetail(true);
      setTenantSel(item);
      setFolderSel(null);
      setFiles([]);
      setSubfolders([]);
      setTruncated(false);
      const response = await apiClient.get(`/superadmin/midia/${item.tenant}/`);
      setFolders(response.data?.folders || []);
    } catch (err) {
      logger.warn('Erro ao listar pastas:', err);
      setError('Falha ao listar pastas desta loja.');
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  const abrirPasta = useCallback(async (folder: string) => {
    if (!tenantSel) return;
    try {
      setLoadingDetail(true);
      setFolderSel(folder);
      const response = await apiClient.get(
        `/superadmin/midia/${tenantSel.tenant}/${folder}/`,
      );
      setFiles(response.data?.files || []);
      setSubfolders(response.data?.subfolders || []);
      setTruncated(Boolean(response.data?.truncated));
    } catch (err) {
      logger.warn('Erro ao listar arquivos:', err);
      setError('Falha ao listar arquivos desta pasta.');
    } finally {
      setLoadingDetail(false);
    }
  }, [tenantSel]);

  const excluirArquivo = useCallback(async (file: MidiaArquivo) => {
    if (!tenantSel || !folderSel) return;
    if (!confirm(`Excluir "${file.filename}"? Esta ação não pode ser desfeita.`)) return;
    try {
      await apiClient.delete(`/superadmin/midia/${tenantSel.tenant}/delete/${folderSel}/${file.filename}/`);
      setFiles((prev) => prev.filter((f) => f.filename !== file.filename));
    } catch {
      setError('Falha ao excluir arquivo.');
    }
  }, [tenantSel, folderSel]);

  const filtrados = useMemo(() => {
    const q = filtro.trim().toLowerCase();
    if (!q) return tenants;
    return tenants.filter((t) =>
      [t.nome, t.documento, t.tenant, t.slug || ''].some((v) =>
        String(v).toLowerCase().includes(q),
      ),
    );
  }, [tenants, filtro]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <nav className="bg-purple-700 text-white shadow">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <div>
            <a href="/superadmin/dashboard" className="text-sm text-purple-100 hover:underline">
              ← Voltar ao dashboard
            </a>
            <h1 className="text-xl font-semibold mt-1">Servidor de Mídia</h1>
            <p className="text-sm text-purple-100">
              Pastas por loja (nome + CPF/CNPJ) em media.lwksistemas.com.br
            </p>
          </div>
          <button
            type="button"
            onClick={carregarTenants}
            className="rounded-lg bg-white/15 px-3 py-2 text-sm hover:bg-white/25"
          >
            Atualizar
          </button>
        </div>
      </nav>

      <main className="max-w-full mx-auto px-4 py-6 space-y-6">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700 dark:border-red-800 dark:bg-red-950/40 dark:text-red-200">
            {error}
          </div>
        )}

        {!tenantSel && (
          <section className="space-y-4">
            <input
              type="search"
              value={filtro}
              onChange={(e) => setFiltro(e.target.value)}
              placeholder="Buscar por nome, CPF ou CNPJ…"
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
            />

            {loading ? (
              <p className="text-sm text-gray-500">Carregando pastas…</p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {filtrados.map((item) => (
                  <button
                    key={item.tenant}
                    type="button"
                    onClick={() => abrirTenant(item)}
                    className="rounded-xl border border-gray-200 bg-white p-4 text-left shadow-sm transition hover:border-purple-300 hover:shadow dark:border-gray-800 dark:bg-gray-900"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-medium text-gray-900 dark:text-gray-100">
                          {item.nome}
                        </div>
                        <div className="mt-1 font-mono text-sm text-purple-700 dark:text-purple-300">
                          {item.documento}
                        </div>
                      </div>
                      <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                        {item.folder_count} pasta{item.folder_count === 1 ? '' : 's'}
                      </span>
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                      {item.tipo === 'sistema' && 'Pasta de sistema'}
                      {item.tipo === 'orfao' && 'Sem loja cadastrada'}
                      {item.tipo === 'loja' && (item.is_active ? 'Loja ativa' : 'Loja inativa')}
                    </div>
                  </button>
                ))}
                {!filtrados.length && (
                  <p className="text-sm text-gray-500 col-span-full">Nenhuma pasta encontrada.</p>
                )}
              </div>
            )}
          </section>
        )}

        {tenantSel && !folderSel && (
          <section className="space-y-4">
            <button
              type="button"
              onClick={() => {
                setTenantSel(null);
                setFolders([]);
              }}
              className="text-sm text-purple-700 hover:underline dark:text-purple-300"
            >
              ← Todas as lojas
            </button>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {tenantSel.nome}
              </h2>
              <p className="font-mono text-sm text-purple-700 dark:text-purple-300">
                {tenantSel.documento}
              </p>
            </div>
            {loadingDetail ? (
              <p className="text-sm text-gray-500">Carregando pastas…</p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                {folders.map((f) => (
                  <button
                    key={f.folder}
                    type="button"
                    onClick={() => abrirPasta(f.folder)}
                    className="rounded-xl border border-gray-200 bg-white p-4 text-left hover:border-purple-300 dark:border-gray-800 dark:bg-gray-900"
                  >
                    <div className="font-medium">{f.folder}/</div>
                    <div className="mt-1 text-xs text-gray-500">
                      {f.file_count} arquivo{f.file_count === 1 ? '' : 's'}
                      {f.subfolder_count
                        ? ` · ${f.subfolder_count} paciente${f.subfolder_count === 1 ? '' : 's'}`
                        : ''}
                    </div>
                  </button>
                ))}
                {!folders.length && (
                  <p className="text-sm text-gray-500">Nenhuma pasta com arquivos.</p>
                )}
              </div>
            )}
          </section>
        )}

        {tenantSel && folderSel && (
          <section className="space-y-4">
            <button
              type="button"
              onClick={() => {
                if (folderSel.includes('/')) {
                  const parent = folderSel.split('/').slice(0, -1).join('/');
                  abrirPasta(parent);
                  return;
                }
                setFolderSel(null);
                setFiles([]);
                setSubfolders([]);
                setTruncated(false);
              }}
              className="text-sm text-purple-700 hover:underline dark:text-purple-300"
            >
              ← {folderSel.includes('/') ? `Voltar em ${folderSel.split('/')[0]}` : `Pastas de ${tenantSel.nome}`}
            </button>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {tenantSel.nome} / {folderSel}
              </h2>
              <p className="font-mono text-sm text-purple-700 dark:text-purple-300">
                {tenantSel.documento}
              </p>
            </div>
            {truncated && (
              <p className="text-sm text-amber-700 dark:text-amber-300">
                Mostrando os 500 arquivos mais recentes.
              </p>
            )}
            {loadingDetail ? (
              <p className="text-sm text-gray-500">Carregando…</p>
            ) : (
              <>
                {!!subfolders.length && (
                  <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                    {subfolders.map((s) => (
                      <button
                        key={s.path}
                        type="button"
                        onClick={() => abrirPasta(s.path)}
                        className="rounded-xl border border-gray-200 bg-white p-4 text-left hover:border-purple-300 dark:border-gray-800 dark:bg-gray-900"
                      >
                        <div className="font-medium break-all">{s.name}/</div>
                        <div className="mt-1 text-xs text-gray-500">
                          {s.file_count} arquivo{s.file_count === 1 ? '' : 's'}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
                <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
                  <table className="min-w-full text-sm">
                    <thead className="bg-gray-50 text-left text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                      <tr>
                        <th className="px-4 py-3 font-medium">Arquivo</th>
                        <th className="px-4 py-3 font-medium">Tamanho</th>
                        <th className="px-4 py-3 font-medium">Modificado</th>
                        <th className="px-4 py-3 font-medium">Link</th>
                        <th className="px-4 py-3 font-medium">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {files.map((f) => (
                        <tr key={f.filename} className="border-t border-gray-100 dark:border-gray-800">
                          <td className="px-4 py-3 font-mono text-xs break-all">{f.filename}</td>
                          <td className="px-4 py-3 whitespace-nowrap">{formatBytes(f.size)}</td>
                          <td className="px-4 py-3 whitespace-nowrap">{formatDate(f.mtime)}</td>
                          <td className="px-4 py-3">
                            <a
                              href={f.public_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-purple-700 hover:underline dark:text-purple-300"
                            >
                              Abrir
                            </a>
                          </td>
                          <td className="px-4 py-3">
                            <button
                              type="button"
                              onClick={() => excluirArquivo(f)}
                              className="text-xs text-red-600 hover:text-red-800 hover:underline"
                            >
                              Excluir
                            </button>
                          </td>
                        </tr>
                      ))}
                      {!files.length && !subfolders.length && (
                        <tr>
                          <td colSpan={5} className="px-4 py-6 text-center text-gray-500">
                            Pasta vazia.
                          </td>
                        </tr>
                      )}
                      {!files.length && !!subfolders.length && (
                        <tr>
                          <td colSpan={5} className="px-4 py-4 text-center text-gray-500">
                            Sem arquivos soltos nesta pasta — abra a pasta do paciente acima.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
