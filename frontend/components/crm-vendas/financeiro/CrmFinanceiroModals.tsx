'use client';

import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import type {
  GrupoFinanceiro,
  LancamentoFinanceiro,
  TipoFinanceiro,
  VendedorOption,
} from '@/hooks/crm-vendas/useCrmFinanceiroPage';

interface LancamentoModalProps {
  open: boolean;
  tipo: TipoFinanceiro;
  editing: LancamentoFinanceiro | null;
  grupos: GrupoFinanceiro[];
  vendedores: VendedorOption[];
  isAdmin: boolean;
  saving: boolean;
  onClose: () => void;
  onSave: (payload: Record<string, unknown>) => void;
}

export function CrmLancamentoModal({
  open,
  tipo,
  editing,
  grupos,
  vendedores,
  isAdmin,
  saving,
  onClose,
  onSave,
}: LancamentoModalProps) {
  const [vendedorId, setVendedorId] = useState('');
  const [grupoId, setGrupoId] = useState('');
  const [descricao, setDescricao] = useState('');
  const [valor, setValor] = useState('');
  const [dataVencimento, setDataVencimento] = useState('');
  const [status, setStatus] = useState('pendente');
  const [observacoes, setObservacoes] = useState('');
  const [recorrente, setRecorrente] = useState(false);
  const [frequencia, setFrequencia] = useState('mensal');
  const [dataFimRecorrencia, setDataFimRecorrencia] = useState('');

  useEffect(() => {
    if (!open) return;
    setVendedorId(editing ? String(editing.vendedor) : vendedores[0]?.id ? String(vendedores[0].id) : '');
    setGrupoId(editing?.grupo ? String(editing.grupo) : '');
    setDescricao(editing?.descricao ?? '');
    setValor(editing ? String(editing.valor) : '');
    setDataVencimento(editing?.data_vencimento?.slice(0, 10) ?? new Date().toISOString().slice(0, 10));
    setStatus(editing?.status ?? 'pendente');
    setObservacoes(editing?.observacoes ?? '');
    setRecorrente(false);
    setFrequencia('mensal');
    setDataFimRecorrencia('');
  }, [open, editing, vendedores]);

  if (!open) return null;

  const gruposTipo = grupos.filter((g) => g.tipo === tipo && g.is_active);

  const inputCls =
    'mt-1 w-full rounded border border-gray-200 px-3 py-2 text-sm dark:bg-gray-800 dark:border-gray-700';
  const labelCls = 'block text-sm';

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: Record<string, unknown> = {
      tipo,
      descricao,
      valor: parseFloat(valor.replace(',', '.')) || 0,
      data_vencimento: dataVencimento,
      status,
      observacoes,
      grupo: grupoId ? Number(grupoId) : null,
    };
    if (isAdmin && vendedorId) payload.vendedor = Number(vendedorId);
    if (!editing && recorrente) {
      payload.recorrente = true;
      payload.frequencia = frequencia;
      if (dataFimRecorrencia) payload.data_fim_recorrencia = dataFimRecorrencia;
    }
    onSave(payload);
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between px-5 py-4 border-b dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {editing ? 'Editar' : 'Nova'} {tipo === 'receita' ? 'receita' : 'despesa'}
          </h2>
          <button type="button" onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
            <X size={20} />
          </button>
        </div>
        <form onSubmit={submit} className="p-5 md:p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-8">
            <div className="space-y-4">
              {isAdmin && (
                <label className={labelCls}>
                  <span className="text-gray-600 dark:text-gray-400">Vendedor</span>
                  <select
                    required
                    value={vendedorId}
                    onChange={(e) => setVendedorId(e.target.value)}
                    className={inputCls}
                  >
                    <option value="">Selecione</option>
                    {vendedores.map((v) => (
                      <option key={v.id} value={v.id}>{v.nome}</option>
                    ))}
                  </select>
                </label>
              )}
              <label className={labelCls}>
                <span className="text-gray-600 dark:text-gray-400">Grupo</span>
                <select value={grupoId} onChange={(e) => setGrupoId(e.target.value)} className={inputCls}>
                  <option value="">Sem grupo</option>
                  {gruposTipo.map((g) => (
                    <option key={g.id} value={g.id}>{g.nome}</option>
                  ))}
                </select>
              </label>
              <label className={labelCls}>
                <span className="text-gray-600 dark:text-gray-400">Descrição</span>
                <input
                  required
                  value={descricao}
                  onChange={(e) => setDescricao(e.target.value)}
                  className={inputCls}
                />
              </label>
              {!editing && (
                <div className="rounded-lg border border-dashed border-gray-200 dark:border-gray-700 p-3 space-y-3">
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                    <input
                      type="checkbox"
                      checked={recorrente}
                      onChange={(e) => setRecorrente(e.target.checked)}
                    />
                    Pagamento recorrente
                  </label>
                  {recorrente && (
                    <>
                      <label className={labelCls}>
                        <span className="text-gray-600 dark:text-gray-400">Frequência</span>
                        <select
                          value={frequencia}
                          onChange={(e) => setFrequencia(e.target.value)}
                          className={inputCls}
                        >
                          <option value="mensal">Mensal</option>
                          <option value="trimestral">Trimestral</option>
                          <option value="anual">Anual</option>
                        </select>
                      </label>
                      <label className={labelCls}>
                        <span className="text-gray-600 dark:text-gray-400">Encerrar em (opcional)</span>
                        <input
                          type="date"
                          value={dataFimRecorrencia}
                          onChange={(e) => setDataFimRecorrencia(e.target.value)}
                          className={inputCls}
                        />
                      </label>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        O primeiro vencimento usa a data acima; os próximos são gerados automaticamente.
                      </p>
                    </>
                  )}
                </div>
              )}
            </div>

            <div className="space-y-4">
              <label className={labelCls}>
                <span className="text-gray-600 dark:text-gray-400">Valor (R$)</span>
                <input
                  required
                  type="number"
                  step="0.01"
                  min="0"
                  value={valor}
                  onChange={(e) => setValor(e.target.value)}
                  className={inputCls}
                />
              </label>
              <label className={labelCls}>
                <span className="text-gray-600 dark:text-gray-400">Vencimento</span>
                <input
                  required
                  type="date"
                  value={dataVencimento}
                  onChange={(e) => setDataVencimento(e.target.value)}
                  className={inputCls}
                />
              </label>
              <label className={labelCls}>
                <span className="text-gray-600 dark:text-gray-400">Status</span>
                <select value={status} onChange={(e) => setStatus(e.target.value)} className={inputCls}>
                  <option value="pendente">Pendente</option>
                  <option value="pago">Pago</option>
                  <option value="cancelado">Cancelado</option>
                </select>
              </label>
              <label className={labelCls}>
                <span className="text-gray-600 dark:text-gray-400">Observações</span>
                <textarea
                  value={observacoes}
                  onChange={(e) => setObservacoes(e.target.value)}
                  rows={4}
                  className={inputCls}
                />
              </label>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-5 mt-5 border-t border-gray-100 dark:border-gray-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 text-sm rounded-lg bg-[#0176d3] text-white hover:bg-[#0159a8] disabled:opacity-50"
            >
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface GrupoModalProps {
  open: boolean;
  editing: GrupoFinanceiro | null;
  tipoInicial: TipoFinanceiro;
  saving: boolean;
  onClose: () => void;
  onSave: (payload: Record<string, unknown>) => void;
}

export function CrmGrupoModal({ open, editing, tipoInicial, saving, onClose, onSave }: GrupoModalProps) {
  const [nome, setNome] = useState('');
  const [tipo, setTipo] = useState<TipoFinanceiro>(tipoInicial);
  const [ordem, setOrdem] = useState('0');
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    if (!open) return;
    setNome(editing?.nome ?? '');
    setTipo(editing?.tipo ?? tipoInicial);
    setOrdem(String(editing?.ordem ?? 0));
    setIsActive(editing?.is_active ?? true);
  }, [open, editing, tipoInicial]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-sm">
        <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
          <h2 className="font-semibold">{editing ? 'Editar grupo' : 'Novo grupo'}</h2>
          <button type="button" onClick={onClose}><X size={20} /></button>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSave({ nome, tipo, ordem: Number(ordem), is_active: isActive });
          }}
          className="p-4 space-y-3"
        >
          <label className="block text-sm">
            Nome
            <input required value={nome} onChange={(e) => setNome(e.target.value)} className="mt-1 w-full rounded border px-3 py-2 dark:bg-gray-800" />
          </label>
          <label className="block text-sm">
            Tipo
            <select value={tipo} onChange={(e) => setTipo(e.target.value as TipoFinanceiro)} className="mt-1 w-full rounded border px-3 py-2 dark:bg-gray-800">
              <option value="receita">Receita</option>
              <option value="despesa">Despesa</option>
            </select>
          </label>
          <label className="block text-sm">
            Ordem
            <input type="number" value={ordem} onChange={(e) => setOrdem(e.target.value)} className="mt-1 w-full rounded border px-3 py-2 dark:bg-gray-800" />
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            Ativo
          </label>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-3 py-2 border rounded text-sm">Cancelar</button>
            <button type="submit" disabled={saving} className="px-3 py-2 bg-[#0176d3] text-white rounded text-sm">
              Salvar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
