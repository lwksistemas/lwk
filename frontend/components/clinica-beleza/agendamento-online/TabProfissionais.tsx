"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronUp, Loader2, Plus, Trash2 } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import {
  agendamentoOnlineAdminApi,
  mensagemErroAgendamentoOnline,
  type AgendamentoOnlineHorario,
  type AgendamentoOnlineProfissional,
} from "@/lib/clinica-beleza-api/agendamento-online";
import { DIAS_SEMANA } from "@/lib/agendamento-online-format";
import { PrimaryButton, SectionCard, Switch } from "./ui";

export function TabProfissionais({ primary }: { primary: string }) {
  const toast = useToast();
  const [itens, setItens] = useState<AgendamentoOnlineProfissional[]>([]);
  const [original, setOriginal] = useState<string>("[]");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [aberto, setAberto] = useState<number | null>(null);

  const carregar = useCallback(async () => {
    setLoading(true);
    try {
      const data = await agendamentoOnlineAdminApi.listProfissionais();
      setItens(data);
      setOriginal(JSON.stringify(data));
    } catch (err) {
      toast.error(mensagemErroAgendamentoOnline(err, "Não foi possível carregar os profissionais."));
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const dirty = useMemo(() => JSON.stringify(itens) !== original, [itens, original]);

  const atualizar = (id: number, patch: Partial<AgendamentoOnlineProfissional>) => {
    setItens((lista) => lista.map((p) => (p.professional_id === id ? { ...p, ...patch } : p)));
  };

  const atualizarHorario = (id: number, idx: number, patch: Partial<AgendamentoOnlineHorario>) => {
    setItens((lista) =>
      lista.map((p) =>
        p.professional_id === id
          ? { ...p, horarios: p.horarios.map((h, i) => (i === idx ? { ...h, ...patch } : h)) }
          : p,
      ),
    );
  };

  const adicionarHorario = (id: number) => {
    setItens((lista) =>
      lista.map((p) =>
        p.professional_id === id
          ? {
              ...p,
              usar_horarios_exclusivos: true,
              horarios: [...p.horarios, { dia_semana: 0, hora_inicio: "09:00", hora_fim: "12:00", ativo: true }],
            }
          : p,
      ),
    );
  };

  const removerHorario = (id: number, idx: number) => {
    setItens((lista) =>
      lista.map((p) =>
        p.professional_id === id ? { ...p, horarios: p.horarios.filter((_, i) => i !== idx) } : p,
      ),
    );
  };

  const salvar = async () => {
    for (const p of itens) {
      for (const h of p.horarios) {
        if (h.hora_fim <= h.hora_inicio) {
          toast.error(`${p.nome}: o horário final deve ser depois do inicial.`);
          setAberto(p.professional_id);
          return;
        }
      }
    }
    setSaving(true);
    try {
      const salvo = await agendamentoOnlineAdminApi.saveProfissionais(itens);
      setItens(salvo);
      setOriginal(JSON.stringify(salvo));
      toast.success("Profissionais salvos.");
    } catch (err) {
      toast.error(mensagemErroAgendamentoOnline(err, "Não foi possível salvar."));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-10 text-sm text-[#8a6e74]">
        <Loader2 className="h-4 w-4 animate-spin" /> Carregando profissionais…
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <SectionCard
        title="Profissionais no agendamento online"
        description="Libere quem aparece na página pública. Sem horários exclusivos, vale o horário de trabalho cadastrado."
      >
        {itens.length === 0 ? (
          <p className="text-sm text-[#8a6e74]">Nenhum profissional ativo. Cadastre em Configurações → Cadastrar profissionais.</p>
        ) : (
          <ul className="space-y-3">
            {itens.map((p) => {
              const expandido = aberto === p.professional_id;
              return (
                <li key={p.professional_id} className="rounded-2xl border border-[#f0e4e6] dark:border-gray-700">
                  <div className="flex flex-wrap items-center gap-3 px-3 py-3">
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-gray-900 dark:text-gray-100">{p.nome}</p>
                      <p className="truncate text-xs text-[#8a6e74]">{p.especialidade || "Sem especialidade"}</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-gray-700 dark:text-gray-300">
                      <span className="flex items-center gap-2">
                        Liberado
                        <Switch
                          label={`Liberar ${p.nome}`}
                          checked={p.liberado}
                          onChange={(v) => atualizar(p.professional_id, { liberado: v })}
                          primary={primary}
                        />
                      </span>
                      <span className="flex items-center gap-2">
                        Bloqueado
                        <Switch
                          label={`Bloquear ${p.nome} temporariamente`}
                          checked={p.bloqueado_temporariamente}
                          onChange={(v) => atualizar(p.professional_id, { bloqueado_temporariamente: v })}
                          primary="#dc2626"
                        />
                      </span>
                      <span className="flex items-center gap-2">
                        Horários exclusivos
                        <Switch
                          label={`Usar horários exclusivos de ${p.nome}`}
                          checked={p.usar_horarios_exclusivos}
                          onChange={(v) => atualizar(p.professional_id, { usar_horarios_exclusivos: v })}
                          primary={primary}
                        />
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setAberto(expandido ? null : p.professional_id)}
                      className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium hover:bg-[#fbf6f4]"
                      style={{ color: primary }}
                      aria-expanded={expandido}
                    >
                      Períodos ({p.horarios.length})
                      {expandido ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                  </div>

                  {expandido ? (
                    <div className="space-y-2 border-t border-[#f0e4e6] bg-[#fdfafa] px-3 py-3 dark:border-gray-700 dark:bg-gray-900/40">
                      {!p.usar_horarios_exclusivos ? (
                        <p className="text-xs text-[#8a6e74]">
                          Os períodos abaixo só valem com “Horários exclusivos” ligado. Hoje vale o horário de trabalho.
                        </p>
                      ) : null}
                      {p.horarios.length === 0 ? (
                        <p className="text-xs text-[#8a6e74]">Nenhum período cadastrado.</p>
                      ) : null}
                      {p.horarios.map((h, idx) => (
                        <div key={h.id ?? `n-${idx}`} className="flex flex-wrap items-center gap-2">
                          <select
                            aria-label="Dia da semana"
                            value={h.dia_semana}
                            onChange={(e) => atualizarHorario(p.professional_id, idx, { dia_semana: Number(e.target.value) })}
                            className="rounded-xl border border-[#e8d9dc] bg-white px-2 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-900"
                          >
                            {DIAS_SEMANA.map((d, i) => (
                              <option key={d} value={i}>
                                {d}
                              </option>
                            ))}
                          </select>
                          <input
                            type="time"
                            aria-label="Hora inicial"
                            value={h.hora_inicio}
                            onChange={(e) => atualizarHorario(p.professional_id, idx, { hora_inicio: e.target.value })}
                            className="rounded-xl border border-[#e8d9dc] bg-white px-2 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-900"
                          />
                          <span className="text-xs text-[#8a6e74]">até</span>
                          <input
                            type="time"
                            aria-label="Hora final"
                            value={h.hora_fim}
                            onChange={(e) => atualizarHorario(p.professional_id, idx, { hora_fim: e.target.value })}
                            className="rounded-xl border border-[#e8d9dc] bg-white px-2 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-900"
                          />
                          <label className="flex items-center gap-1.5 text-xs text-gray-700 dark:text-gray-300">
                            <input
                              type="checkbox"
                              checked={h.ativo}
                              onChange={(e) => atualizarHorario(p.professional_id, idx, { ativo: e.target.checked })}
                            />
                            Ativo
                          </label>
                          <button
                            type="button"
                            onClick={() => removerHorario(p.professional_id, idx)}
                            className="rounded-lg p-1.5 text-red-600 hover:bg-red-50"
                            aria-label="Remover período"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={() => adicionarHorario(p.professional_id)}
                        className="inline-flex items-center gap-1 text-xs font-semibold"
                        style={{ color: primary }}
                      >
                        <Plus className="h-4 w-4" /> Adicionar período
                      </button>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </SectionCard>

      <div className="flex items-center justify-end gap-3">
        {dirty ? <span className="text-xs text-[#8a6e74]">Alterações não salvas</span> : null}
        <PrimaryButton primary={primary} onClick={salvar} disabled={!dirty} loading={saving}>
          Salvar profissionais
        </PrimaryButton>
      </div>
    </div>
  );
}
