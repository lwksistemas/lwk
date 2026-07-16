'use client';

import { useState } from 'react';
import { Check, Mail, MessageCircle, Printer } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';
import { formatApiError } from '@/lib/api-errors';
import { formatCep, formatCpfCnpj, formatTelefone } from '@/lib/format-br';
import { formatCurrency } from '@/lib/financeiro-helpers';
import {
  CabeleireiroAPI,
  type SalaoAgendamento,
  type SalaoLojaInfo,
  type SalaoPayment,
} from '@/lib/cabeleireiro-api';

const METHODS = [
  { value: 'CASH', label: 'Dinheiro' },
  { value: 'PIX', label: 'PIX' },
  { value: 'CREDIT_CARD', label: 'Cartão de Crédito' },
  { value: 'DEBIT_CARD', label: 'Cartão de Débito' },
  { value: 'TRANSFER', label: 'Transferência' },
];

type Props = {
  agendamento: SalaoAgendamento;
  onClose: () => void;
  onSuccess: (ag: SalaoAgendamento, payment: SalaoPayment) => void;
};

function labelDocumentoLoja(cpfCnpj?: string): string {
  const d = (cpfCnpj || '').replace(/\D/g, '');
  if (d.length === 11) return 'CPF';
  if (d.length === 14) return 'CNPJ';
  return 'CPF/CNPJ';
}

function linhaTelCep(telefone?: string, cep?: string): string {
  const partes: string[] = [];
  const tel = formatTelefone(telefone || '');
  const cepFmt = formatCep(cep || '');
  if (tel) partes.push(`Tel: ${tel}`);
  if (cepFmt) partes.push(`CEP ${cepFmt}`);
  return partes.join('  ·  ');
}

function formatDataHora(isoOrDate?: string | null, hora?: string | null): string {
  if (!isoOrDate && !hora) return '—';
  if (isoOrDate && isoOrDate.includes('T')) {
    return new Date(isoOrDate).toLocaleString('pt-BR', {
      timeZone: 'America/Sao_Paulo',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
  if (isoOrDate && hora) {
    const h = hora.slice(0, 5);
    const [y, m, d] = isoOrDate.split('-');
    if (y && m && d) return `${d}/${m}/${y} ${h}`;
    return `${isoOrDate} ${h}`;
  }
  if (isoOrDate) {
    const [y, m, d] = isoOrDate.split('-');
    if (y && m && d) return `${d}/${m}/${y}`;
    return isoOrDate;
  }
  return hora?.slice(0, 5) || '—';
}

function gerarHtmlReciboSalao(params: {
  agendamento: SalaoAgendamento;
  payment: SalaoPayment;
  desconto: number;
  lojaData: SalaoLojaInfo;
}): string {
  const { agendamento, payment, desconto, lojaData } = params;
  const valorPago = Number(payment.amount || 0);
  const valorServico = Number(agendamento.valor || payment.valor_total || valorPago);
  const totalGeral = desconto > 0 ? valorServico : Number(payment.valor_total_efetivo ?? valorServico);
  const totalAposDesconto = Math.max(totalGeral - desconto, 0);
  const dataHoraPagamento = payment.payment_date
    ? formatDataHora(payment.payment_date)
    : new Date().toLocaleString('pt-BR', {
        timeZone: 'America/Sao_Paulo',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
  const dataAtendimento = formatDataHora(agendamento.data, agendamento.hora_inicio);
  const telCep = linhaTelCep(lojaData.telefone || lojaData.owner_telefone, lojaData.cep);
  const metodo = payment.payment_method_label || payment.payment_method || 'Pagamento';
  const servicoNome = agendamento.servico_nome || 'Atendimento';
  const subtotalExibir = desconto > 0 ? totalGeral : totalAposDesconto;

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Recibo de Pagamento</title>
<style>
  @page { size: 80mm auto; margin: 4mm; }
  body { font-family: 'Courier New', monospace; width: 72mm; margin: 0 auto; padding: 8px; font-size: 11px; line-height: 1.4; }
  .header { text-align: center; border-bottom: 1px dashed #333; padding-bottom: 6px; margin-bottom: 8px; }
  .header h1 { font-size: 13px; margin: 0 0 2px; }
  .header p { margin: 1px 0; font-size: 10px; color: #444; }
  .section { margin: 6px 0; }
  .section-title { font-weight: bold; font-size: 10px; text-transform: uppercase; border-bottom: 1px dotted #aaa; margin-bottom: 4px; }
  table { width: 100%; border-collapse: collapse; font-size: 11px; }
  td { padding: 2px 0; vertical-align: top; }
  .divider { border-top: 1px dashed #333; margin: 8px 0; }
  .total { font-size: 14px; font-weight: bold; text-align: center; margin: 8px 0; }
  .footer { text-align: center; font-size: 9px; color: #666; margin-top: 10px; border-top: 1px dashed #333; padding-top: 6px; }
  @media print { body { margin: 0; width: 72mm; } }
</style>
</head><body>
<div class="header">
  <h1>${lojaData.nome || 'SALÃO'}</h1>
  ${lojaData.cpf_cnpj ? `<p>${labelDocumentoLoja(lojaData.cpf_cnpj)}: ${formatCpfCnpj(lojaData.cpf_cnpj)}</p>` : ''}
  ${lojaData.endereco ? `<p>${lojaData.endereco}</p>` : ''}
  ${telCep ? `<p>${telCep}</p>` : ''}
  ${lojaData.email || lojaData.owner_email ? `<p>${lojaData.email || lojaData.owner_email}</p>` : ''}
  <p style="margin-top:4px;font-weight:bold">RECIBO DE PAGAMENTO</p>
  <p>${dataHoraPagamento}</p>
</div>

<div class="section">
  <div class="section-title">Cliente</div>
  <table>
    <tr><td>${agendamento.cliente_nome}</td></tr>
  </table>
</div>

<div class="section">
  <div class="section-title">Profissional</div>
  <table>
    <tr><td>${agendamento.profissional_nome || '—'}</td></tr>
  </table>
</div>

<div class="section">
  <div class="section-title">Data/Hora do atendimento</div>
  <table>
    <tr><td>${dataAtendimento}</td></tr>
  </table>
</div>

<div class="section">
  <div class="section-title">Serviços</div>
  <table>
    <tr><td style="padding-left:8px">• ${servicoNome}</td><td style="text-align:right">R$ ${valorServico.toFixed(2)}</td></tr>
  </table>
</div>

<div class="divider"></div>
<table>
  <tr><td><strong>Subtotal</strong></td><td style="text-align:right"><strong>R$ ${subtotalExibir.toFixed(2)}</strong></td></tr>
  ${desconto > 0 ? `<tr><td>Desconto</td><td style="text-align:right">- R$ ${desconto.toFixed(2)}</td></tr>` : ''}
  <tr><td><strong>Total</strong></td><td style="text-align:right"><strong>R$ ${totalAposDesconto.toFixed(2)}</strong></td></tr>
</table>

<div class="section">
  <div class="section-title">Formas de pagamento:</div>
  <table>
    <tr><td>${metodo}</td><td style="text-align:right">R$ ${valorPago.toFixed(2)}</td></tr>
  </table>
</div>

<div class="total">VALOR PAGO: R$ ${valorPago.toFixed(2)}</div>
${
  valorPago + 0.009 >= totalAposDesconto && totalAposDesconto > 0
    ? `<div class="footer" style="border-top:none;margin-top:0;"><p style="font-weight:bold;color:#333;">Quitado</p></div>`
    : ''
}

<div class="footer">
  <p>Agradecemos pela confiança!</p>
  <p>Documento não fiscal — gerado pelo sistema.</p>
  <button onclick="window.print()" style="margin-top:8px;padding:6px 16px;font-size:12px;cursor:pointer;border:1px solid #333;border-radius:4px;background:#fff;">Imprimir</button>
</div>
</body></html>`;
}

export function ModalReceberSalao({ agendamento, onClose, onSuccess }: Props) {
  const valorInicial = Number(agendamento.valor || 0);
  const [amount, setAmount] = useState(String(valorInicial || ''));
  const [method, setMethod] = useState('PIX');
  const [desconto, setDesconto] = useState('0');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [payment, setPayment] = useState<SalaoPayment | null>(null);
  const [descontoAplicado, setDescontoAplicado] = useState(0);
  const [sending, setSending] = useState(false);

  const save = async () => {
    setError('');
    const valor = Number(String(amount).replace(',', '.'));
    const desc = Number(String(desconto).replace(',', '.')) || 0;
    if (Number.isNaN(valor) || valor <= 0) {
      setError('Informe um valor válido.');
      return;
    }
    setSaving(true);
    try {
      const res = await CabeleireiroAPI.receberAgendamento(agendamento.id, {
        amount: valor,
        payment_method: method,
        desconto: desc,
      });
      setPayment(res.payment);
      setDescontoAplicado(desc);
      onSuccess(res.agendamento, res.payment);
    } catch (e) {
      setError(formatApiError(e) || 'Erro ao receber pagamento');
    } finally {
      setSaving(false);
    }
  };

  const enviar = async (canal: 'email' | 'whatsapp') => {
    if (!payment) return;
    setSending(true);
    try {
      const res = await CabeleireiroAPI.payments.enviarRecibo(payment.id, canal);
      alert(res.message || (res.success ? 'Enviado' : res.error || 'Falha'));
    } catch (e) {
      alert(formatApiError(e) || 'Erro ao enviar recibo');
    } finally {
      setSending(false);
    }
  };

  const imprimir = async () => {
    if (!payment) return;
    let lojaData: SalaoLojaInfo = {};
    try {
      lojaData = await CabeleireiroAPI.loja.info();
    } catch {
      /* defaults */
    }
    const desc =
      descontoAplicado ||
      Number(payment.desconto || 0) ||
      0;
    const html = gerarHtmlReciboSalao({
      agendamento,
      payment,
      desconto: desc,
      lojaData,
    });
    const w = window.open('', '_blank', 'width=320,height=700');
    if (!w) return;
    w.document.write(html);
    w.document.close();
  };

  return (
    <Modal isOpen onClose={onClose} maxWidth="md">
      <div className="p-6 space-y-4">
        {!payment ? (
          <>
            <h2 className="text-lg font-semibold">Receber pagamento</h2>
            <p className="text-sm text-gray-500">
              {agendamento.cliente_nome} — {agendamento.servico_nome || 'Atendimento'}
            </p>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <label className="block text-sm space-y-1">
              <span>Valor (R$)</span>
              <input
                type="number"
                step="0.01"
                min="0"
                className="w-full border rounded-lg px-3 py-2"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
            </label>
            <label className="block text-sm space-y-1">
              <span>Desconto (R$)</span>
              <input
                type="number"
                step="0.01"
                min="0"
                className="w-full border rounded-lg px-3 py-2"
                value={desconto}
                onChange={(e) => setDesconto(e.target.value)}
              />
            </label>
            <label className="block text-sm space-y-1">
              <span>Forma de pagamento</span>
              <select
                className="w-full border rounded-lg px-3 py-2"
                value={method}
                onChange={(e) => setMethod(e.target.value)}
              >
                {METHODS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg text-sm">
                Cancelar
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={() => void save()}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm text-white disabled:opacity-60"
                style={{ backgroundColor: SALAO_PRIMARY }}
              >
                <Check size={14} />
                {saving ? 'Salvando...' : 'Confirmar recebimento'}
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 className="text-lg font-semibold text-emerald-700">Pagamento registrado</h2>
            <p className="text-sm text-gray-600">
              {formatCurrency(Number(payment.amount || 0))} ·{' '}
              {payment.payment_method_label || payment.payment_method}
            </p>
            <p className="text-xs text-gray-500">
              Comissão: {formatCurrency(Number(payment.comissao_valor || 0))}
            </p>
            <p className="text-sm text-gray-600 pt-1">Envie o recibo de pagamento para o cliente:</p>
            <div className="flex flex-wrap gap-2 pt-2">
              <button
                type="button"
                onClick={() => void imprimir()}
                className="inline-flex items-center gap-1.5 px-3 py-2 border rounded-lg text-sm"
              >
                <Printer size={14} /> Imprimir
              </button>
              <button
                type="button"
                disabled={sending}
                onClick={() => void enviar('email')}
                className="inline-flex items-center gap-1.5 px-3 py-2 border rounded-lg text-sm"
              >
                <Mail size={14} /> Email
              </button>
              <button
                type="button"
                disabled={sending}
                onClick={() => void enviar('whatsapp')}
                className="inline-flex items-center gap-1.5 px-3 py-2 border rounded-lg text-sm text-emerald-700"
              >
                <MessageCircle size={14} /> WhatsApp
              </button>
              <button type="button" onClick={onClose} className="ml-auto px-3 py-2 text-sm border rounded-lg">
                Fechar
              </button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
