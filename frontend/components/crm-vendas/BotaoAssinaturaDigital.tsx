'use client';

import { useState } from 'react';
import { FileSignature, CheckCircle, AlertCircle, Mail, MessageCircle } from 'lucide-react';
import { useWhatsappEnvioFlags } from '@/hooks/useWhatsappEnvioFlags';

interface BotaoAssinaturaDigitalProps {
  documentoId: number;
  tipoDocumento: 'proposta' | 'contrato';
  statusAssinatura?: string;
  leadEmail?: string;
  leadTelefone?: string;
  vendedorEmail?: string;
  vendedorTelefone?: string;
  vendedorNome?: string;
  onSucesso?: () => void;
  /** Linha de menu (dropdown) — mesmo padrão visual dos outros itens da lista. */
  variant?: 'default' | 'menuItem';
}

export default function BotaoAssinaturaDigital({
  documentoId,
  tipoDocumento,
  statusAssinatura = 'rascunho',
  leadEmail,
  leadTelefone,
  vendedorEmail,
  vendedorTelefone,
  vendedorNome,
  onSucesso,
  variant = 'default',
}: BotaoAssinaturaDigitalProps) {
  const [enviando, setEnviando] = useState(false);
  const [canalVendedor, setCanalVendedor] = useState<'email' | 'whatsapp'>('email');
  const [mensagem, setMensagem] = useState<{ tipo: 'sucesso' | 'erro'; texto: string } | null>(null);
  const { proposta: propostaWhatsapp, contrato: contratoWhatsapp } = useWhatsappEnvioFlags();
  const whatsappHabilitado = tipoDocumento === 'proposta' ? propostaWhatsapp : contratoWhatsapp;

  const temEmailCliente = !!(leadEmail || '').trim();
  const temTelefoneCliente = !!(leadTelefone || '').trim();
  const temEmailVendedor = !!(vendedorEmail || '').trim();
  const temTelefoneVendedor = !!(vendedorTelefone || '').trim();

  const endpointBase =
    tipoDocumento === 'proposta'
      ? `/crm-vendas/propostas/${documentoId}`
      : `/crm-vendas/contratos/${documentoId}`;

  const chamarApi = async (
    acao: 'enviar_para_assinatura' | 'reenviar_para_assinatura',
    body: Record<string, string>,
  ) => {
    const { default: apiClient } = await import('@/lib/api-client');
    return apiClient.post(`${endpointBase}/${acao}/`, body);
  };

  const enviarCliente = async (canalCliente: 'email' | 'whatsapp', canalVendedor: 'email' | 'whatsapp') => {
    if (canalCliente === 'email' && !temEmailCliente) {
      setMensagem({ tipo: 'erro', texto: 'Lead não possui e-mail cadastrado.' });
      return;
    }
    if (canalCliente === 'whatsapp' && !temTelefoneCliente) {
      setMensagem({ tipo: 'erro', texto: 'Lead não possui telefone cadastrado.' });
      return;
    }
    if (canalVendedor === 'email' && !temEmailVendedor) {
      setMensagem({ tipo: 'erro', texto: 'Vendedor não possui e-mail. Escolha WhatsApp ou cadastre o e-mail.' });
      return;
    }
    if (canalVendedor === 'whatsapp' && !temTelefoneVendedor) {
      setMensagem({ tipo: 'erro', texto: 'Vendedor não possui telefone. Escolha e-mail ou cadastre o telefone.' });
      return;
    }

    const labelCliente = canalCliente === 'whatsapp' ? 'WhatsApp' : 'e-mail';
    const labelVendedor = canalVendedor === 'whatsapp' ? 'WhatsApp' : 'e-mail';
    if (
      !confirm(
        `Enviar assinatura ao cliente por ${labelCliente}?\n\n` +
          `Quando o cliente assinar, o vendedor${vendedorNome ? ` (${vendedorNome})` : ''} receberá o link por ${labelVendedor}.`,
      )
    ) {
      return;
    }

    setEnviando(true);
    setMensagem(null);
    try {
      const res = await chamarApi('enviar_para_assinatura', {
        canal: canalCliente,
        canal_vendedor: canalVendedor,
      });
      setMensagem({ tipo: 'sucesso', texto: res.data.message || 'Enviado com sucesso.' });
      setTimeout(() => onSucesso?.(), 2000);
    } catch (err: unknown) {
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setMensagem({ tipo: 'erro', texto: detail || 'Erro ao enviar para assinatura.' });
    } finally {
      setEnviando(false);
    }
  };

  const reenviar = async (canal: 'email' | 'whatsapp', destino: 'cliente' | 'vendedor') => {
    if (destino === 'cliente') {
      if (canal === 'email' && !temEmailCliente) {
        setMensagem({ tipo: 'erro', texto: 'Lead não possui e-mail cadastrado.' });
        return;
      }
      if (canal === 'whatsapp' && !temTelefoneCliente) {
        setMensagem({ tipo: 'erro', texto: 'Lead não possui telefone cadastrado.' });
        return;
      }
    } else {
      if (canal === 'email' && !temEmailVendedor) {
        setMensagem({ tipo: 'erro', texto: 'Vendedor não possui e-mail cadastrado.' });
        return;
      }
      if (canal === 'whatsapp' && !temTelefoneVendedor) {
        setMensagem({ tipo: 'erro', texto: 'Vendedor não possui telefone cadastrado.' });
        return;
      }
    }

    const quem = destino === 'cliente' ? 'cliente' : `vendedor${vendedorNome ? ` (${vendedorNome})` : ''}`;
    const label = canal === 'whatsapp' ? 'WhatsApp' : 'e-mail';
    if (!confirm(`Reenviar link de assinatura por ${label} para o ${quem}?`)) return;

    setEnviando(true);
    setMensagem(null);
    try {
      const res = await chamarApi('reenviar_para_assinatura', { canal });
      setMensagem({ tipo: 'sucesso', texto: res.data.message || 'Reenviado.' });
      setTimeout(() => onSucesso?.(), 1500);
    } catch (err: unknown) {
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setMensagem({ tipo: 'erro', texto: detail || 'Erro ao reenviar.' });
    } finally {
      setEnviando(false);
    }
  };

  const SecaoTitulo = ({ children }: { children: React.ReactNode }) => (
    <p className="px-3 py-1 text-[10px] uppercase tracking-wide text-gray-400 dark:text-gray-500">{children}</p>
  );

  const BtnPreferencia = ({
    canal,
    ativo,
    onSelect,
    disabled,
  }: {
    canal: 'email' | 'whatsapp';
    ativo: boolean;
    onSelect: () => void;
    disabled?: boolean;
  }) => {
    const isWhatsapp = canal === 'whatsapp';
    const Icon = isWhatsapp ? MessageCircle : Mail;
    return (
      <button
        type="button"
        onClick={onSelect}
        disabled={disabled}
        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border disabled:opacity-50 ${
          ativo
            ? isWhatsapp
              ? 'bg-green-600 text-white border-green-600'
              : 'bg-blue-600 text-white border-blue-600'
            : isWhatsapp
              ? 'border-green-200 text-green-700 dark:border-green-800 dark:text-green-300'
              : 'border-blue-200 text-blue-700 dark:border-blue-800 dark:text-blue-300'
        }`}
      >
        <Icon size={12} />
        {isWhatsapp ? 'WhatsApp' : 'E-mail'}
      </button>
    );
  };

  const BtnCanal = ({
    canal,
    destino,
    modo,
    disabled,
    title,
  }: {
    canal: 'email' | 'whatsapp';
    destino: 'cliente' | 'vendedor';
    modo: 'enviar' | 'reenviar';
    disabled?: boolean;
    title?: string;
  }) => {
    const isWhatsapp = canal === 'whatsapp';
    const Icon = isWhatsapp ? MessageCircle : Mail;
    const label = isWhatsapp ? 'WhatsApp' : 'E-mail';
    const onClick =
      modo === 'enviar'
        ? () => enviarCliente(canal, canalVendedor)
        : () => reenviar(canal, destino);

    if (variant === 'menuItem') {
      return (
        <button
          type="button"
          onClick={onClick}
          disabled={enviando || disabled}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-left"
          title={title}
        >
          {enviando ? (
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-green-600 border-t-transparent shrink-0" />
          ) : (
            <Icon size={15} className={isWhatsapp ? 'text-green-500 shrink-0' : 'text-blue-500 shrink-0'} />
          )}
          <span>
            {modo === 'reenviar' ? 'Reenviar ' : ''}
            {label}
          </span>
        </button>
      );
    }

    return (
      <button
        type="button"
        onClick={onClick}
        disabled={enviando || disabled}
        className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
          isWhatsapp ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'
        }`}
        title={title}
      >
        <Icon className="w-4 h-4" />
        <span className="text-sm">{label}</span>
      </button>
    );
  };

  const MensagemBox = () =>
    mensagem ? (
      <div
        className={`mx-3 mb-2 text-xs px-2 py-1.5 rounded flex items-start gap-1.5 ${
          mensagem.tipo === 'sucesso'
            ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200'
            : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
        }`}
      >
        {mensagem.tipo === 'sucesso' ? (
          <CheckCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
        ) : (
          <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
        )}
        <span>{mensagem.texto}</span>
      </div>
    ) : null;

  if (statusAssinatura === 'rascunho') {
    const conteudo = (
      <>
        <SecaoTitulo>Cliente — enviar para assinar</SecaoTitulo>
        <div className={`flex flex-wrap gap-1.5 ${variant === 'menuItem' ? 'px-3 pb-2' : 'px-1 pb-2'}`}>
          <BtnCanal canal="email" destino="cliente" modo="enviar" disabled={!temEmailCliente} title="Enviar ao cliente por e-mail" />
          {whatsappHabilitado && (
            <BtnCanal canal="whatsapp" destino="cliente" modo="enviar" disabled={!temTelefoneCliente} title="Enviar ao cliente por WhatsApp" />
          )}
        </div>
        <SecaoTitulo>Vendedor — após cliente assinar</SecaoTitulo>
        <p className="px-3 pb-1 text-[11px] text-gray-500 dark:text-gray-400">
          {vendedorNome ? `${vendedorNome}: ` : ''}escolha como o vendedor receberá o link.
        </p>
        <div className={`flex flex-wrap gap-1.5 ${variant === 'menuItem' ? 'px-3 pb-2' : 'px-1 pb-2'}`}>
          <BtnPreferencia canal="email" ativo={canalVendedor === 'email'} onSelect={() => setCanalVendedor('email')} disabled={!temEmailVendedor} />
          {whatsappHabilitado && (
            <BtnPreferencia canal="whatsapp" ativo={canalVendedor === 'whatsapp'} onSelect={() => setCanalVendedor('whatsapp')} disabled={!temTelefoneVendedor} />
          )}
        </div>
        <MensagemBox />
      </>
    );

    if (variant === 'menuItem') {
      return <div className="space-y-0 border-t border-gray-100 dark:border-gray-700 mt-1 pt-1">{conteudo}</div>;
    }
    return (
      <div className="space-y-2 p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-800 dark:text-gray-200">
          <FileSignature className="w-4 h-4" />
          Assinatura digital
        </div>
        {conteudo}
      </div>
    );
  }

  if (statusAssinatura === 'aguardando_cliente') {
    return (
      <div className={variant === 'menuItem' ? 'border-t border-gray-100 dark:border-gray-700 mt-1 pt-1' : 'space-y-2'}>
        <SecaoTitulo>Reenviar ao cliente</SecaoTitulo>
        <BtnCanal canal="email" destino="cliente" modo="reenviar" disabled={!temEmailCliente} />
        {whatsappHabilitado && (
          <BtnCanal canal="whatsapp" destino="cliente" modo="reenviar" disabled={!temTelefoneCliente} />
        )}
        <MensagemBox />
      </div>
    );
  }

  if (statusAssinatura === 'aguardando_vendedor') {
    return (
      <div className={variant === 'menuItem' ? 'border-t border-gray-100 dark:border-gray-700 mt-1 pt-1' : 'space-y-2'}>
        <SecaoTitulo>
          Vendedor{vendedorNome ? `: ${vendedorNome}` : ''} — assinar
        </SecaoTitulo>
        <p className="px-3 pb-1 text-[11px] text-gray-500 dark:text-gray-400">
          Cliente já assinou. Reenvie o link ao vendedor por e-mail ou WhatsApp.
        </p>
        <BtnCanal canal="email" destino="vendedor" modo="reenviar" disabled={!temEmailVendedor} />
        {whatsappHabilitado && (
          <BtnCanal canal="whatsapp" destino="vendedor" modo="reenviar" disabled={!temTelefoneVendedor} />
        )}
        <MensagemBox />
      </div>
    );
  }

  return null;
}
