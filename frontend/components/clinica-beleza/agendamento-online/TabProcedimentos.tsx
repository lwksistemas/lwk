"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link2, Loader2, Pencil, Trash2, X } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import { cbGetList } from "@/lib/clinica-beleza-api/client-http";
import {
  agendamentoOnlineAdminApi,
  mensagemErroAgendamentoOnline,
  type AgendamentoOnlineProcedimento,
  type AgendamentoOnlineProfissional,
} from "@/lib/clinica-beleza-api/agendamento-online";
import { formatarDuracao, formatarPrecoBRL } from "@/lib/agendamento-online-format";
import { PrimaryButton, SecondaryButton, Switch } from "./ui";

type ProcedureOpt = {
  id: number;
  nome: string;
  categoria?: string;
  duracao_minutos?: number;
  preco?: string | number | null;
};

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={onClose}
    >
      <div
        className="max-h-[90dvh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-white p-5 shadow-xl dark:bg-gray-800 sm:rounded-3xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
          <button type="button" onClick={onClose} aria-label="Fechar" className="rounded-lg p-1 hover:bg-[#fbf6f4]">
            <X className="h-5 w-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function TabProcedimentos({ primary }: { primary: string }) {
  const toast = useToast();
  const [itens, setItens] = useState<AgendamentoOnlineProcedimento[]>([]);
  const [profissionais, setProfissionais] = useState<AgendamentoOnlineProfissional[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  const [vincularAberto, setVincularAberto] = useState(false);
  const [opcoes, setOpcoes] = useState<ProcedureOpt[]>([]);
  const [opcoesLoading, setOpcoesLoading] = useState(false);
  const [busca, setBusca] = useState("");
  const [vinculando, setVinculando] = useState<number | null>(null);

  const [editando, setEditando] = useState<AgendamentoOnlineProcedimento | null>(null);
  const [editProfs, setEditProfs] = useState<number[]>([]);
  const [salvandoProfs, setSalvandoProfs] = useState(false);

  const carregar = useCallback(async () => {
    setLoading(true);
    try {
      const [procs, profs] = await Promise.all([
        agendamentoOnlineAdminApi.listProcedimentos(),
        agendamentoOnlineAdminApi.listProfissionais().catch(() => [] as AgendamentoOnlineProfissional[]),
      ]);
      setItens(procs);
      setProfissionais(profs);
    } catch (err) {
      toast.error(mensagemErroAgendamentoOnline(err, "Não foi possível carregar os procedimentos."));
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const alternar = async (item: AgendamentoOnlineProcedimento, campo: "liberado" | "exibir_valor", valor: boolean) => {
    setBusyId(item.id);
    setItens((l) => l.map((i) => (i.id === item.id ? { ...i, [campo]: valor } : i)));
    try {
      const atualizado = await agendamentoOnlineAdminApi.patchProcedimento(item.id, { [campo]: valor });
      setItens((l) => l.map((i) => (i.id === item.id ? atualizado : i)));
    } catch (err) {
      setItens((l) => l.map((i) => (i.id === item.id ? item : i)));
      toast.error(mensagemErroAgendamentoOnline(err, "Não foi possível atualizar."));
    } finally {
      setBusyId(null);
    }
  };

  const desvincular = async (item: AgendamentoOnlineProcedimento) => {
    if (!window.confirm(`Remover “${item.nome}” do agendamento online? O procedimento continua cadastrado na clínica.`)) return;
    setBusyId(item.id);
    try {
      await agendamentoOnlineAdminApi.desvincularProcedimento(item.id);
      setItens((l) => l.filter((i) => i.id !== item.id));
      toast.success("Procedimento desvinculado.");
    } catch (err) {
      toast.error(mensagemErroAgendamentoOnline(err, "Não foi possível desvincular."));
    } finally {
      setBusyId(null);
    }
  };

  const abrirVincular = async () => {
    setVincularAberto(true);
    setBusca("");
    setOpcoesLoading(true);
    try {
      const lista = await cbGetList<ProcedureOpt>("/procedures/", { active: true, all: 1 });
      setOpcoes(lista);
    } catch (err) {
      toast.error(mensagemErroAgendamentoOnline(err, "Não foi possível carregar os procedimentos."));
    } finally {
      setOpcoesLoading(false);
    }
  };

  const vinculadosIds = useMemo(() => new Set(itens.map((i) => i.procedure_id)), [itens]);
  const opcoesFiltradas = useMemo(() => {
    const q = busca.trim().toLowerCase();
    return opcoes.filter((o) => !vinculadosIds.has(o.id) && (!q || o.nome.toLowerCase().includes(q)));
  }, [opcoes, vinculadosIds, busca]);

  const vincular = async (opt: ProcedureOpt) => {
    setVinculando(opt.id);
    try {
      const criado = await agendamentoOnlineAdminApi.vincularProcedimento(opt.id);
      setItens((l) => [...l, criado]);
      toast.success(`“${opt.nome}” vinculado.`);
    } catch (err) {
      toast.error(mensagemErroAgendamentoOnline(err, "Não foi possível vincular."));
    } finally {
      setVinculando(null);
    }
  };

  const abrirEditarProfs = (item: AgendamentoOnlineProcedimento) => {
    setEditando(item);
    setEditProfs(item.profissionais);
  };

  const salvarProfs = async () => {
    if (!editando) return;
    setSalvandoProfs(true);
    try {
      const atualizado = await agendamentoOnlineAdminApi.patchProcedimento(editando.id, { profissionais: editProfs });
      setItens((l) => l.map((i) => (i.id === editando.id ? atualizado : i)));
      setEditando(null);
      toast.success("Profissionais atualizados.");
    } catch (err) {
      toast.error(mensagemErroAgendamentoOnline(err, "Não foi possível salvar."));
    } finally {
      setSalvandoProfs(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-xl text-sm text-[#8a6e74] dark:text-gray-400">
          Escolha quais procedimentos o cliente vê na página pública. Desvincular não exclui o procedimento da clínica.
        </p>
        <PrimaryButton primary={primary} onClick={abrirVincular}>
          <Link2 className="h-4 w-4" /> Vincular procedimento
        </PrimaryButton>
      </div>

      <div className="overflow-x-auto rounded-3xl border border-[#f0e4e6] bg-white dark:border-gray-700 dark:bg-gray-800">
        {loading ? (
          <div className="flex items-center gap-2 p-6 text-sm text-[#8a6e74]">
            <Loader2 className="h-4 w-4 animate-spin" /> Carregando…
          </div>
        ) : itens.length === 0 ? (
          <p className="p-6 text-sm text-[#8a6e74]">Nenhum procedimento vinculado ainda. Use “Vincular procedimento”.</p>
        ) : (
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-pink-50 text-xs uppercase tracking-wide text-[#8a6e74] dark:bg-gray-900/50">
              <tr>
                <th className="px-3 py-2.5 font-semibold">Procedimento</th>
                <th className="px-3 py-2.5 font-semibold">Categoria</th>
                <th className="px-3 py-2.5 font-semibold">Duração</th>
                <th className="px-3 py-2.5 font-semibold">Valor</th>
                <th className="px-3 py-2.5 font-semibold">Profissionais</th>
                <th className="px-3 py-2.5 text-center font-semibold">Liberar online</th>
                <th className="px-3 py-2.5 text-center font-semibold">Exibir valor</th>
                <th className="px-3 py-2.5 text-right font-semibold">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f0e4e6] dark:divide-gray-700">
              {itens.map((i) => (
                <tr key={i.id} className={busyId === i.id ? "opacity-60" : ""}>
                  <td className="px-3 py-2.5 font-medium text-gray-900 dark:text-gray-100">{i.nome}</td>
                  <td className="px-3 py-2.5 text-gray-700 dark:text-gray-300">{i.categoria || "—"}</td>
                  <td className="px-3 py-2.5 text-gray-700 dark:text-gray-300">{formatarDuracao(i.duracao_minutos)}</td>
                  <td className="px-3 py-2.5 text-gray-700 dark:text-gray-300">{formatarPrecoBRL(i.preco) || "—"}</td>
                  <td className="px-3 py-2.5 text-gray-700 dark:text-gray-300">
                    {i.profissionais_nomes.length ? i.profissionais_nomes.join(", ") : "Todos liberados"}
                  </td>
                  <td className="px-3 py-2.5">
                    <div className="flex justify-center">
                      <Switch
                        label={`Liberar ${i.nome} online`}
                        checked={i.liberado}
                        onChange={(v) => alternar(i, "liberado", v)}
                        primary={primary}
                        disabled={busyId === i.id}
                      />
                    </div>
                  </td>
                  <td className="px-3 py-2.5">
                    <div className="flex justify-center">
                      <Switch
                        label={`Exibir valor de ${i.nome}`}
                        checked={i.exibir_valor}
                        onChange={(v) => alternar(i, "exibir_valor", v)}
                        primary={primary}
                        disabled={busyId === i.id}
                      />
                    </div>
                  </td>
                  <td className="px-3 py-2.5">
                    <div className="flex justify-end gap-1">
                      <button
                        type="button"
                        onClick={() => abrirEditarProfs(i)}
                        className="rounded-lg p-1.5 hover:bg-[#fbf6f4]"
                        aria-label={`Escolher profissionais de ${i.nome}`}
                        title="Escolher profissionais"
                        style={{ color: primary }}
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => desvincular(i)}
                        className="rounded-lg p-1.5 text-red-600 hover:bg-red-50"
                        aria-label={`Desvincular ${i.nome}`}
                        title="Desvincular"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {vincularAberto ? (
        <Modal title="Vincular procedimento" onClose={() => setVincularAberto(false)}>
          <input
            autoFocus
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar procedimento…"
            className="mb-3 w-full rounded-xl border border-[#e8d9dc] px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-900"
          />
          {opcoesLoading ? (
            <div className="flex items-center gap-2 py-6 text-sm text-[#8a6e74]">
              <Loader2 className="h-4 w-4 animate-spin" /> Carregando…
            </div>
          ) : opcoesFiltradas.length === 0 ? (
            <p className="py-6 text-sm text-[#8a6e74]">Nenhum procedimento disponível para vincular.</p>
          ) : (
            <ul className="max-h-[50dvh] divide-y divide-[#f0e4e6] overflow-y-auto rounded-2xl border border-[#f0e4e6]">
              {opcoesFiltradas.map((o) => (
                <li key={o.id} className="flex items-center justify-between gap-3 px-3 py-2.5">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">{o.nome}</p>
                    <p className="text-xs text-[#8a6e74]">
                      {[o.categoria, formatarDuracao(Number(o.duracao_minutos || 0)), formatarPrecoBRL(o.preco)]
                        .filter((x) => x && x !== "—")
                        .join(" · ")}
                    </p>
                  </div>
                  <PrimaryButton primary={primary} onClick={() => vincular(o)} loading={vinculando === o.id}>
                    Vincular
                  </PrimaryButton>
                </li>
              ))}
            </ul>
          )}
        </Modal>
      ) : null}

      {editando ? (
        <Modal title={`Profissionais — ${editando.nome}`} onClose={() => setEditando(null)}>
          <p className="mb-3 text-xs text-[#8a6e74]">
            Nenhum marcado = todos os profissionais liberados online atendem este procedimento.
          </p>
          <ul className="max-h-[50dvh] space-y-1 overflow-y-auto">
            {profissionais.map((p) => (
              <li key={p.professional_id}>
                <label className="flex cursor-pointer items-center gap-2 rounded-xl px-2 py-1.5 text-sm hover:bg-[#fbf6f4]">
                  <input
                    type="checkbox"
                    checked={editProfs.includes(p.professional_id)}
                    onChange={(e) =>
                      setEditProfs((l) =>
                        e.target.checked ? [...l, p.professional_id] : l.filter((x) => x !== p.professional_id),
                      )
                    }
                  />
                  <span>{p.nome}</span>
                  {!p.liberado ? <span className="text-xs text-[#8a6e74]">(não liberado online)</span> : null}
                </label>
              </li>
            ))}
          </ul>
          <div className="mt-4 flex justify-end gap-2">
            <SecondaryButton onClick={() => setEditando(null)}>Cancelar</SecondaryButton>
            <PrimaryButton primary={primary} onClick={salvarProfs} loading={salvandoProfs}>
              Salvar
            </PrimaryButton>
          </div>
        </Modal>
      ) : null}
    </div>
  );
}
