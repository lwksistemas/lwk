'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ChevronDown } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { fetchAllPaginatedResults } from '@/lib/crm-utils';
import { NFSE_ATIVIDADES_MUNICIPAIS } from '@/lib/nfse-atividades-municipais';

type Prestadora = {
  id: number;
  nome: string;
  razao_social?: string;
  cnpj?: string;
  nfse_atividade_padrao?: string;
};

type Linha = {
  prestadoraId: number;
  nome: string;
  atividadeId: string;
  atividadeInicial: string;
};

const ATIVIDADES = NFSE_ATIVIDADES_MUNICIPAIS.filter((a) => a.id !== 'loja');

let salvarAtual: (() => Promise<void>) | null = null;

export function registrarSalvarAtividadesPrestadora(fn: (() => Promise<void>) | null) {
  salvarAtual = fn;
}

export async function salvarAtividadesPrestadoraNfse() {
  if (salvarAtual) await salvarAtual();
}

function nomeEmpresa(conta: Prestadora): string {
  const razao = (conta.razao_social || '').trim();
  const nome = (conta.nome || '').trim();
  const label = razao || nome || `Empresa ${conta.id}`;
  return conta.cnpj ? `${label} — ${conta.cnpj}` : label;
}

export function AtividadesPorPrestadora({ inputClass }: { inputClass: string }) {
  const params = useParams();
  const slug = typeof params?.slug === 'string' ? params.slug : '';
  const [linhas, setLinhas] = useState<Linha[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [aberto, setAberto] = useState(false);

  const salvar = useCallback(async () => {
    for (const linha of linhas) {
      if (linha.atividadeId === linha.atividadeInicial) continue;
      await apiClient.patch(`/crm-vendas/contas/${linha.prestadoraId}/`, {
        nfse_atividade_padrao: linha.atividadeId,
      });
    }
    setLinhas((atual) => atual.map((linha) => ({ ...linha, atividadeInicial: linha.atividadeId })));
  }, [linhas]);

  useEffect(() => {
    registrarSalvarAtividadesPrestadora(salvar);
    return () => registrarSalvarAtividadesPrestadora(null);
  }, [salvar]);

  useEffect(() => {
    let cancelado = false;
    void (async () => {
      try {
        const prestadoras = await fetchAllPaginatedResults<Prestadora>('/crm-vendas/contas/', {
          tipo: 'prestadora',
        });
        if (cancelado) return;
        setLinhas(
          prestadoras.map((conta) => {
            const atividadeId = ATIVIDADES.some((a) => a.id === conta.nfse_atividade_padrao)
              ? conta.nfse_atividade_padrao || ''
              : '';
            return {
              prestadoraId: conta.id,
              nome: nomeEmpresa(conta),
              atividadeId,
              atividadeInicial: atividadeId,
            };
          }),
        );
      } catch {
        if (!cancelado) setErro('Não foi possível carregar as empresas prestadoras.');
      } finally {
        if (!cancelado) setCarregando(false);
      }
    })();
    return () => {
      cancelado = true;
    };
  }, []);

  return (
    <div className="md:col-span-2">
      <button
        type="button"
        onClick={() => setAberto((atual) => !atual)}
        aria-expanded={aberto}
        className="flex w-full items-center justify-between gap-3 rounded-lg border border-gray-200 dark:border-gray-600 px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-[#0d1f3c]"
      >
        <span>
          <span className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Atividade municipal padrão
          </span>
          <span className="mt-0.5 block text-xs text-gray-500 dark:text-gray-400">
            Cada empresa prestadora tem a própria atividade. Abra para configurar.
          </span>
        </span>
        <ChevronDown
          size={18}
          className={`shrink-0 text-gray-500 transition-transform ${aberto ? 'rotate-180' : ''}`}
        />
      </button>
      {aberto && (
        <div className="mt-3 space-y-4">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Ao emitir a nota dessa empresa, a atividade municipal já vem escolhida.
          </p>
          {carregando && <p className="text-sm text-gray-500">Carregando empresas...</p>}
          {erro && <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>}
          {!carregando && linhas.length === 0 && !erro && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Nenhuma empresa prestadora cadastrada.{' '}
              {slug ? (
                <Link href={`/loja/${slug}/crm-vendas/customers`} className="text-[#0176d3] underline">
                  Cadastre em Contas
                </Link>
              ) : (
                'Cadastre em Contas'
              )}{' '}
              com o tipo Prestadora.
            </p>
          )}
          {linhas.map((linha) => (
            <div key={linha.prestadoraId}>
              <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                {linha.nome}
              </label>
              <select
                value={linha.atividadeId}
                onChange={(e) =>
                  setLinhas((atual) =>
                    atual.map((item) =>
                      item.prestadoraId === linha.prestadoraId
                        ? { ...item, atividadeId: e.target.value }
                        : item,
                    ),
                  )
                }
                className={inputClass}
              >
                <option value="">Usar configuração padrão da loja</option>
                {ATIVIDADES.map((atividade) => (
                  <option key={atividade.id} value={atividade.id}>
                    {atividade.label}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
