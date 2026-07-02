'use client';

import {
  Building2,
  Mail,
  Phone,
  MapPin,
  Tag,
  Globe,
  FileText,
  Hash,
} from 'lucide-react';
import { formatCpfCnpj, formatTelefone } from '@/lib/format-br';
import { formatDate } from '@/lib/financeiro-helpers';
import type { CrmConta } from '@/hooks/crm-vendas/useCrmCustomersPage';

const TIPO_LABELS: Record<string, string> = {
  cliente: 'Cliente',
  prestadora: 'Prestadora de Serviço',
  ambos: 'Cliente e Prestadora',
};

interface Props {
  conta: CrmConta;
}

export function ContaDetailView({ conta }: Props) {
  const endereco = [
    conta.logradouro,
    conta.numero,
    conta.complemento,
    conta.bairro,
    conta.cidade,
    conta.uf,
    conta.cep,
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 pb-6 border-b border-gray-200 dark:border-gray-700">
        <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-[#0176d3] to-[#0d9dda] flex items-center justify-center text-white font-bold text-xl shrink-0">
          {conta.nome.charAt(0).toUpperCase()}
        </div>
        <div className="min-w-0">
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white truncate">{conta.nome}</h1>
          {conta.razao_social && conta.razao_social !== conta.nome && (
            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{conta.razao_social}</p>
          )}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                conta.tipo === 'prestadora'
                  ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                  : conta.tipo === 'ambos'
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                    : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
              }`}
            >
              {TIPO_LABELS[conta.tipo] || conta.tipo}
            </span>
            {conta.segmento && (
              <span className="text-xs text-gray-500 dark:text-gray-400">{conta.segmento}</span>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-5">
        <InfoItem icon={<Hash size={18} />} label="CNPJ" value={conta.cnpj ? formatCpfCnpj(conta.cnpj) : undefined} />
        <InfoItem icon={<FileText size={18} />} label="Inscrição estadual" value={conta.inscricao_estadual} />
        <InfoItem icon={<Mail size={18} />} label="E-mail" value={conta.email} />
        <InfoItem
          icon={<Phone size={18} />}
          label="Telefone"
          value={conta.telefone ? formatTelefone(conta.telefone) : undefined}
        />
        <InfoItem icon={<Globe size={18} />} label="Site" value={conta.site} />
        <InfoItem icon={<Tag size={18} />} label="Segmento" value={conta.segmento} />
        <InfoItem icon={<Building2 size={18} />} label="Tipo" value={TIPO_LABELS[conta.tipo] || conta.tipo} />
        <InfoItem icon={<MapPin size={18} />} label="Endereço" value={endereco || undefined} />
        <InfoItem icon={<FileText size={18} />} label="Cadastrado em" value={formatDate(conta.created_at)} />
      </div>

      {conta.observacoes && (
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Observações</p>
          <p className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">{conta.observacoes}</p>
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
