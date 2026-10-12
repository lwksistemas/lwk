/**
 * Tabela de assinaturas do superadmin: loja, plano, vencimento, dia e nota fiscal.
 */
import { Fragment, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { formatApiErrorBody } from '@/lib/api-errors';
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers';
import type { Assinatura, Pagamento } from '@/hooks/useAssinaturas';
import { AssinaturaCard } from './AssinaturaCard';

interface PlanoOption {
  id: number;
  nome: string;
  preco_mensal: string | number;
  is_active: boolean;
  tipos_loja: number[];
}

interface AssinaturasTabelaProps {
  assinaturas: Assinatura[];
  onAtualizar: () => void;
  onDownloadBoletoAsaas: (payment: Pagamento) => void;
  onCopyPixAsaas: (pixCode: string) => void;
  onUpdateStatusAsaas: (paymentId: number) => void;
  onNovaCobranca: (assinatura: Assinatura) => void;
  onExcluirAsaas: (payment: Pagamento) => void;
  gerandoCobranca: number | null;
  onDownloadBoletoMP: (payment: Pagamento) => void;
  onCopyPixMP: (pixCode: string) => void;
  onGerarPixMP: (payment: Pagamento) => void;
  onUpdateStatusMP: (lojaSlug: string) => void;
  onNovaCobrancaMP: (assinatura: Assinatura) => void;
  onExcluirMP: (payment: Pagamento) => void;
  gerandoPix: number | null;
  atualizandoMP: string | null;
  gerandoCobrancaMP: string | number | null;
  excluindoPagamentoMP: boolean;
}

const COLUNAS = [
  'Loja',
  'Assinatura',
  'Vencimento',
  'Alterar plano',
  'Dia de vencimento',
  'Conta da empresa',
  'Nota fiscal',
];

function mensagemErro(error: unknown, fallback: string) {
  return formatApiErrorBody(error) || fallback;
}

export function AssinaturasTabela(props: AssinaturasTabelaProps) {
  const { assinaturas, onAtualizar } = props;
  const [planos, setPlanos] = useState<PlanoOption[]>([]);
  const [aberta, setAberta] = useState<number | string | null>(null);
  const [planoEditando, setPlanoEditando] = useState<number | string | null>(null);
  const [planoEscolhido, setPlanoEscolhido] = useState<Record<string, string>>({});
  const [dias, setDias] = useState<Record<string, string>>({});
  const [proxima, setProxima] = useState<Record<string, string>>({});
  const [ocupado, setOcupado] = useState<string | null>(null);

  useEffect(() => {
    apiClient.get('/superadmin/planos/')
      .then((res) => {
        const data = res.data?.results || res.data;
        setPlanos(Array.isArray(data) ? data : []);
      })
      .catch(() => setPlanos([]));
  }, []);

  useEffect(() => {
    const iniciais: Record<string, string> = {};
    assinaturas.forEach((a) => {
      if (a.dia_vencimento) iniciais[String(a.id)] = String(a.dia_vencimento);
    });
    setDias((atual) => ({ ...iniciais, ...atual }));
  }, [assinaturas]);

  const planosDaLoja = (assinatura: Assinatura) => planos.filter((plano) => {
    if (!plano.is_active) return false;
    if (!assinatura.tipo_loja_id) return true;
    return plano.tipos_loja.includes(assinatura.tipo_loja_id);
  });

  const salvarPlano = async (assinatura: Assinatura) => {
    const planoId = planoEscolhido[String(assinatura.id)];
    if (!assinatura.financeiro_id || !planoId) return;
    const plano = planos.find((item) => String(item.id) === planoId);
    const confirma = window.confirm(
      `Alterar o plano de ${assinatura.loja_nome} para ${plano?.nome || 'o plano escolhido'}? A próxima cobrança usa esse valor.`,
    );
    if (!confirma) return;
    const chave = `plano-${assinatura.id}`;
    setOcupado(chave);
    try {
      await apiClient.post(`/superadmin/financeiro/${assinatura.financeiro_id}/alterar_plano/`, {
        plano_id: Number(planoId),
      });
      setPlanoEditando(null);
      onAtualizar();
    } catch (error) {
      window.alert(mensagemErro(error, 'Não foi possível alterar o plano.'));
    } finally {
      setOcupado(null);
    }
  };

  const salvarDia = async (assinatura: Assinatura) => {
    const dia = Number(dias[String(assinatura.id)]);
    if (!assinatura.financeiro_id || !Number.isInteger(dia)) return;
    const confirma = window.confirm(
      `O vencimento de ${assinatura.loja_nome} passa a ser todo dia ${dia}. Vale para a próxima cobrança.`,
    );
    if (!confirma) return;
    const chave = `dia-${assinatura.id}`;
    setOcupado(chave);
    try {
      const res = await apiClient.post(
        `/superadmin/financeiro/${assinatura.financeiro_id}/alterar_dia_vencimento/`,
        { dia_vencimento: dia },
      );
      if (res.data?.data_proxima_cobranca) {
        setProxima((atual) => ({ ...atual, [String(assinatura.id)]: res.data.data_proxima_cobranca }));
      }
      onAtualizar();
    } catch (error) {
      window.alert(mensagemErro(error, 'Não foi possível alterar o dia de vencimento.'));
    } finally {
      setOcupado(null);
    }
  };

  const confirmarConta = async (assinatura: Assinatura, forma: 'pix' | 'transferencia') => {
    if (!assinatura.financeiro_id) return;
    const meio = forma === 'pix' ? 'PIX' : 'transferência';
    const confirma = window.confirm(
      `Confirmar que ${assinatura.loja_nome} pagou por ${meio} na conta da empresa? O boleto Asaas em aberto recebe baixa e a assinatura é atualizada.`,
    );
    if (!confirma) return;
    const chave = `conta-${forma}-${assinatura.id}`;
    setOcupado(chave);
    try {
      const res = await apiClient.post(
        `/superadmin/financeiro/${assinatura.financeiro_id}/confirmar_pagamento_conta/`,
        { forma },
      );
      window.alert(res.data?.message || 'Pagamento confirmado.');
      onAtualizar();
    } catch (error) {
      window.alert(mensagemErro(error, 'Não foi possível confirmar o pagamento.'));
    } finally {
      setOcupado(null);
    }
  };

  const baixarNota = async (assinatura: Assinatura) => {
    if (!assinatura.financeiro_id) return;
    const chave = `nf-${assinatura.id}`;
    setOcupado(chave);
    try {
      const res = await apiClient.get(`/superadmin/financeiro/${assinatura.financeiro_id}/baixar_nota_fiscal/`);
      const url = res.data?.pdf_url;
      if (url) window.open(url, '_blank', 'noopener,noreferrer');
    } catch (error) {
      window.alert(mensagemErro(error, 'Nota fiscal ainda não disponível.'));
    } finally {
      setOcupado(null);
    }
  };

  const reenviarNota = async (assinatura: Assinatura) => {
    if (!assinatura.financeiro_id) return;
    const confirma = window.confirm(`Reenviar a nota fiscal de ${assinatura.loja_nome} para o e-mail do responsável?`);
    if (!confirma) return;
    const chave = `mail-${assinatura.id}`;
    setOcupado(chave);
    try {
      const res = await apiClient.post(`/superadmin/financeiro/${assinatura.financeiro_id}/reenviar_nota_fiscal/`);
      window.alert(res.data?.message || 'Nota fiscal reenviada.');
    } catch (error) {
      window.alert(mensagemErro(error, 'Não foi possível reenviar a nota fiscal.'));
    } finally {
      setOcupado(null);
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            {COLUNAS.map((coluna) => (
              <th
                key={coluna}
                className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
              >
                {coluna}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {assinaturas.map((assinatura) => {
            const chave = String(assinatura.id);
            const abertaLinha = aberta === assinatura.id;
            const editando = planoEditando === assinatura.id;
            const semFinanceiro = !assinatura.financeiro_id;
            const vencimento = assinatura.data_vencimento || assinatura.current_payment_data?.due_date;
            const cobrancaAberta = Boolean(
              assinatura.current_payment_data && !assinatura.current_payment_data.is_paid,
            );
            return (
              <Fragment key={chave}>
                <tr className="align-top hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-3 py-3">
                    <button
                      type="button"
                      onClick={() => setAberta(abertaLinha ? null : assinatura.id)}
                      className="text-left"
                    >
                      <div className="font-medium text-gray-900 dark:text-gray-100">{assinatura.loja_nome}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{assinatura.loja_slug}</div>
                    </button>
                    <span className={`mt-1 inline-block px-2 py-0.5 text-xs rounded-full ${
                      assinatura.ativa
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}>
                      {assinatura.subscription_status_display || (assinatura.ativa ? 'Ativa' : 'Inativa')}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-900 dark:text-gray-100">
                    <div>{assinatura.plano_nome}</div>
                    <div className="text-gray-500 dark:text-gray-400">{formatCurrency(assinatura.plano_valor)}</div>
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-900 dark:text-gray-100 whitespace-nowrap">
                    {formatDate(vencimento)}
                    {cobrancaAberta && (
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {assinatura.current_payment_data?.status_display}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    {editando ? (
                      <div className="flex flex-col gap-1 min-w-[10rem]">
                        <select
                          value={planoEscolhido[chave] || String(assinatura.plano_id || '')}
                          onChange={(e) => setPlanoEscolhido((atual) => ({ ...atual, [chave]: e.target.value }))}
                          className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                        >
                          <option value="">Selecione</option>
                          {planosDaLoja(assinatura).map((plano) => (
                            <option key={plano.id} value={plano.id}>
                              {plano.nome} — {formatCurrency(plano.preco_mensal)}
                            </option>
                          ))}
                        </select>
                        <div className="flex gap-1">
                          <button
                            type="button"
                            disabled={ocupado === `plano-${assinatura.id}` || semFinanceiro}
                            onClick={() => salvarPlano(assinatura)}
                            className="px-2 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                          >
                            Salvar
                          </button>
                          <button
                            type="button"
                            onClick={() => setPlanoEditando(null)}
                            className="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-200"
                          >
                            Cancelar
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        type="button"
                        disabled={semFinanceiro}
                        onClick={() => {
                          setPlanoEditando(assinatura.id);
                          setPlanoEscolhido((atual) => ({
                            ...atual,
                            [chave]: String(assinatura.plano_id || ''),
                          }));
                        }}
                        className="px-2 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                      >
                        Alterar plano
                      </button>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-1">
                      <input
                        type="number"
                        min={1}
                        max={28}
                        value={dias[chave] ?? ''}
                        disabled={semFinanceiro}
                        onChange={(e) => setDias((atual) => ({ ...atual, [chave]: e.target.value }))}
                        className="w-16 text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                      />
                      <button
                        type="button"
                        disabled={ocupado === `dia-${assinatura.id}` || semFinanceiro}
                        onClick={() => salvarDia(assinatura)}
                        className="px-2 py-1 text-xs bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-900 rounded disabled:opacity-50"
                      >
                        Salvar
                      </button>
                    </div>
                    {proxima[chave] && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Próxima: {formatDate(proxima[chave])}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    {typeof assinatura.id === 'number' ? (
                      <div className="flex flex-wrap gap-1">
                        <button
                          type="button"
                          disabled={semFinanceiro || ocupado === `conta-pix-${assinatura.id}`}
                          onClick={() => confirmarConta(assinatura, 'pix')}
                          className="px-2 py-1 text-xs bg-teal-700 text-white rounded hover:bg-teal-800 disabled:opacity-50"
                        >
                          PIX
                        </button>
                        <button
                          type="button"
                          disabled={semFinanceiro || ocupado === `conta-transferencia-${assinatura.id}`}
                          onClick={() => confirmarConta(assinatura, 'transferencia')}
                          className="px-2 py-1 text-xs bg-teal-700 text-white rounded hover:bg-teal-800 disabled:opacity-50"
                        >
                          Transferência
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap gap-1">
                      <button
                        type="button"
                        disabled={semFinanceiro || ocupado === `nf-${assinatura.id}`}
                        onClick={() => baixarNota(assinatura)}
                        className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                      >
                        Baixar
                      </button>
                      <button
                        type="button"
                        disabled={semFinanceiro || ocupado === `mail-${assinatura.id}`}
                        onClick={() => reenviarNota(assinatura)}
                        className="px-2 py-1 text-xs bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50"
                      >
                        Reenviar
                      </button>
                    </div>
                  </td>
                </tr>
                {abertaLinha && (
                  <tr key={`${chave}-detalhe`} className="bg-gray-50 dark:bg-gray-800/60">
                    <td colSpan={COLUNAS.length} className="px-3 py-3">
                      <AssinaturaCard
                        assinatura={assinatura}
                        somenteDetalhe
                        onDownloadBoletoAsaas={props.onDownloadBoletoAsaas}
                        onCopyPixAsaas={props.onCopyPixAsaas}
                        onUpdateStatusAsaas={props.onUpdateStatusAsaas}
                        onNovaCobranca={props.onNovaCobranca}
                        onExcluirAsaas={props.onExcluirAsaas}
                        gerandoCobranca={props.gerandoCobranca}
                        onDownloadBoletoMP={props.onDownloadBoletoMP}
                        onCopyPixMP={props.onCopyPixMP}
                        onGerarPixMP={props.onGerarPixMP}
                        onUpdateStatusMP={props.onUpdateStatusMP}
                        onNovaCobrancaMP={props.onNovaCobrancaMP}
                        onExcluirMP={props.onExcluirMP}
                        gerandoPix={props.gerandoPix}
                        atualizandoMP={props.atualizandoMP}
                        gerandoCobrancaMP={props.gerandoCobrancaMP}
                        excluindoPagamentoMP={props.excluindoPagamentoMP}
                      />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
