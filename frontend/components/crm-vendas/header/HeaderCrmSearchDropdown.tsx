'use client';

import Link from 'next/link';
import { Building2, DollarSign, FileText, Users } from 'lucide-react';
import { formatCrmBrl } from '@/lib/crm-utils';
import { CRM_HEADER_SEARCH_MIN_LEN, crmHeaderHasSearchResults, type CrmHeaderBuscaResult } from '@/lib/crm-header';

interface Props {
  slug: string;
  searchQuery: string;
  searchResults: CrmHeaderBuscaResult | null;
  searchLoading: boolean;
  showSearchDropdown: boolean;
  onSelect: () => void;
}

export function HeaderCrmSearchDropdown({
  slug,
  searchQuery,
  searchResults,
  searchLoading,
  showSearchDropdown,
  onSelect,
}: Props) {
  if (!showSearchDropdown || searchQuery.length < CRM_HEADER_SEARCH_MIN_LEN) return null;

  const hasResults = crmHeaderHasSearchResults(searchResults);

  return (
    <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-[#16325c] rounded-lg shadow-xl border border-gray-200 dark:border-[#0d1f3c] py-2 z-30 max-h-80 overflow-y-auto">
      {searchLoading ? (
        <div className="px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400">Buscando...</div>
      ) : !hasResults ? (
        <div className="px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400">
          Nenhum resultado encontrado
        </div>
      ) : (
        <div className="space-y-1">
          {searchResults!.leads.length > 0 && (
            <div className="px-3 py-1">
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Leads
              </p>
              {searchResults!.leads.map((l) => (
                <Link
                  key={`lead-${l.id}`}
                  href={slug ? `/loja/${slug}/crm-vendas/leads?ver=${l.id}` : '#'}
                  onClick={onSelect}
                  className="flex items-center gap-2 px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] text-sm text-gray-900 dark:text-white"
                >
                  <Users size={14} className="text-[#06a59a] shrink-0" />
                  <span className="truncate">{l.nome}</span>
                  {l.empresa && (
                    <span className="text-gray-500 dark:text-gray-400 truncate">• {l.empresa}</span>
                  )}
                  {l.cpf_cnpj && (
                    <span className="text-gray-400 dark:text-gray-500 text-xs shrink-0">{l.cpf_cnpj}</span>
                  )}
                </Link>
              ))}
            </div>
          )}
          {searchResults!.oportunidades.length > 0 && (
            <div className="px-3 py-1">
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Oportunidades
              </p>
              {searchResults!.oportunidades.map((o) => (
                <Link
                  key={`opp-${o.id}`}
                  href={slug ? `/loja/${slug}/crm-vendas/pipeline?ver=${o.id}` : '#'}
                  onClick={onSelect}
                  className="flex items-center gap-2 px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] text-sm text-gray-900 dark:text-white"
                >
                  <DollarSign size={14} className="text-[#e287b2] shrink-0" />
                  <span className="truncate">{o.lead_nome || o.titulo}</span>
                  {o.lead_nome && o.titulo && o.titulo !== o.lead_nome && (
                    <span className="text-gray-500 dark:text-gray-400 truncate text-xs">• {o.titulo}</span>
                  )}
                  <span className="text-gray-500 dark:text-gray-400 shrink-0">
                    {formatCrmBrl(o.valor, { maximumFractionDigits: 0 })}
                  </span>
                </Link>
              ))}
            </div>
          )}
          {searchResults!.contas.length > 0 && (
            <div className="px-3 py-1">
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Contas
              </p>
              {searchResults!.contas.map((c) => (
                <Link
                  key={`conta-${c.id}`}
                  href={slug ? `/loja/${slug}/crm-vendas/customers/${c.id}` : '#'}
                  onClick={onSelect}
                  className="flex items-center gap-2 px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] text-sm text-gray-900 dark:text-white"
                >
                  <Building2 size={14} className="text-[#0176d3] shrink-0" />
                  <span className="truncate">{c.nome}</span>
                  {c.cnpj && (
                    <span className="text-gray-400 dark:text-gray-500 text-xs shrink-0">{c.cnpj}</span>
                  )}
                  {!c.cnpj && c.segmento && (
                    <span className="text-gray-500 dark:text-gray-400 truncate">• {c.segmento}</span>
                  )}
                </Link>
              ))}
            </div>
          )}
          {(searchResults!.propostas?.length ?? 0) > 0 && (
            <div className="px-3 py-1">
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Propostas
              </p>
              {searchResults!.propostas!.map((p) => (
                <Link
                  key={`prop-${p.id}`}
                  href={slug ? `/loja/${slug}/crm-vendas/propostas` : '#'}
                  onClick={onSelect}
                  className="flex items-center gap-2 px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] text-sm text-gray-900 dark:text-white"
                >
                  <FileText size={14} className="text-[#fe9339] shrink-0" />
                  <span className="truncate">{p.titulo}</span>
                  {p.lead_nome && (
                    <span className="text-gray-500 dark:text-gray-400 truncate">• {p.lead_nome}</span>
                  )}
                  {p.numero && (
                    <span className="text-gray-400 dark:text-gray-500 text-xs shrink-0">#{p.numero}</span>
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
