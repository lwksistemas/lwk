'use client';

import { useEffect, useMemo, useState } from 'react';
import { MessageCircle, X } from 'lucide-react';
import { formatTelefone, telefoneInternacionalBr } from '@/lib/format-br';
import type { Atividade } from '../page';

const TIPO_LABEL: Record<string, string> = {
  call: 'Ligação', meeting: 'Reunião', email: 'Email', task: 'Tarefa',
};

interface ContaOption {
  id: number;
  nome: string;
}

interface LeadOption {
  id: number;
  nome: string;
  empresa?: string;
  telefone?: string;
}

interface FormData {
  titulo: string;
  tipo: Atividade['tipo'];
  data: string;
  duracao_minutos: number;
  observacoes: string;
  conta: number | null;
  lead: number | null;
  lembrete_whatsapp: boolean;
  lembrete_whatsapp_telefone: string;
}

interface Props {
  atividade: Atividade | null;
  form: FormData;
  saving: boolean;
  error: string | null;
  contas: ContaOption[];
  leads: LeadOption[];
  whatsappHabilitado?: boolean;
  onChange: (patch: Partial<FormData>) => void;
  onSave: () => void;
  onSaveAndWhatsapp?: (telefone: string) => void;
  onEnviarWhatsapp?: (telefone: string) => void;
  onClose: () => void;
  onToggleConcluido?: () => void;
  onDelete?: () => void;
}

const inputClass = 'w-full px-3 py-2.5 min-h-[44px] rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white touch-manipulation';

function normalizarBusca(valor: string): string {
  return valor
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

function rotuloLead(lead: LeadOption): string {
  const empresa = (lead.empresa || '').trim();
  if (empresa && empresa.toLowerCase() !== (lead.nome || '').trim().toLowerCase()) {
    return `${lead.nome} — ${empresa}`;
  }
  return lead.nome;
}

export function AtividadeModal({
  atividade,
  form,
  saving,
  error,
  leads,
  whatsappHabilitado = false,
  onChange,
  onSave,
  onSaveAndWhatsapp,
  onEnviarWhatsapp,
  onClose,
  onToggleConcluido,
  onDelete,
}: Props) {
  const [leadBusca, setLeadBusca] = useState('');
  const patch = (partial: Partial<FormData>) => onChange(partial);
  const set = (field: keyof FormData, value: string | number | boolean | null) => patch({ [field]: value });

  const leadSelecionado = useMemo(
    () => (form.lead ? leads.find((l) => l.id === form.lead) : undefined),
    [form.lead, leads],
  );

  useEffect(() => {
    if (atividade && form.lead) {
      const nome = leadSelecionado?.nome || atividade.lead_nome || '';
      if (nome) setLeadBusca(nome);
      if (leadSelecionado?.telefone && !form.lembrete_whatsapp_telefone.trim()) {
        patch({ lembrete_whatsapp_telefone: formatTelefone(leadSelecionado.telefone) });
      }
      return;
    }
    if (!form.lead) {
      setLeadBusca('');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [atividade?.id, form.lead, leadSelecionado, atividade?.lead_nome]);

  const leadsFiltrados = useMemo(() => {
    const q = normalizarBusca(leadBusca.trim());
    if (!q) return leads.slice(0, 80);
    return leads.filter((l) => {
      const nome = normalizarBusca(l.nome || '');
      const empresa = normalizarBusca(l.empresa || '');
      return nome.includes(q) || empresa.includes(q);
    });
  }, [leads, leadBusca]);

  const limparLead = () => {
    setLeadBusca('');
    set('lead', null);
  };

  const telefonePayload = () => telefoneInternacionalBr(form.lembrete_whatsapp_telefone);

  const handleWhatsapp = () => {
    if (!onEnviarWhatsapp) return;
    const tel = telefonePayload();
    if (tel.replace(/\D/g, '').length < 10) return;
    onEnviarWhatsapp(tel);
  };

  const handleSaveAndWhatsapp = () => {
    if (!onSaveAndWhatsapp) return;
    const tel = telefonePayload();
    if (tel.replace(/\D/g, '').length < 10) return;
    onSaveAndWhatsapp(tel);
  };

  const telefoneValido = form.lembrete_whatsapp_telefone.replace(/\D/g, '').length >= 10;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} aria-hidden="true" />
      <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 overflow-y-auto">
        <div
          className="bg-white dark:bg-gray-800 rounded-t-xl sm:rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md max-h-[95vh] overflow-y-auto sm:max-w-4xl sm:max-h-[90vh] sm:w-[calc(100vw-2rem)]"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {atividade ? 'Editar atividade' : 'Nova atividade'}
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
              aria-label="Fechar"
            >
              <X size={20} />
            </button>
          </div>

          <div className="p-4 sm:p-6 space-y-4">
            {error && (
              <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
                {error}
              </p>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Título</label>
                  <input
                    type="text"
                    value={form.titulo}
                    onChange={(e) => set('titulo', e.target.value)}
                    className={inputClass}
                    placeholder="Ex: Ligar para cliente"
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label>
                    <select value={form.tipo} onChange={(e) => set('tipo', e.target.value)} className={inputClass}>
                      {Object.entries(TIPO_LABEL).map(([k, v]) => (
                        <option key={k} value={k}>{v}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Duração</label>
                    <select
                      value={form.duracao_minutos}
                      onChange={(e) => set('duracao_minutos', Number(e.target.value))}
                      className={inputClass}
                    >
                      {[15, 30, 45, 60, 90, 120, 180, 240].map((m) => (
                        <option key={m} value={m}>
                          {m < 60 ? `${m} min` : `${m / 60}h${m % 60 ? ` ${m % 60}min` : ''}`}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data e hora</label>
                  <input
                    type="datetime-local"
                    value={form.data}
                    onChange={(e) => set('data', e.target.value)}
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Lead</label>
                  <input
                    type="text"
                    value={leadBusca}
                    onChange={(e) => {
                      const valor = e.target.value;
                      setLeadBusca(valor);
                      if (!form.lead) return;
                      const nomeAtual = leadSelecionado?.nome || atividade?.lead_nome || '';
                      if (nomeAtual && normalizarBusca(valor) === normalizarBusca(nomeAtual)) return;
                      patch({ lead: null });
                    }}
                    className={inputClass}
                    placeholder="Buscar lead pelo nome..."
                    autoComplete="off"
                  />
                  {leadBusca.trim() && !form.lead && leadsFiltrados.length > 0 && (
                    <div className="w-full mt-1 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 max-h-36 overflow-y-auto">
                      {leadsFiltrados.slice(0, 20).map((l) => (
                        <button
                          key={l.id}
                          type="button"
                          onClick={() => {
                            const updates: Partial<FormData> = { lead: l.id };
                            if (l.telefone) {
                              updates.lembrete_whatsapp_telefone = formatTelefone(l.telefone);
                            }
                            patch(updates);
                            setLeadBusca(l.nome);
                          }}
                          className="w-full text-left px-3 py-2 text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600 border-b border-gray-100 dark:border-gray-600 last:border-b-0"
                        >
                          {rotuloLead(l)}
                        </button>
                      ))}
                    </div>
                  )}
                  {leadBusca.trim() && !form.lead && leadsFiltrados.length === 0 && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Nenhum lead encontrado.</p>
                  )}
                  {form.lead && (leadSelecionado || atividade?.lead_nome) && (
                    <div className="flex items-center justify-between gap-2 mt-1">
                      <p className="text-xs text-green-600 dark:text-green-400">
                        ✓ {leadSelecionado ? rotuloLead(leadSelecionado) : atividade?.lead_nome}
                      </p>
                      <button type="button" onClick={limparLead} className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
                        Remover
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
                  <textarea
                    value={form.observacoes}
                    onChange={(e) => set('observacoes', e.target.value)}
                    rows={5}
                    className="w-full min-h-[120px] px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Detalhes da atividade (opcional)"
                  />
                </div>

                {whatsappHabilitado && (
                  <div className="rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 p-4 space-y-3">
                    <div className="flex items-center gap-2 text-green-800 dark:text-green-300">
                      <MessageCircle size={18} />
                      <span className="text-sm font-medium">WhatsApp</span>
                    </div>
                    <label className="flex items-start gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={form.lembrete_whatsapp}
                        onChange={(e) => set('lembrete_whatsapp', e.target.checked)}
                        className="mt-1 rounded border-gray-300 text-green-600 focus:ring-green-500"
                      />
                      <span className="text-sm text-gray-800 dark:text-gray-200">
                        Lembretes automáticos <strong>24h</strong> e <strong>2h</strong> antes da atividade
                      </span>
                    </label>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                        Número do WhatsApp
                      </label>
                      <input
                        type="tel"
                        value={form.lembrete_whatsapp_telefone}
                        onChange={(e) => set('lembrete_whatsapp_telefone', formatTelefone(e.target.value))}
                        className={inputClass}
                        placeholder="(00) 00000-0000"
                      />
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {form.lembrete_whatsapp
                          ? 'O sistema enviará mensagens automáticas neste número antes da atividade.'
                          : 'Marque os lembretes automáticos ou use o botão abaixo para enviar agora.'}
                        {form.lead ? ' Telefone do lead preenchido automaticamente.' : ''}
                      </p>
                    </div>
                    {atividade && onEnviarWhatsapp && (
                      <button
                        type="button"
                        onClick={handleWhatsapp}
                        disabled={saving || !telefoneValido}
                        className="w-full px-4 py-2.5 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium flex items-center justify-center gap-2"
                      >
                        <MessageCircle size={16} />
                        {saving ? 'Enviando...' : 'Enviar WhatsApp agora'}
                      </button>
                    )}
                  </div>
                )}

                {atividade && (
                  <div className="flex gap-2 flex-wrap">
                    {onToggleConcluido && (
                      <button
                        type="button"
                        onClick={onToggleConcluido}
                        disabled={saving}
                        className="px-3 py-2 rounded-lg text-sm font-medium bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
                      >
                        {atividade.concluido ? 'Desmarcar concluída' : 'Marcar concluída'}
                      </button>
                    )}
                    {onDelete && (
                      <button
                        type="button"
                        onClick={onDelete}
                        disabled={saving}
                        className="px-3 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
                      >
                        Excluir
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="p-4 sm:p-6 border-t border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 touch-manipulation min-h-[44px]"
            >
              Cancelar
            </button>
            {whatsappHabilitado && onSaveAndWhatsapp && (
              <button
                type="button"
                onClick={handleSaveAndWhatsapp}
                disabled={saving || !telefoneValido}
                className="px-4 py-2.5 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium touch-manipulation min-h-[44px] flex items-center justify-center gap-2"
              >
                <MessageCircle size={16} />
                {saving ? 'Salvando...' : 'Salvar e enviar WhatsApp'}
              </button>
            )}
            <button
              type="button"
              onClick={onSave}
              disabled={saving || (form.lembrete_whatsapp && !telefoneValido)}
              className="px-4 py-2.5 rounded-lg bg-[#0176d3] hover:bg-[#0159a8] text-white font-medium disabled:opacity-50 touch-manipulation min-h-[44px]"
            >
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
