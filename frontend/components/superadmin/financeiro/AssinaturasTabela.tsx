/**
 * Tabela de assinaturas do superadmin: loja, plano, vencimento, dia e nota fiscal.
 */
import { Fragment, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { downloadBlobFile } from '@/lib/download-blob';
import { openPdfFromApiBlobResponse } from '@/lib/nfse-helpers';
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
  onHistoricoAberto?: (loja: { slug: string; nome: string } | null) => void;
  fecharHistorico?: number;
}

interface ItemHistorico {
  id: number | string;
  mes: string;
  valor: string;
  vencimento: string | null;
  pago_em: string | null;
  situacao: string;
  situacao_display: string;
  numero_nf: string;
  nfse_id?: number | null;
  nf_pdf_url: string;
  nf_status: string;
  comprovante_url?: string;
  provedor_boleto?: string;
  provedor_display?: string;
}

const BANCOS_ASSINATURA = [
  { id: 'asaas', nome: 'Asaas' },
  { id: 'mercadopago', nome: 'Mercado Pago' },
  { id: 'cora', nome: 'Cora' },
];

const COR_SITUACAO: Record<string, string> = {
  pago: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  vencido: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  a_vencer: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
};

const COLUNAS = [
  'Loja',
  'Assinatura',
  'Vencimento',
  'Alterar plano',
  'Dia de vencimento',
  'Localizar pagamento',
  'Boleto',
  'Histórico',
];

function mensagemErro(error: unknown, fallback: string) {
  return formatApiErrorBody(error) || fallback;
}

function corVencimento(bloqueada: boolean | undefined, vencimento?: string) {
  if (bloqueada) {
    return 'text-gray-400 dark:text-gray-500';
  }
  if (!vencimento) {
    return 'text-gray-900 dark:text-gray-100';
  }
  const parte = vencimento.slice(0, 10).split('-');
  const ano = Number(parte[0]);
  const mes = Number(parte[1]);
  const dia = Number(parte[2]);
  if (!ano || !mes || !dia) {
    return 'text-gray-900 dark:text-gray-100';
  }
  const prazo = new Date(ano, mes - 1, dia);
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const dias = Math.round((prazo.getTime() - hoje.getTime()) / 86400000);
  if (dias < 0) {
    return 'font-semibold text-red-600 dark:text-red-400';
  }
  if (dias <= 5) {
    return 'font-semibold text-amber-600 dark:text-amber-400';
  }
  return 'text-gray-900 dark:text-gray-100';
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
  const [historicoAberto, setHistoricoAberto] = useState<number | string | null>(null);
  const [historicos, setHistoricos] = useState<Record<string, ItemHistorico[]>>({});
  const [historicoErro, setHistoricoErro] = useState<Record<string, string>>({});
  const [bancosAssinatura, setBancosAssinatura] = useState<Record<string, string>>({});
  const [assinaturasCanceladas, setAssinaturasCanceladas] = useState<Record<string, boolean>>({});
  const [degustacoes, setDegustacoes] = useState<Record<string, {
    em_degustacao: boolean;
    degustacao_ate: string | null;
    dias_apos_pagamento: number | null;
    boleto_em_aberto: boolean;
  }>>({});
  const [conta, setConta] = useState<Assinatura | null>(null);
  const [comprovante, setComprovante] = useState<File | null>(null);

  useEffect(() => {
    apiClient.get('/superadmin/planos/')
      .then((res) => {
        const data = res.data?.results || res.data;
        setPlanos(Array.isArray(data) ? data : []);
      })
      .catch(() => setPlanos([]));
  }, []);

  useEffect(() => {
    if (!props.fecharHistorico) return;
    setHistoricoAberto(null);
    props.onHistoricoAberto?.(null);
  }, [props.fecharHistorico]);

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

  const confirmarConta = async () => {
    if (!conta?.financeiro_id) return;
    if (!comprovante) {
      window.alert('Envie o comprovante em PDF ou uma foto.');
      return;
    }
    const assinatura = conta;
    const chave = `conta-${assinatura.id}`;
    setOcupado(chave);
    try {
      const dados = new FormData();
      dados.append('comprovante', comprovante);
      const res = await apiClient.post(
        `/superadmin/financeiro/${assinatura.financeiro_id}/confirmar_pagamento_conta/`,
        dados,
      );
      window.alert(res.data?.message || 'Pagamento confirmado.');
      setConta(null);
      setComprovante(null);
      onAtualizar();
    } catch (error) {
      window.alert(mensagemErro(error, 'Não foi possível confirmar o pagamento.'));
    } finally {
      setOcupado(null);
    }
  };

  const carregarHistorico = async (assinatura: Assinatura) => {
    if (!assinatura.financeiro_id) return;
    const chave = `historico-${assinatura.id}`;
    setOcupado(chave);
    try {
      const res = await apiClient.get(`/superadmin/financeiro/${assinatura.financeiro_id}/historico_loja/`);
      setHistoricos((atual) => ({ ...atual, [String(assinatura.id)]: res.data?.itens || [] }));
      setBancosAssinatura((atual) => ({
        ...atual,
        [String(assinatura.id)]: res.data?.provedor_boleto || 'asaas',
      }));
      setAssinaturasCanceladas((atual) => ({
        ...atual,
        [String(assinatura.id)]: Boolean(res.data?.assinatura_cancelada),
      }));
      setDegustacoes((atual) => ({
        ...atual,
        [String(assinatura.id)]: {
          em_degustacao: Boolean(res.data?.em_degustacao),
          degustacao_ate: res.data?.degustacao_ate || null,
          dias_apos_pagamento: res.data?.dias_apos_pagamento ?? null,
          boleto_em_aberto: Boolean(res.data?.boleto_em_aberto),
        },
      }));
      setHistoricoErro((atual) => ({ ...atual, [String(assinatura.id)]: '' }));
    } catch (error) {
      setHistoricoErro((atual) => ({
        ...atual,
        [String(assinatura.id)]: mensagemErro(error, 'Não foi possível carregar o histórico.'),
      }));
    } finally {
      setOcupado(null);
    }
  };

  const abrirHistorico = async (assinatura: Assinatura) => {
    setHistoricoAberto(assinatura.id);
    props.onHistoricoAberto?.({ slug: assinatura.loja_slug, nome: assinatura.loja_nome });
    if (!assinatura.financeiro_id || historicos[String(assinatura.id)]) return;
    await carregarHistorico(assinatura);
  };

  const baixarNotaDoMes = async (item: ItemHistorico) => {
    if (!item.nfse_id) return;
    setOcupado(`nf-hist-${item.nfse_id}`);
    try {
      const res = await apiClient.get(`/superadmin/nfse-emitidas/${item.nfse_id}/pdf/`, {
        responseType: 'blob',
      });
      await openPdfFromApiBlobResponse(res);
    } catch (error) {
      window.alert(mensagemErro(error, 'Nota fiscal ainda não disponível.'));
    } finally {
      setOcupado(null);
    }
  };

  const reenviarNotaDoMes = async (item: ItemHistorico, nome: string) => {
    if (!item.nfse_id) return;
    const rotulo = item.numero_nf ? `a NF ${item.numero_nf}` : 'a nota fiscal';
    const confirma = window.confirm(`Reenviar ${rotulo} de ${nome} para o e-mail do responsável?`);
    if (!confirma) return;
    setOcupado(`mail-hist-${item.nfse_id}`);
    try {
      const res = await apiClient.post(`/superadmin/nfse-emitidas/${item.nfse_id}/reenviar/`);
      window.alert(res.data?.message || 'Nota fiscal reenviada.');
    } catch (error) {
      window.alert(mensagemErro(error, 'Não foi possível reenviar a nota fiscal.'));
    } finally {
      setOcupado(null);
    }
  };

  const trocarBanco = async (assinatura: Assinatura, provedor: string) => {
    if (!assinatura.financeiro_id) return;
    const nomeBanco = BANCOS_ASSINATURA.find((banco) => banco.id === provedor)?.nome || provedor;
    const confirma = window.confirm(
      `Trocar o banco de ${assinatura.loja_nome} para ${nomeBanco}?\n\nSe o boleto deste mês ainda não foi gerado, ele será emitido agora. Se já existir, a troca vale no próximo mês.`,
    );
    if (!confirma) return;
    setOcupado(`banco-${assinatura.id}`);
    try {
      const res = await apiClient.post(
        `/superadmin/financeiro/${assinatura.financeiro_id}/trocar_banco/`,
        { provedor },
      );
      window.alert(res.data?.message || 'Banco da assinatura atualizado.');
      setBancosAssinatura((atual) => ({ ...atual, [String(assinatura.id)]: provedor }));
      await carregarHistorico(assinatura);
      onAtualizar();
    } catch (error) {
      window.alert(mensagemErro(error, 'Não foi possível trocar o banco.'));
      setOcupado(null);
    }
  };

  const iniciarDegustacao = async (assinatura: Assinatura, dias: number) => {
    if (!assinatura.financeiro_id) return;
    const confirma = window.confirm(
      `Abrir ${dias} dias de demonstração para ${assinatura.loja_nome}?\n\nSe não houver boleto, o prazo começa agora e nenhum boleto é gerado. Se já houver boleto, ele continua valendo e a demonstração só começa depois do pagamento.`,
    );
    if (!confirma) return;
    setOcupado(`degustacao-${assinatura.id}`);
    try {
      const res = await apiClient.post(
        `/superadmin/financeiro/${assinatura.financeiro_id}/iniciar_degustacao/`,
        { dias },
      );
      window.alert(res.data?.message || 'Demonstração configurada.');
      setDegustacoes((atual) => ({
        ...atual,
        [String(assinatura.id)]: {
          em_degustacao: Boolean(res.data?.em_degustacao),
          degustacao_ate: res.data?.degustacao_ate || null,
          dias_apos_pagamento: res.data?.dias_apos_pagamento ?? null,
          boleto_em_aberto: Boolean(res.data?.aguardando_pagamento),
        },
      }));
      await carregarHistorico(assinatura);
      onAtualizar();
    } catch (error) {
      window.alert(mensagemErro(error, 'Não foi possível abrir a demonstração.'));
      setOcupado(null);
    }
  };

  const alterarAssinatura = async (assinatura: Assinatura, acao: 'cancelar' | 'reativar') => {
    if (!assinatura.financeiro_id) return;
    const confirma = window.confirm(
      acao === 'cancelar'
        ? `Cancelar a assinatura de ${assinatura.loja_nome}?\n\nO sistema para de emitir boletos e bloqueia o acesso. Cadastros, fotos, notas e pagamentos não são apagados. Para voltar, use Reativar: o boleto é gerado e o acesso volta depois do pagamento.`
        : `Reativar a assinatura de ${assinatura.loja_nome}?\n\nSe não houver boleto em aberto, um boleto será emitido agora. O acesso volta depois que o cliente pagar.`,
    );
    if (!confirma) return;
    setOcupado(`assinatura-${assinatura.id}`);
    try {
      const caminho = acao === 'cancelar' ? 'cancelar_assinatura' : 'reativar_assinatura';
      const res = await apiClient.post(
        `/superadmin/financeiro/${assinatura.financeiro_id}/${caminho}/`,
      );
      window.alert(res.data?.message || (acao === 'cancelar' ? 'Assinatura cancelada.' : 'Assinatura reativada.'));
      setAssinaturasCanceladas((atual) => ({
        ...atual,
        [String(assinatura.id)]: Boolean(res.data?.assinatura_cancelada),
      }));
      if (res.data?.boleto_url) window.open(res.data.boleto_url, '_blank', 'noopener,noreferrer');
      await carregarHistorico(assinatura);
      onAtualizar();
    } catch (error) {
      window.alert(mensagemErro(error, acao === 'cancelar'
        ? 'Não foi possível cancelar a assinatura.'
        : 'Não foi possível reativar a assinatura.'));
      setOcupado(null);
    }
  };

  const nomeArquivoBoleto = (assinatura: Assinatura) => {
    const documento = (assinatura.cpf_cnpj || assinatura.loja_slug || '').replace(/\D/g, '') || 'sem-documento';
    const vencimento = assinatura.current_payment_data?.due_date || assinatura.data_vencimento || '';
    const partes = /^(\d{4})-(\d{2})/.exec(vencimento);
    const mes = partes ? `${partes[2]}-${partes[1]}` : 'sem-vencimento';
    return `${documento}-assinatura-${mes}.pdf`;
  };

  const baixarBoleto = async (assinatura: Assinatura) => {
    if (!assinatura.financeiro_id) return;
    setOcupado(`boleto-pdf-${assinatura.id}`);
    try {
      const res = await apiClient.get(
        `/superadmin/financeiro/${assinatura.financeiro_id}/baixar_boleto/`,
        { responseType: 'blob' },
      );
      const blob = res.data as Blob;
      const tipo = String(res.headers?.['content-type'] || blob.type || '');
      if (tipo.includes('json') || blob.type?.includes('json')) {
        const dados = JSON.parse(await blob.text()) as { error?: string };
        window.alert(dados.error || 'Não foi possível baixar o boleto.');
        return;
      }
      const cabecalho = String(res.headers?.['content-disposition'] || '');
      const marcado = cabecalho.match(/filename="([^"]+\.pdf)"/i);
      downloadBlobFile(blob, marcado?.[1] || nomeArquivoBoleto(assinatura));
    } catch (error) {
      const dados = (error as { response?: { data?: Blob } })?.response?.data;
      if (dados instanceof Blob) {
        try {
          const json = JSON.parse(await dados.text()) as { error?: string };
          window.alert(json.error || 'Não foi possível baixar o boleto.');
          return;
        } catch {
          // o corpo não era JSON
        }
      }
      window.alert(mensagemErro(error, 'Não foi possível baixar o boleto.'));
    } finally {
      setOcupado(null);
    }
  };

  const acaoBoleto = async (assinatura: Assinatura) => {
    if (!assinatura.financeiro_id) return;
    const confirma = window.confirm(
      `Reenviar o boleto em aberto de ${assinatura.loja_nome} para o e-mail do responsável?`,
    );
    if (!confirma) return;
    const chave = `boleto-reenviar-${assinatura.id}`;
    setOcupado(chave);
    try {
      const res = await apiClient.post(
        `/superadmin/financeiro/${assinatura.financeiro_id}/reenviar_boleto/`,
      );
      window.alert(res.data?.message || 'Boleto reenviado.');
      onAtualizar();
    } catch (error) {
      window.alert(mensagemErro(error, 'Não foi possível reenviar o boleto.'));
    } finally {
      setOcupado(null);
    }
  };

  const lojaHistorico = assinaturas.find((item) => item.id === historicoAberto);
  if (lojaHistorico) {
    const chaveHistorico = String(lojaHistorico.id);
    return (
      <div>
        <button
          type="button"
          onClick={() => {
            setHistoricoAberto(null);
            props.onHistoricoAberto?.(null);
          }}
          className="mb-4 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-200"
        >
          Voltar às assinaturas
        </button>
        <HistoricoLoja
          nome={lojaHistorico.loja_nome}
          plano={lojaHistorico.plano_nome}
          valor={lojaHistorico.plano_valor}
          carregando={ocupado === `historico-${lojaHistorico.id}`}
          trocando={ocupado === `banco-${lojaHistorico.id}` || ocupado === `historico-${lojaHistorico.id}`}
          erro={historicoErro[chaveHistorico]}
          itens={historicos[chaveHistorico]}
          provedor={bancosAssinatura[chaveHistorico] || 'asaas'}
          onTrocar={(provedor) => trocarBanco(lojaHistorico, provedor)}
          cancelada={Boolean(assinaturasCanceladas[chaveHistorico])}
          alterando={ocupado === `assinatura-${lojaHistorico.id}`}
          degustacao={degustacoes[chaveHistorico]}
          iniciandoDegustacao={ocupado === `degustacao-${lojaHistorico.id}`}
          onIniciarDegustacao={(dias) => iniciarDegustacao(lojaHistorico, dias)}
          onCancelar={() => alterarAssinatura(lojaHistorico, 'cancelar')}
          onReativar={() => alterarAssinatura(lojaHistorico, 'reativar')}
          ocupadoNota={ocupado}
          onBaixarNota={baixarNotaDoMes}
          onReenviarNota={(item) => reenviarNotaDoMes(item, lojaHistorico.loja_nome)}
        />
      </div>
    );
  }

  return (
    <>
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
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {assinatura.current_payment_data?.provedor === 'cora'
                          ? 'Cora'
                          : assinatura.current_payment_data?.provedor === 'mercadopago'
                            ? 'Mercado Pago'
                            : 'Asaas'}
                      </div>
                    </button>
                    <span className={`mt-1 inline-block px-2 py-0.5 text-xs rounded-full ${
                      assinatura.assinatura_cancelada
                        ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                        : assinatura.ativa
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}>
                      {assinatura.assinatura_cancelada
                        ? 'Cancelado'
                        : (assinatura.subscription_status_display || (assinatura.ativa ? 'Ativa' : 'Inativa'))}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-900 dark:text-gray-100">
                    <div>{assinatura.plano_nome}</div>
                    <div className="text-gray-500 dark:text-gray-400">{formatCurrency(assinatura.plano_valor)}</div>
                  </td>
                  <td className={`px-3 py-3 text-sm whitespace-nowrap ${
                    assinatura.assinatura_cancelada
                      ? 'font-semibold text-purple-600 dark:text-purple-400'
                      : corVencimento(assinatura.bloqueada, vencimento)
                  }`}>
                    {assinatura.assinatura_cancelada ? 'cancelado' : formatDate(vencimento)}
                    {cobrancaAberta && !assinatura.assinatura_cancelada && (
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
                    {assinatura.financeiro_id && assinatura.current_payment_data?.provedor !== 'mercadopago' ? (
                      <button
                        type="button"
                        disabled={semFinanceiro || ocupado === `conta-${assinatura.id}`}
                        onClick={() => {
                          setComprovante(null);
                          setConta(assinatura);
                        }}
                        className="px-2 py-1 text-xs bg-teal-700 text-white rounded hover:bg-teal-800 disabled:opacity-50"
                      >
                        Enviar comprovante
                      </button>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    {assinatura.current_payment_data?.is_paid ? (
                      <span className="text-xs text-gray-400">—</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        <button
                          type="button"
                          disabled={semFinanceiro || ocupado === `boleto-pdf-${assinatura.id}`}
                          onClick={() => baixarBoleto(assinatura)}
                          className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          PDF
                        </button>
                        <button
                          type="button"
                          disabled={semFinanceiro || ocupado === `boleto-reenviar-${assinatura.id}`}
                          onClick={() => acaoBoleto(assinatura)}
                          className="px-2 py-1 text-xs bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
                        >
                          Reenviar
                        </button>
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <button
                      type="button"
                      disabled={semFinanceiro || ocupado === `historico-${assinatura.id}`}
                      onClick={() => abrirHistorico(assinatura)}
                      className="px-2 py-1 text-xs bg-slate-700 text-white rounded hover:bg-slate-800 disabled:opacity-50"
                    >
                      Histórico
                    </button>
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
      {conta && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-lg bg-white dark:bg-gray-900 p-5 shadow-lg">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Enviar comprovante
            </h2>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
              Envie o PDF do banco ou uma foto nítida do comprovante. O sistema só baixa o boleto de {conta.loja_nome} se o pagamento estiver no nome e no CPF ou CNPJ do cadastro e o crédito aparecer na conta {conta.current_payment_data?.provedor === 'cora' ? 'Cora' : 'Asaas'}.
            </p>
            <label className="mt-4 block text-sm text-gray-700 dark:text-gray-200">
              Comprovante em PDF ou foto
              <input
                type="file"
                accept="application/pdf,.pdf,image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
                className="mt-1 block w-full text-sm"
                onChange={(evento) => setComprovante(evento.target.files?.[0] || null)}
              />
            </label>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setConta(null);
                  setComprovante(null);
                }}
                className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-200"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={!comprovante || ocupado === `conta-${conta.id}`}
                onClick={confirmarConta}
                className="px-3 py-1.5 text-sm bg-teal-700 text-white rounded hover:bg-teal-800 disabled:opacity-50"
              >
                Localizar pagamento
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function HistoricoLoja({
  nome,
  plano,
  valor,
  carregando,
  trocando,
  erro,
  itens,
  provedor,
  onTrocar,
  cancelada,
  alterando,
  degustacao,
  iniciandoDegustacao,
  onIniciarDegustacao,
  onCancelar,
  onReativar,
  ocupadoNota,
  onBaixarNota,
  onReenviarNota,
}: {
  nome: string;
  plano: string;
  valor: string;
  carregando: boolean;
  trocando: boolean;
  erro?: string;
  itens?: ItemHistorico[];
  provedor: string;
  onTrocar: (provedor: string) => void;
  cancelada: boolean;
  alterando: boolean;
  degustacao?: {
    em_degustacao: boolean;
    degustacao_ate: string | null;
    dias_apos_pagamento: number | null;
    boleto_em_aberto: boolean;
  };
  iniciandoDegustacao: boolean;
  onIniciarDegustacao: (dias: number) => void;
  onCancelar: () => void;
  onReativar: () => void;
  ocupadoNota: string | null;
  onBaixarNota: (item: ItemHistorico) => void;
  onReenviarNota: (item: ItemHistorico) => void;
}) {
  const [escolhido, setEscolhido] = useState(provedor || 'asaas');
  const [diasDegustacao, setDiasDegustacao] = useState(15);
  const temComprovante = Boolean(itens?.some((item) => item.comprovante_url));

  useEffect(() => {
    setEscolhido(provedor || 'asaas');
  }, [provedor]);

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{nome}</h2>
      <p className="mb-4 text-sm text-gray-500 dark:text-gray-400">
        {plano} · {formatCurrency(valor)}
      </p>
      <div className="mb-4 flex flex-wrap items-end gap-2">
        <label className="text-sm text-gray-700 dark:text-gray-200">
          Banco da assinatura
          <select
            value={escolhido}
            onChange={(evento) => setEscolhido(evento.target.value)}
            className="mt-1 block rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1.5 text-sm text-gray-900 dark:text-gray-100"
          >
            {BANCOS_ASSINATURA.map((banco) => (
              <option key={banco.id} value={banco.id}>{banco.nome}</option>
            ))}
          </select>
        </label>
        <button
          type="button"
          disabled={trocando || escolhido === (provedor || 'asaas')}
          onClick={() => onTrocar(escolhido)}
          className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
        >
          Trocar banco
        </button>
      </div>
      <p className="mb-4 text-xs text-gray-500 dark:text-gray-400">
        Se o boleto deste mês ainda não foi gerado, ele sai no banco novo. Se já foi gerado, a troca vale no próximo mês.
      </p>
      {!cancelada && (
        <div className="mb-4 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-3">
          <p className="text-sm font-medium text-amber-950 dark:text-amber-100">Demonstração</p>
          <p className="mt-1 text-xs text-amber-900 dark:text-amber-200">
            Sem boleto, os dias começam agora e nenhum boleto é gerado. Com boleto em aberto, a demonstração só começa depois do pagamento.
          </p>
          {degustacao?.em_degustacao && degustacao.degustacao_ate && (
            <p className="mt-2 text-sm text-amber-950 dark:text-amber-100">
              Em demonstração até {degustacao.degustacao_ate.split('-').reverse().join('/')}.
            </p>
          )}
          {degustacao?.dias_apos_pagamento ? (
            <p className="mt-2 text-sm text-amber-950 dark:text-amber-100">
              {degustacao.dias_apos_pagamento} dias começam quando o boleto em aberto for pago.
            </p>
          ) : null}
          <div className="mt-3 flex flex-wrap items-end gap-2">
            <label className="text-sm text-gray-700 dark:text-gray-200">
              Dias
              <select
                value={diasDegustacao}
                onChange={(evento) => setDiasDegustacao(Number(evento.target.value))}
                className="mt-1 block rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1.5 text-sm text-gray-900 dark:text-gray-100"
              >
                <option value={7}>7 dias</option>
                <option value={15}>15 dias</option>
                <option value={30}>30 dias</option>
                <option value={60}>60 dias</option>
              </select>
            </label>
            <button
              type="button"
              disabled={iniciandoDegustacao}
              onClick={() => onIniciarDegustacao(diasDegustacao)}
              className="px-3 py-1.5 text-sm bg-amber-600 text-white rounded hover:bg-amber-700 disabled:opacity-50"
            >
              Iniciar demonstração
            </button>
          </div>
        </div>
      )}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        {cancelada ? (
          <>
            <span className="text-sm text-red-700 dark:text-red-300">
              Assinatura cancelada. O acesso está bloqueado e nenhum boleto novo é emitido. Os dados do cliente permanecem.
            </span>
            <button
              type="button"
              disabled={alterando}
              onClick={onReativar}
              className="px-3 py-1.5 text-sm bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50"
            >
              Reativar
            </button>
          </>
        ) : (
          <button
            type="button"
            disabled={alterando}
            onClick={onCancelar}
            className="px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
          >
            Cancelar assinatura
          </button>
        )}
      </div>
      {carregando && <p className="text-sm text-gray-500">Carregando pagamentos e notas...</p>}
      {erro && <p className="text-sm text-red-600">{erro}</p>}
      {itens && itens.length === 0 && (
        <p className="text-sm text-gray-500">Nenhum pagamento nem nota fiscal nesta loja.</p>
      )}
      {itens && itens.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase text-gray-500 dark:text-gray-400">
                <th className="px-2 py-1">Mês</th>
                <th className="px-2 py-1">Vencimento</th>
                <th className="px-2 py-1">Valor</th>
                <th className="px-2 py-1">Status</th>
                <th className="px-2 py-1">Pago em</th>
                <th className="px-2 py-1">Nota fiscal</th>
                {temComprovante && <th className="px-2 py-1">Comprovante</th>}
                <th className="px-2 py-1">Banco</th>
              </tr>
            </thead>
            <tbody>
              {itens.map((item) => (
                <tr key={item.id} className="border-t border-gray-200 dark:border-gray-700">
                  <td className="px-2 py-2 text-gray-900 dark:text-gray-100">{item.mes || '—'}</td>
                  <td className="px-2 py-2 text-gray-900 dark:text-gray-100">{formatDate(item.vencimento)}</td>
                  <td className="px-2 py-2 text-gray-900 dark:text-gray-100">{formatCurrency(item.valor)}</td>
                  <td className="px-2 py-2">
                    <span className={`px-2 py-0.5 text-xs rounded-full ${COR_SITUACAO[item.situacao] || ''}`}>
                      {item.situacao_display}
                    </span>
                  </td>
                  <td className="px-2 py-2 text-gray-900 dark:text-gray-100">{formatDate(item.pago_em)}</td>
                  <td className="px-2 py-2">
                    {item.numero_nf ? (
                      <div className="flex flex-wrap items-center gap-1">
                        <span className="text-gray-900 dark:text-gray-100">NF {item.numero_nf}</span>
                        {item.nfse_id ? (
                          <>
                            <button
                              type="button"
                              disabled={ocupadoNota === `nf-hist-${item.nfse_id}`}
                              onClick={() => onBaixarNota(item)}
                              className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                            >
                              Baixar
                            </button>
                            <button
                              type="button"
                              disabled={ocupadoNota === `mail-hist-${item.nfse_id}`}
                              onClick={() => onReenviarNota(item)}
                              className="px-2 py-1 text-xs bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50"
                            >
                              Reenviar
                            </button>
                          </>
                        ) : null}
                      </div>
                    ) : (
                      <span className="text-gray-400">Sem nota</span>
                    )}
                  </td>
                  {temComprovante && (
                    <td className="px-2 py-2">
                      {item.comprovante_url ? (
                        <a
                          href={item.comprovante_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          PDF
                        </a>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                  )}
                  <td className="px-2 py-2 text-gray-900 dark:text-gray-100">{item.provedor_display || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
