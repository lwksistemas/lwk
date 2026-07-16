'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';
import {
  CabeleireiroAPI,
  type SalaoCategoriaServico,
  type SalaoProfissionalComissao,
  type SalaoServico,
} from '@/lib/cabeleireiro-api';

type Row = {
  categoria: number | '';
  servico: number | '';
  modo: 'percentual' | 'fixo';
  valor: string;
};

type Props = {
  profissionalId: number;
  profissionalNome: string;
  onClose: () => void;
};

function norm(s: string) {
  return (s || '').trim().toUpperCase();
}

function toRows(list: SalaoProfissionalComissao[]): Row[] {
  return list
    .filter((c) => c.servico)
    .map((c) => ({
      categoria: c.categoria,
      servico: c.servico as number,
      modo: c.modo === 'fixo' ? 'fixo' : 'percentual',
      valor: String(c.valor ?? ''),
    }));
}

export function ModalComissoesSalao({ profissionalId, profissionalNome, onClose }: Props) {
  const [categorias, setCategorias] = useState<SalaoCategoriaServico[]>([]);
  const [servicos, setServicos] = useState<SalaoServico[]>([]);
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const catById = useMemo(() => {
    const m = new Map<number, SalaoCategoriaServico>();
    for (const c of categorias) m.set(c.id, c);
    return m;
  }, [categorias]);

  const servicosDaCategoria = useCallback(
    (categoriaId: number | '') => {
      if (categoriaId === '' || categoriaId == null) return [];
      const cat = catById.get(Number(categoriaId));
      if (!cat) return [];
      const nome = norm(cat.nome);
      return servicos.filter((s) => norm(s.categoria || '') === nome);
    },
    [catById, servicos],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [cats, svcs, comissoes] = await Promise.all([
        CabeleireiroAPI.categorias.list(),
        CabeleireiroAPI.servicos.list(),
        CabeleireiroAPI.profissionais.comissoes.list(profissionalId),
      ]);
      setCategorias(cats.filter((c) => c.is_active !== false));
      setServicos(svcs);
      setRows(toRows(comissoes));
    } catch {
      setError('Erro ao carregar comissões');
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [profissionalId]);

  useEffect(() => {
    void load();
  }, [load]);

  const addRow = () => {
    setRows((prev) => [...prev, { categoria: '', servico: '', modo: 'percentual', valor: '' }]);
  };

  const updateRow = (idx: number, patch: Partial<Row>) => {
    setRows((prev) =>
      prev.map((r, i) => {
        if (i !== idx) return r;
        const next = { ...r, ...patch };
        if ('categoria' in patch && patch.categoria !== r.categoria) {
          next.servico = '';
        }
        return next;
      }),
    );
  };

  const removeRow = (idx: number) => {
    setRows((prev) => prev.filter((_, i) => i !== idx));
  };

  const save = async () => {
    setError('');
    const used = new Set<number>();
    const payload: { categoria: number; servico: number; modo: string; valor: number }[] = [];

    for (const row of rows) {
      if (row.categoria === '' || row.categoria == null) {
        setError('Selecione a categoria em todas as linhas.');
        return;
      }
      if (row.servico === '' || row.servico == null) {
        setError('Selecione o serviço em todas as linhas.');
        return;
      }
      const svcId = Number(row.servico);
      if (used.has(svcId)) {
        setError('Não repita o mesmo serviço.');
        return;
      }
      used.add(svcId);
      const valor = Number(String(row.valor).replace(',', '.'));
      if (Number.isNaN(valor) || valor < 0) {
        setError('Informe um valor válido (zero ou positivo).');
        return;
      }
      if (row.modo === 'percentual' && valor > 100) {
        setError('Percentual não pode ser maior que 100.');
        return;
      }
      payload.push({
        categoria: Number(row.categoria),
        servico: svcId,
        modo: row.modo,
        valor,
      });
    }

    setSaving(true);
    try {
      await CabeleireiroAPI.profissionais.comissoes.save(profissionalId, payload);
      onClose();
    } catch {
      setError('Erro ao salvar comissões');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal isOpen onClose={onClose} maxWidth="2xl">
      <div className="p-6 space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Comissões</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            {profissionalNome} — escolha a categoria, o serviço e o valor (% ou R$)
          </p>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {loading ? (
          <p className="text-sm text-gray-500 py-6 text-center">Carregando...</p>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs text-gray-500">
                Ex.: Categoria Cabelo → Corte simples 40% ou R$ 25.
              </p>
              <button
                type="button"
                onClick={addRow}
                className="inline-flex items-center gap-1 text-xs font-medium shrink-0"
                style={{ color: SALAO_PRIMARY }}
              >
                <Plus size={14} /> Adicionar
              </button>
            </div>

            {categorias.length === 0 ? (
              <p className="text-sm text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
                Cadastre categorias e serviços em Serviços antes de configurar comissões.
              </p>
            ) : null}

            {rows.length === 0 ? (
              <p className="text-sm text-gray-400 italic py-4 text-center">
                Nenhuma comissão. Clique em Adicionar.
              </p>
            ) : (
              <div className="space-y-2 max-h-[50vh] overflow-y-auto pr-1">
                {rows.map((row, idx) => {
                  const svcs = servicosDaCategoria(row.categoria);
                  return (
                    <div
                      key={idx}
                      className="flex flex-wrap items-center gap-2 bg-[#F7F0F3] rounded-lg px-3 py-2.5"
                    >
                      <select
                        value={row.categoria === '' ? '' : String(row.categoria)}
                        onChange={(e) =>
                          updateRow(idx, {
                            categoria: e.target.value ? Number(e.target.value) : '',
                          })
                        }
                        className="flex-1 min-w-[140px] border rounded-lg px-2 py-2 text-sm bg-white"
                      >
                        <option value="">Categoria...</option>
                        {categorias.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.nome}
                          </option>
                        ))}
                      </select>
                      <select
                        value={row.servico === '' ? '' : String(row.servico)}
                        onChange={(e) =>
                          updateRow(idx, {
                            servico: e.target.value ? Number(e.target.value) : '',
                          })
                        }
                        disabled={row.categoria === ''}
                        className="flex-1 min-w-[160px] border rounded-lg px-2 py-2 text-sm bg-white disabled:opacity-50"
                      >
                        <option value="">
                          {row.categoria === ''
                            ? 'Escolha a categoria'
                            : svcs.length
                              ? 'Serviço...'
                              : 'Nenhum serviço nesta categoria'}
                        </option>
                        {svcs.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.nome}
                          </option>
                        ))}
                      </select>
                      <select
                        value={row.modo}
                        onChange={(e) =>
                          updateRow(idx, {
                            modo: e.target.value === 'fixo' ? 'fixo' : 'percentual',
                          })
                        }
                        className="w-24 border rounded-lg px-2 py-2 text-sm bg-white"
                      >
                        <option value="percentual">%</option>
                        <option value="fixo">R$</option>
                      </select>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={row.valor}
                        onChange={(e) => updateRow(idx, { valor: e.target.value })}
                        placeholder={row.modo === 'percentual' ? '40' : '25.00'}
                        className="w-24 border rounded-lg px-2 py-2 text-sm bg-white"
                      />
                      <button
                        type="button"
                        onClick={() => removeRow(idx)}
                        className="p-1.5 text-red-500 hover:bg-red-50 rounded"
                        title="Remover"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg text-sm">
            Cancelar
          </button>
          <button
            type="button"
            disabled={saving || loading}
            onClick={() => void save()}
            className="px-4 py-2 rounded-lg text-sm text-white disabled:opacity-60"
            style={{ backgroundColor: SALAO_PRIMARY }}
          >
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>
    </Modal>
  );
}
