'use client';

import { Building2, Briefcase, Mail, Phone, FileText } from 'lucide-react';
import { formatTelefone } from '@/lib/format-br';
import { formatDate } from '@/lib/financeiro-helpers';
import type { CrmContato } from '@/hooks/crm-vendas/useCrmContatosPage';

interface Props {
  contato: CrmContato;
}

export function ContatoDetailView({ contato }: Props) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 pb-6 border-b border-gray-200 dark:border-gray-700">
        <div className="w-14 h-14 rounded-full bg-gradient-to-br from-[#06a59a] to-[#0d9dda] flex items-center justify-center text-white font-bold text-xl shrink-0">
          {contato.nome.charAt(0).toUpperCase()}
        </div>
        <div className="min-w-0">
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white truncate">{contato.nome}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">{contato.cargo || 'Sem cargo definido'}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-5">
        <InfoItem icon={<Building2 size={18} />} label="Conta" value={contato.conta_nome} />
        <InfoItem icon={<Briefcase size={18} />} label="Cargo" value={contato.cargo} />
        <InfoItem icon={<Mail size={18} />} label="E-mail" value={contato.email} />
        <InfoItem
          icon={<Phone size={18} />}
          label="Telefone"
          value={contato.telefone ? formatTelefone(contato.telefone) : undefined}
        />
        <InfoItem icon={<FileText size={18} />} label="Cadastrado em" value={formatDate(contato.created_at)} />
      </div>

      {contato.observacoes && (
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Observações</p>
          <p className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">{contato.observacoes}</p>
        </div>
      )}
    </div>
  );
}

function InfoItem({ icon, label, value }: { icon: React.ReactNode; label: string; value?: string }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-3 min-w-0">
      <span className="text-gray-400 mt-0.5 shrink-0">{icon}</span>
      <div className="min-w-0">
        <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
        <p className="text-sm text-gray-900 dark:text-white break-words">{value}</p>
      </div>
    </div>
  );
}
