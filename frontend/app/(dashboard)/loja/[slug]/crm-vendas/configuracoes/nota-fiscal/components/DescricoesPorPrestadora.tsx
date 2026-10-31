'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { textoVisivelDoTemplate } from '@/lib/crm-proposta-template-legenda';
import { fetchAllPaginatedResults } from '@/lib/crm-utils';

type Prestadora = { id: number; nome: string; razao_social?: string; cnpj?: string };
type Template = {
  id: number;
  nome: string;
  conteudo: string;
  is_padrao: boolean;
  prestadora?: number | null;
};

type Linha = {
  prestadoraId: number;
  nome: string;
  templateId: number | null;
  texto: string;
  textoInicial: string;
};

let salvarAtual: (() => Promise<void>) | null = null;

export function registrarSalvarDescricoesPrestadora(fn: (() => Promise<void>) | null) {
  salvarAtual = fn;
}

export async function salvarDescricoesPrestadoraNfse() {
  if (salvarAtual) await salvarAtual();
}

function nomeEmpresa(conta: Prestadora): string {
  const razao = (conta.razao_social || '').trim();
  const nome = (conta.nome || '').trim();
  const label = razao || nome || `Empresa ${conta.id}`;
  return conta.cnpj ? `${label} — ${conta.cnpj}` : label;
}

export function DescricoesPorPrestadora({ inputClass }: { inputClass: string }) {
  const params = useParams();
  const slug = typeof params?.slug === 'string' ? params.slug : '';
  const [linhas, setLinhas] = useState<Linha[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');

  const salvar = useCallback(async () => {
    const proximas = linhas.map((linha) => ({ ...linha }));
    for (const linha of proximas) {
      const texto = linha.texto.trim();
      if (texto === linha.textoInicial.trim()) continue;
      if (!texto && linha.templateId) {
        await apiClient.delete(`/crm-vendas/nfse-templates/${linha.templateId}/`);
        linha.templateId = null;
        linha.textoInicial = '';
        continue;
      }
      if (!texto) continue;
      if (linha.templateId) {
        await apiClient.patch(`/crm-vendas/nfse-templates/${linha.templateId}/`, {
          conteudo: texto,
          prestadora: linha.prestadoraId,
          is_padrao: true,
          ativo: true,
        });
      } else {
        const criado = await apiClient.post<{ id: number }>('/crm-vendas/nfse-templates/', {
          nome: linha.nome.slice(0, 255),
          conteudo: texto,
          prestadora: linha.prestadoraId,
          is_padrao: true,
          ativo: true,
        });
        linha.templateId = criado.data.id;
      }
      linha.textoInicial = texto;
    }
    setLinhas(proximas);
  }, [linhas]);

  useEffect(() => {
    registrarSalvarDescricoesPrestadora(salvar);
    return () => registrarSalvarDescricoesPrestadora(null);
  }, [salvar]);

  useEffect(() => {
    let cancelado = false;
    void (async () => {
      try {
        const [prestadoras, templates] = await Promise.all([
          fetchAllPaginatedResults<Prestadora>('/crm-vendas/contas/', { tipo: 'prestadora' }),
          fetchAllPaginatedResults<Template>('/crm-vendas/nfse-templates/', { ativo: 'true' }),
        ]);
        if (cancelado) return;
        setLinhas(
          prestadoras.map((conta) => {
            const daEmpresa = templates.filter((t) => t.prestadora === conta.id);
            const escolhido = daEmpresa.find((t) => t.is_padrao) || daEmpresa[0];
            const texto = escolhido ? textoVisivelDoTemplate(escolhido.conteudo) : '';
            return {
              prestadoraId: conta.id,
              nome: nomeEmpresa(conta),
              templateId: escolhido?.id ?? null,
              texto,
              textoInicial: texto,
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
      <p className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        Descrição padrão do serviço
      </p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
        Cada empresa prestadora tem o próprio texto. Ao emitir a nota para essa empresa, a descrição
        usada é a dela.
      </p>
      {carregando && <p className="text-sm text-gray-500">Carregando empresas...</p>}
      {erro && <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>}
      {!carregando && linhas.length === 0 && !erro && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
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
      <div className="space-y-4">
        {linhas.map((linha) => (
          <div key={linha.prestadoraId}>
            <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
              {linha.nome}
            </label>
            <textarea
              value={linha.texto}
              onChange={(e) =>
                setLinhas((atual) =>
                  atual.map((item) =>
                    item.prestadoraId === linha.prestadoraId ? { ...item, texto: e.target.value } : item,
                  ),
                )
              }
              rows={4}
              className={inputClass}
              placeholder="Texto da nota desta empresa"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
