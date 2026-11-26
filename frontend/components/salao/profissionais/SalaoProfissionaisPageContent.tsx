"use client";

import { useCallback, useEffect, useState, type Dispatch, type FormEvent, type SetStateAction } from "react";
import { CalendarClock, Scissors, Timer } from "lucide-react";
import { AppPageContent, AppPanel } from "@/components/shared/layout/PageContent";
import { EntityListTable, type EntityListColumn } from "@/components/shared/layout/EntityListTable";
import { StandardPageHeader } from "@/components/shared/layout/StandardPageHeader";
import { useFormRouting } from "@/hooks/shared/useFormRouting";
import { INTERVALOS_AGENDA_MIN, INTERVALO_AGENDA_PADRAO, intervaloAgendaMinutos } from "@/lib/intervalo-agenda";
import { SalaoAPI, type JornadaDia, type ProfissionalSalao, type ServicoSalao } from "@/lib/salao-api";

const DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];
const CAMPO = "w-full rounded-lg border px-2 py-2";
const VAZIO = {
  nome: "",
  telefone: "",
  especialidade: "Cabeleireiro",
  comissao_tipo: "percentual",
  comissao_percentual: "0",
  comissao_fixa: "0",
  intervalo_agenda_minutos: String(INTERVALO_AGENDA_PADRAO),
};

type Regra = { servico: number; nome: string; tipo: "percentual" | "fixo"; valor: string };

export function SalaoProfissionaisPageContent() {
  const { isNovo, editId, isFormView, voltarLista, abrirNovo, abrirEditar } = useFormRouting();
  const [lista, setLista] = useState<ProfissionalSalao[]>([]);
  const [servicos, setServicos] = useState<ServicoSalao[]>([]);
  const [regras, setRegras] = useState<Regra[]>([]);
  const [form, setForm] = useState(VAZIO);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [jornadaModalId, setJornadaModalId] = useState<number | null>(null);
  const [intervaloModalId, setIntervaloModalId] = useState<number | null>(null);

  const carregar = useCallback(() => {
    Promise.all([SalaoAPI.profissionais(), SalaoAPI.servicos()])
      .then(([pessoas, procedimentos]) => {
        setLista(pessoas);
        setServicos(procedimentos);
      })
      .catch((exc: Error) => setErro(exc.message));
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  useEffect(() => {
    if (!isFormView) {
      setForm(VAZIO);
      setRegras([]);
      setErro("");
      setAviso("");
      return;
    }
    if (isNovo || !editId) {
      setForm(VAZIO);
      setRegras(montarRegras(servicos, []));
      setErro("");
      setAviso("");
      return;
    }
    let ativo = true;
    Promise.all([SalaoAPI.profissionais(), SalaoAPI.servicos()])
      .then(([pessoas, procedimentos]) => {
        if (!ativo) return;
        setLista(pessoas);
        setServicos(procedimentos);
        const item = pessoas.find((p) => p.id === editId);
        if (!item) {
          setErro("Profissional não encontrado.");
          return;
        }
        setForm({
          nome: item.nome,
          telefone: item.telefone,
          especialidade: item.especialidade,
          comissao_tipo: item.comissao_tipo || "percentual",
          comissao_percentual: String(item.comissao_percentual),
          comissao_fixa: String(item.comissao_fixa || "0"),
          intervalo_agenda_minutos: String(intervaloAgendaMinutos(item)),
        });
        setRegras(montarRegras(procedimentos, item.comissoes, item.comissao_tipo || "percentual"));
        setErro("");
        setAviso("");
      })
      .catch((exc: Error) => {
        if (ativo) setErro(exc.message);
      });
    return () => {
      ativo = false;
    };
  }, [isFormView, isNovo, editId]);

  async function salvar(evento: FormEvent) {
    evento.preventDefault();
    setErro("");
    setAviso("");
    try {
      const corpo = {
        ...form,
        comissao_percentual: form.comissao_percentual.replace(",", "."),
        comissao_fixa: form.comissao_fixa.replace(",", "."),
        intervalo_agenda_minutos: Number(form.intervalo_agenda_minutos),
        comissoes: regras
          .filter((regra) => regra.valor.trim() !== "")
          .map((regra) => ({
            servico: regra.servico,
            tipo: regra.tipo,
            valor: regra.valor.replace(",", "."),
          })),
      };
      await SalaoAPI.salvarProfissional(corpo, editId ?? undefined);
      carregar();
      voltarLista();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível salvar.");
    }
  }

  async function arquivar() {
    if (!editId) return;
    setErro("");
    try {
      await SalaoAPI.arquivar(`/profissionais/${editId}/`);
      carregar();
      voltarLista();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível arquivar.");
    }
  }

  const columns: EntityListColumn<ProfissionalSalao>[] = [
    { key: "nome", header: "Nome", render: (row) => <span className="font-medium">{row.nome}</span> },
    { key: "especialidade", header: "Função", render: (row) => row.especialidade },
    { key: "telefone", header: "Telefone", render: (row) => row.telefone },
    {
      key: "comissao",
      header: "Comissão",
      render: (row) => `${rotuloComissao(row)} · ${intervaloAgendaMinutos(row)} min`,
    },
  ];

  if (isFormView) {
    return (
      <AppPageContent>
        <StandardPageHeader
          title={editId ? "Editar profissional" : "Novo profissional"}
          subtitle="Dados e comissões. Jornada e intervalo da agenda ficam na lista."
          icon={Scissors}
          onBack={voltarLista}
          showBack
        />
        <AppPanel className="p-4 sm:p-6">
          {erro ? <p className="mb-3 text-sm text-red-700">{erro}</p> : null}
          {aviso ? <p className="mb-3 text-sm text-[#1f8a4c]">{aviso}</p> : null}
          <form onSubmit={salvar}>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-sm">Nome
                <input className={`mt-1 ${CAMPO}`} value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
              </label>
              <label className="text-sm">Telefone
                <input className={`mt-1 ${CAMPO}`} value={form.telefone} onChange={(e) => setForm({ ...form, telefone: e.target.value })} required />
              </label>
              <label className="text-sm">Função
                <input className={`mt-1 ${CAMPO}`} value={form.especialidade} onChange={(e) => setForm({ ...form, especialidade: e.target.value })} />
              </label>
              <label className="text-sm">Comissão padrão
                <select
                  className={`mt-1 ${CAMPO}`}
                  value={form.comissao_tipo}
                  onChange={(e) => {
                    const tipo = e.target.value === "fixo" ? "fixo" : "percentual";
                    setForm({ ...form, comissao_tipo: tipo });
                    setRegras((atual) => atual.map((regra) => (regra.valor.trim() ? regra : { ...regra, tipo })));
                  }}
                >
                  <option value="percentual">Porcentagem</option>
                  <option value="fixo">Valor fixo</option>
                </select>
              </label>
              <label className="text-sm">{form.comissao_tipo === "fixo" ? "Valor fixo (R$)" : "Porcentagem"}
                <input
                  className={`mt-1 ${CAMPO}`}
                  value={form.comissao_tipo === "fixo" ? form.comissao_fixa : form.comissao_percentual}
                  onChange={(e) =>
                    setForm(
                      form.comissao_tipo === "fixo"
                        ? { ...form, comissao_fixa: e.target.value }
                        : { ...form, comissao_percentual: e.target.value },
                    )
                  }
                />
              </label>
              <label className="text-sm">Intervalo por atendimento
                <select
                  className={`mt-1 ${CAMPO}`}
                  value={form.intervalo_agenda_minutos}
                  onChange={(e) => setForm({ ...form, intervalo_agenda_minutos: e.target.value })}
                >
                  {INTERVALOS_AGENDA_MIN.map((minutos) => (
                    <option key={minutos} value={minutos}>{minutos} minutos</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="mt-5">
              <h3 className="text-sm font-medium">Comissão por procedimento</h3>
              <p className="mt-1 text-xs text-[#8a6e74]">Em branco, o procedimento usa a comissão padrão.</p>
              <div className="mt-2 space-y-2">
                {regras.map((regra, indice) => (
                  <div key={regra.servico} className="grid grid-cols-[1fr_9rem_7rem] items-center gap-2 text-sm">
                    <span>{regra.nome}</span>
                    <select
                      className={CAMPO}
                      value={regra.tipo}
                      onChange={(e) => alterarRegra(setRegras, indice, { tipo: e.target.value as Regra["tipo"] })}
                    >
                      <option value="percentual">Porcentagem</option>
                      <option value="fixo">Valor fixo</option>
                    </select>
                    <input
                      className={CAMPO}
                      value={regra.valor}
                      placeholder={form.comissao_tipo === "fixo" ? form.comissao_fixa : form.comissao_percentual}
                      onChange={(e) => alterarRegra(setRegras, indice, { valor: e.target.value })}
                    />
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-6 flex flex-wrap items-center justify-end gap-2">
              {editId ? <button type="button" className="mr-auto rounded-full border px-4 py-2 text-sm" onClick={arquivar}>Arquivar</button> : null}
              <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={voltarLista}>Cancelar</button>
              <button className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" type="submit">Salvar</button>
            </div>
          </form>
        </AppPanel>
      </AppPageContent>
    );
  }

  return (
    <AppPageContent>
      <StandardPageHeader
        title="Profissionais"
        subtitle="A jornada padrão é de segunda a sábado, das 9h às 19h. Domingo começa como folga."
        icon={Scissors}
        newLabel="Novo profissional"
        onNew={abrirNovo}
      />
      {erro ? <p className="mb-3 text-sm text-red-700">{erro}</p> : null}
      <AppPanel>
        <EntityListTable
          columns={columns}
          rows={lista}
          rowKey={(row) => row.id}
          onRowClick={(row) => abrirEditar(row.id)}
          emptyMessage={<p className="px-4 py-8 text-sm text-[#8a6e74]">Nenhum profissional cadastrado.</p>}
          trailingCell={(row) => (
            <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
              <button
                type="button"
                className="rounded-lg p-1.5 text-[#7a3044] hover:bg-[#f5e6ea]"
                title="Jornada"
                onClick={() => setJornadaModalId(row.id)}
              >
                <CalendarClock className="h-4 w-4" />
              </button>
              <button
                type="button"
                className="rounded-lg p-1.5 text-[#7a3044] hover:bg-[#f5e6ea]"
                title="Intervalo da agenda"
                onClick={() => setIntervaloModalId(row.id)}
              >
                <Timer className="h-4 w-4" />
              </button>
            </div>
          )}
        />
      </AppPanel>
      {jornadaModalId != null ? (
        <ModalJornada
          profissionalId={jornadaModalId}
          nome={lista.find((p) => p.id === jornadaModalId)?.nome || ""}
          onClose={() => setJornadaModalId(null)}
          onErro={setErro}
        />
      ) : null}
      {intervaloModalId != null && lista.some((p) => p.id === intervaloModalId) ? (
        <ModalIntervalo
          profissional={lista.find((p) => p.id === intervaloModalId)!}
          onClose={() => setIntervaloModalId(null)}
          onSalvo={() => {
            setIntervaloModalId(null);
            carregar();
          }}
          onErro={setErro}
        />
      ) : null}
    </AppPageContent>
  );
}

function ModalJornada({
  profissionalId,
  nome,
  onClose,
  onErro,
}: {
  profissionalId: number;
  nome: string;
  onClose: () => void;
  onErro: (msg: string) => void;
}) {
  const [jornada, setJornada] = useState<JornadaDia[]>([]);
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    SalaoAPI.jornada(profissionalId)
      .then(setJornada)
      .catch((exc: Error) => onErro(exc.message));
  }, [profissionalId, onErro]);

  async function salvar() {
    setSalvando(true);
    try {
      await SalaoAPI.salvarJornada(profissionalId, jornada);
      onClose();
    } catch (exc) {
      onErro(exc instanceof Error ? exc.message : "Não foi possível salvar a jornada.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="max-h-[90vh] w-full max-w-3xl overflow-auto rounded-2xl bg-white p-5">
        <h2 className="text-lg font-semibold">Jornada — {nome}</h2>
        <p className="mt-1 text-xs text-[#8a6e74]">Entrada, saída e, se houver, começo e fim do intervalo.</p>
        {jornada.length === 7 ? (
          <div className="mt-4 min-w-[640px] space-y-2 overflow-auto">
            {jornada.map((dia, indice) => (
              <div key={dia.dia_semana} className="grid grid-cols-[7rem_4rem_1fr_1fr_1fr_1fr] items-center gap-2 text-sm">
                <span>{DIAS[dia.dia_semana]}</span>
                <label className="flex items-center gap-1 text-xs">
                  <input type="checkbox" checked={dia.ativo} onChange={(e) => alterarDia(setJornada, indice, { ativo: e.target.checked })} />
                  Atende
                </label>
                <input type="time" className={CAMPO} value={dia.hora_entrada} disabled={!dia.ativo} onChange={(e) => alterarDia(setJornada, indice, { hora_entrada: e.target.value })} />
                <input type="time" className={CAMPO} value={dia.hora_saida} disabled={!dia.ativo} onChange={(e) => alterarDia(setJornada, indice, { hora_saida: e.target.value })} />
                <input type="time" className={CAMPO} value={dia.intervalo_inicio} disabled={!dia.ativo} onChange={(e) => alterarDia(setJornada, indice, { intervalo_inicio: e.target.value })} />
                <input type="time" className={CAMPO} value={dia.intervalo_fim} disabled={!dia.ativo} onChange={(e) => alterarDia(setJornada, indice, { intervalo_fim: e.target.value })} />
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm text-[#8a6e74]">Carregando jornada…</p>
        )}
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={onClose}>Fechar</button>
          <button type="button" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" disabled={salvando || jornada.length !== 7} onClick={salvar}>
            {salvando ? "Salvando…" : "Salvar"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ModalIntervalo({
  profissional,
  onClose,
  onSalvo,
  onErro,
}: {
  profissional: ProfissionalSalao;
  onClose: () => void;
  onSalvo: () => void;
  onErro: (msg: string) => void;
}) {
  const [valor, setValor] = useState(String(intervaloAgendaMinutos(profissional)));
  const [salvando, setSalvando] = useState(false);

  async function salvar() {
    setSalvando(true);
    try {
      await SalaoAPI.salvarProfissional(
        {
          nome: profissional.nome,
          telefone: profissional.telefone,
          especialidade: profissional.especialidade,
          comissao_tipo: profissional.comissao_tipo || "percentual",
          comissao_percentual: String(profissional.comissao_percentual),
          comissao_fixa: String(profissional.comissao_fixa || "0"),
          intervalo_agenda_minutos: Number(valor),
          comissoes: (profissional.comissoes || []).map((c) => ({
            servico: c.servico,
            tipo: c.tipo,
            valor: c.valor,
          })),
        },
        profissional.id,
      );
      onSalvo();
    } catch (exc) {
      onErro(exc instanceof Error ? exc.message : "Não foi possível salvar o intervalo.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="w-full max-w-md rounded-2xl bg-white p-5">
        <h2 className="text-lg font-semibold">Intervalo da agenda — {profissional.nome}</h2>
        <p className="mt-1 text-xs text-[#8a6e74]">Passo entre um horário e o outro na agenda deste profissional.</p>
        <label className="mt-4 block text-sm">Minutos
          <select className={`mt-1 ${CAMPO}`} value={valor} onChange={(e) => setValor(e.target.value)}>
            {INTERVALOS_AGENDA_MIN.map((minutos) => (
              <option key={minutos} value={minutos}>{minutos} minutos</option>
            ))}
          </select>
        </label>
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={onClose}>Fechar</button>
          <button type="button" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" disabled={salvando} onClick={salvar}>
            {salvando ? "Salvando…" : "Salvar"}
          </button>
        </div>
      </div>
    </div>
  );
}

function montarRegras(
  procedimentos: ServicoSalao[],
  gravadas: ProfissionalSalao["comissoes"] = [],
  tipoPadrao: Regra["tipo"] = "percentual",
) {
  return procedimentos.map((servico) => {
    const atual = gravadas.find((item) => item.servico === servico.id);
    return { servico: servico.id, nome: servico.nome, tipo: atual?.tipo || tipoPadrao, valor: atual ? atual.valor : "" };
  });
}

function rotuloComissao(item: ProfissionalSalao) {
  const padrao = item.comissao_tipo === "fixo" ? `R$ ${item.comissao_fixa}` : `${item.comissao_percentual}%`;
  return item.comissoes?.length ? `${padrao} · por procedimento` : padrao;
}

function alterarRegra(setRegras: Dispatch<SetStateAction<Regra[]>>, indice: number, parcial: Partial<Regra>) {
  setRegras((atual) => atual.map((regra, posicao) => (posicao === indice ? { ...regra, ...parcial } : regra)));
}

function alterarDia(setJornada: Dispatch<SetStateAction<JornadaDia[]>>, indice: number, parcial: Partial<JornadaDia>) {
  setJornada((atual) => atual.map((dia, posicao) => (posicao === indice ? { ...dia, ...parcial } : dia)));
}
