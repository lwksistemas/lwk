'use client';

import { useState } from 'react';
import { Check, Mail, MessageCircle, Printer } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';
import { formatCurrency } from '@/lib/financeiro-helpers';
import {
  CabeleireiroAPI,
  type SalaoAgendamento,
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

export function ModalReceberSalao({ agendamento, onClose, onSuccess }: Props) {
  const valorInicial = Number(agendamento.valor || 0);
  const [amount, setAmount] = useState(String(valorInicial || ''));
  const [method, setMethod] = useState('PIX');
  const [desconto, setDesconto] = useState('0');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [payment, setPayment] = useState<SalaoPayment | null>(null);
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
      onSuccess(res.agendamento, res.payment);
    } catch (e) {
      const msg =
        e && typeof e === 'object' && 'response' in e
          ? (e as { response?: { data?: { error?: string } } }).response?.data?.error
          : undefined;
      setError(msg || 'Erro ao receber pagamento');
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
    } catch {
      alert('Erro ao enviar recibo');
    } finally {
      setSending(false);
    }
  };

  const imprimir = () => {
    if (!payment) return;
    const w = window.open('', '_blank', 'width=420,height=640');
    if (!w) return;
    w.document.write(`<!DOCTYPE html><html><head><title>Recibo</title>
      <style>body{font-family:Arial,sans-serif;padding:24px;color:#333}
      h1{font-size:16px;margin:0 0 8px} .muted{color:#666;font-size:12px}
      .total{font-size:20px;font-weight:bold;margin-top:16px}</style></head><body>
      <h1>Recibo de Pagamento</h1>
      <p class="muted">${payment.payment_date || ''}</p>
      <p><b>Cliente:</b> ${agendamento.cliente_nome}</p>
      <p><b>Serviço:</b> ${agendamento.servico_nome || '—'}</p>
      <p><b>Profissional:</b> ${agendamento.profissional_nome || '—'}</p>
      <p><b>Forma:</b> ${payment.payment_method_label || payment.payment_method}</p>
      <p class="total">Valor pago: ${formatCurrency(Number(payment.amount || 0))}</p>
      <p class="muted">Documento não fiscal</p>
      <script>window.print()</script></body></html>`);
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
            <div className="flex flex-wrap gap-2 pt-2">
              <button
                type="button"
                onClick={imprimir}
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
