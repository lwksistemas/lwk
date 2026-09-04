'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';

type Pasta = { folder?: string; name?: string; path?: string; file_count?: number; subfolder_count?: number };
type Arquivo = { filename: string; size?: number; public_url: string };

function formatBytes(n?: number) {
  if (!n && n !== 0) return '';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export default function BackupMidiaPage() {
  const params = useParams();
  const token = String(params.token || '');
  const [lojaNome, setLojaNome] = useState('');
  const [folder, setFolder] = useState('');
  const [pastas, setPastas] = useState<Pasta[]>([]);
  const [subpastas, setSubpastas] = useState<Pasta[]>([]);
  const [arquivos, setArquivos] = useState<Arquivo[]>([]);
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(true);

  const apiUrl = useMemo(() => {
    const base = getPrimaryApiBaseUrl();
    const q = folder ? `?folder=${encodeURIComponent(folder)}` : '';
    return `${base}/superadmin/public/backup-midia/${encodeURIComponent(token)}/${q}`;
  }, [token, folder]);

  const carregar = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErro('');
    try {
      const res = await fetch(apiUrl);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setErro(data.error || 'Link inválido ou expirado.');
        setPastas([]);
        setSubpastas([]);
        setArquivos([]);
        return;
      }
      setLojaNome(data.loja_nome || '');
      setPastas(data.folders || []);
      setSubpastas(data.subfolders || []);
      setArquivos(data.files || []);
    } catch {
      setErro('Não foi possível carregar as pastas. Tente de novo.');
    } finally {
      setLoading(false);
    }
  }, [apiUrl, token]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const abrirPasta = (nome: string) => {
    setFolder((atual) => (atual ? `${atual}/${nome}` : nome));
  };

  const voltar = () => {
    if (!folder) return;
    const parts = folder.split('/').filter(Boolean);
    parts.pop();
    setFolder(parts.join('/'));
  };

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-2xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900">Fotos e PDFs da loja</h1>
        <p className="mt-1 text-sm text-slate-600">
          {lojaNome || 'Backup de mídia'} — baixe os arquivos no seu computador. O e-mail já levou o ZIP dos cadastros.
        </p>
        {folder ? (
          <button type="button" onClick={voltar} className="mt-3 text-sm text-emerald-700 hover:underline">
            ← Voltar
          </button>
        ) : null}
        {folder ? <p className="mt-1 font-mono text-xs text-slate-500">{folder}</p> : null}
        {loading ? <p className="mt-6 text-sm text-slate-500">Carregando…</p> : null}
        {erro ? <p className="mt-6 text-sm text-red-600">{erro}</p> : null}
        {!loading && !erro ? (
          <ul className="mt-4 divide-y divide-slate-100">
            {pastas.map((p) => {
              const nome = p.folder || p.name || '';
              return (
                <li key={nome}>
                  <button
                    type="button"
                    onClick={() => abrirPasta(nome)}
                    className="flex w-full items-center justify-between py-3 text-left text-sm hover:bg-slate-50"
                  >
                    <span className="font-medium text-slate-800">{nome}/</span>
                    <span className="text-xs text-slate-500">
                      {p.file_count ?? 0} arquivo(s)
                    </span>
                  </button>
                </li>
              );
            })}
            {subpastas.map((p) => {
              const nome = p.name || '';
              return (
                <li key={p.path || nome}>
                  <button
                    type="button"
                    onClick={() => abrirPasta(nome)}
                    className="flex w-full items-center justify-between py-3 text-left text-sm hover:bg-slate-50"
                  >
                    <span className="font-medium text-slate-800">{nome}/</span>
                    <span className="text-xs text-slate-500">{p.file_count ?? 0} arquivo(s)</span>
                  </button>
                </li>
              );
            })}
            {arquivos.map((f) => (
              <li key={f.filename} className="flex items-center justify-between py-3 text-sm">
                <span className="truncate text-slate-800">{f.filename}</span>
                <span className="ml-3 flex shrink-0 items-center gap-3">
                  <span className="text-xs text-slate-500">{formatBytes(f.size)}</span>
                  <a
                    href={f.public_url}
                    target="_blank"
                    rel="noreferrer"
                    download={f.filename}
                    className="font-medium text-emerald-700 hover:underline"
                  >
                    Baixar
                  </a>
                </span>
              </li>
            ))}
            {!pastas.length && !subpastas.length && !arquivos.length ? (
              <li className="py-6 text-sm text-slate-500">Nenhuma foto ou PDF nesta pasta.</li>
            ) : null}
          </ul>
        ) : null}
      </div>
    </div>
  );
}
