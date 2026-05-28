'use client';

import { PlusCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function NfseSuperadminHeader({
  total,
  loading,
  onEmitir,
  onAtualizar,
}: {
  total: number;
  loading: boolean;
  onEmitir: () => void;
  onAtualizar: () => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <a
          href="/superadmin/dashboard"
          className="flex items-center text-muted-foreground hover:text-foreground transition-colors"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m12 19-7-7 7-7" />
            <path d="M19 12H5" />
          </svg>
        </a>
        <div>
          <h1 className="text-3xl font-bold">NFS-e Emitidas</h1>
          <p className="text-muted-foreground">Notas fiscais emitidas pela LWK para as lojas ({total} notas)</p>
        </div>
      </div>
      <div className="flex gap-2">
        <Button onClick={onEmitir}>
          <PlusCircle className="w-4 h-4 mr-2" />
          Emitir NFS-e
        </Button>
        <Button variant="outline" onClick={onAtualizar} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Atualizar
        </Button>
      </div>
    </div>
  );
}
