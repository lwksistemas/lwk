"use client";

import { useEffect, useState, type Dispatch, type FormEvent, type SetStateAction } from "react";
import { INTERVALOS_AGENDA_MIN, INTERVALO_AGENDA_PADRAO, intervaloAgendaMinutos } from "@/lib/intervalo-agenda";
import { SalaoAPI, type JornadaDia, type ProfissionalSalao, type ServicoSalao } from "@/lib/salao-api";

const DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];
const CAMPO = "w-full rounded-lg border px-2 py-2";
const VAZIO = { nome: "", telefone: "", especialidade: "Cabeleireiro", comissao_tipo: "percentual", comissao_percentual: "0", comissao_fixa: "0", intervalo_agenda_minutos: String(INTERVALO_AGENDA_PADRAO) };

type Regra = { servico: number; nome: string; tipo: "percentual" | "fixo"; valor: string };

export default function ProfissionaisSalaoPage() {
  const [lista, setLista] = useState<ProfissionalSalao[]>([]);
  const [servicos, setServicos] = useState<ServicoSalao[]>([]);
  const [regras, setRegras] = useState<Regra[]>([]);
  const [escolhido, setEscolhido] = useState<number | null>(null);
  const [form, setForm] = useState(VAZIO);
  const [jornada, setJornada] = useState<JornadaDia[]>([]);
  const [aberto, setAberto] = useState(false);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");

  function carregar() {
    Promise.all([SalaoAPI.profissionais(), SalaoAPI.servicos()])
      .then(([pessoas, procedimentos]) => {
        setLista(pessoas);
        setServicos(procedimentos);
      })
      .catch((exc: Error) => setErro(exc.message));
  }
  useEffect(() => { carregar(); }, []);

  async function abrir(item: ProfissionalSalao) {
    setErro("");
    setAviso("");
    setEscolhido(item.id);
    setForm({
      nome: item.nome,
      telefone: item.telefone,
      especialidade: item.especialidade,
      comissao_tipo: item.comissao_tipo || "percentual",
      comissao_percentual: String(item.comissao_percentual),
      comissao_fixa: String(item.comissao_fixa || "0"),
      intervalo_agenda_minutos: String(intervaloAgendaMinutos(item)),
    });
    setRegras(montarRegras(servicos, item.comissoes, item.comissao_tipo || "percentual"));
    setJornada([]);
    setAberto(true);
    setJornada(await SalaoAPI.jornada(item.id));
  }

  function novo() {
    setEscolhido(null);
    setForm(VAZIO);
    setRegras(montarRegras(servicos, []));
    setJornada([]);
    setErro("");
    setAviso("");
    setAberto(true);
  }

  function fechar() {
    setAberto(false);
    setEscolhido(null);
    setForm(VAZIO);
    setRegras([]);
    setJornada([]);
    setErro("");
    setAviso("");
  }

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
        comissoes: regras.filter((regra) => regra.valor.trim() !== "").map((regra) => ({
          servico: regra.servico,
          tipo: regra.tipo,
          valor: regra.valor.replace(",", "."),
        })),
      };
      const salvo = await SalaoAPI.salvarProfissional(corpo, escolhido ?? undefined);
      if (jornada.length === 7) await SalaoAPI.salvarJornada(salvo.id, jornada);
      setEscolhido(salvo.id);
      setJornada(await SalaoAPI.jornada(salvo.id));
      setAviso("Profissional gravado.");
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível salvar.");
    }
  }

  async function arquivar() {
    if (!escolhido) return;
    setErro("");
    try {
      await SalaoAPI.arquivar(`/profissionais/${escolhido}/`);
      fechar();
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível arquivar.");
    }
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold sm:text-3xl">Profissionais</h1>
          <p className="text-sm text-[#8a6e74]">A jornada padrão é de segunda a sábado, das 9h às 19h. Domingo começa como folga.</p>
        </div>
        <button type="button" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" onClick={novo}>Novo profissional</button>
      </div>
      {!aberto && erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      {lista.length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum profissional cadastrado.</p> : null}
      <ul className="grid gap-3 md:grid-cols-2">
        {lista.map((item) => (
          <li key={item.id}>
            <button type="button" className="flex h-full w-full items-start justify-between gap-3 rounded-3xl border border-[#f0e4e6] bg-white px-4 py-3 text-left hover:bg-[#fbf6f4]" onClick={() => abrir(item)}>
              <span>
                <span className="block font-medium">{item.nome}</span>
                <span className="mt-0.5 block text-sm text-[#8a6e74]">{item.especialidade} · {rotuloComissao(item)} · intervalo {intervaloAgendaMinutos(item)} min</span>
              </span>
              <span className="shrink-0 text-sm text-[#8a6e74]">{item.telefone}</span>
            </button>
          </li>
        ))}
      </ul>
      {aberto ? (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="profissional-formulario" onClick={(evento) => { if (evento.target === evento.currentTarget) fechar(); }}>
          <div className="max-h-[90vh] w-full max-w-4xl overflow-auto rounded-3xl bg-white p-5">
            <h2 id="profissional-formulario" className="mb-3 text-lg font-semibold">{escolhido ? "Editar profissional" : "Novo profissional"}</h2>
            {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
            {aviso ? <p className="mb-2 text-sm text-[#1f8a4c]">{aviso}</p> : null}
            <form onSubmit={salvar}>
              <div className="grid gap-2 sm:grid-cols-2">
                <label className="text-sm">Nome
                  <input className={`mt-1 ${CAMPO}`} value={form.nome} onChange={(evento) => setForm({ ...form, nome: evento.target.value })} required />
                </label>
                <label className="text-sm">Telefone
                  <input className={`mt-1 ${CAMPO}`} value={form.telefone} onChange={(evento) => setForm({ ...form, telefone: evento.target.value })} required />
                </label>
                <label className="text-sm">Função
                  <input className={`mt-1 ${CAMPO}`} value={form.especialidade} onChange={(evento) => setForm({ ...form, especialidade: evento.target.value })} />
                </label>
                <label className="text-sm">Comissão padrão
                  <select className={`mt-1 ${CAMPO}`} value={form.comissao_tipo} onChange={(evento) => {
                    const tipo = evento.target.value === "fixo" ? "fixo" : "percentual";
                    setForm({ ...form, comissao_tipo: tipo });
                    setRegras((atual) => atual.map((regra) => regra.valor.trim() ? regra : { ...regra, tipo }));
                  }}>
                    <option value="percentual">Porcentagem</option>
                    <option value="fixo">Valor fixo</option>
                  </select>
                </label>
                <label className="text-sm">{form.comissao_tipo === "fixo" ? "Valor fixo (R$)" : "Porcentagem"}
                  <input className={`mt-1 ${CAMPO}`} value={form.comissao_tipo === "fixo" ? form.comissao_fixa : form.comissao_percentual} onChange={(evento) => setForm(form.comissao_tipo === "fixo" ? { ...form, comissao_fixa: evento.target.value } : { ...form, comissao_percentual: evento.target.value })} />
                </label>
                <label className="text-sm">Intervalo por atendimento
                  <select className={`mt-1 ${CAMPO}`} value={form.intervalo_agenda_minutos} onChange={(evento) => setForm({ ...form, intervalo_agenda_minutos: evento.target.value })}>
                    {INTERVALOS_AGENDA_MIN.map((minutos) => <option key={minutos} value={minutos}>{minutos} minutos</option>)}
                  </select>
                  <span className="mt-1 block text-xs text-[#8a6e74]">Passo entre um horário e o outro na agenda deste profissional.</span>
                </label>
              </div>
              <div className="mt-4">
                <h3 className="text-sm font-medium">Comissão por procedimento</h3>
                <p className="mt-1 text-xs text-[#8a6e74]">Em branco, o procedimento usa a comissão padrão. Exemplo: Barba em valor fixo e Corte masculino em porcentagem.</p>
                <div className="mt-2 space-y-2">
                  {regras.map((regra, indice) => (
                    <div key={regra.servico} className="grid grid-cols-[1fr_9rem_7rem] items-center gap-2 text-sm">
                      <span>{regra.nome}</span>
                      <select className={CAMPO} value={regra.tipo} onChange={(evento) => alterarRegra(setRegras, indice, { tipo: evento.target.value as Regra["tipo"] })}>
                        <option value="percentual">Porcentagem</option>
                        <option value="fixo">Valor fixo</option>
                      </select>
                      <input className={CAMPO} value={regra.valor} placeholder={form.comissao_tipo === "fixo" ? form.comissao_fixa : form.comissao_percentual} onChange={(evento) => alterarRegra(setRegras, indice, { valor: evento.target.value })} />
                    </div>
                  ))}
                </div>
              </div>
              {escolhido && jornada.length === 7 ? (
                <div className="mt-4 overflow-auto">
                  <h3 className="mb-2 text-sm font-medium">Jornada</h3>
                  <div className="min-w-[640px] space-y-2">
                    {jornada.map((dia, indice) => (
                      <div key={dia.dia_semana} className="grid grid-cols-[7rem_4rem_1fr_1fr_1fr_1fr] items-center gap-2 text-sm">
                        <span>{DIAS[dia.dia_semana]}</span>
                        <label className="flex items-center gap-1 text-xs">
                          <input type="checkbox" checked={dia.ativo} onChange={(evento) => alterarDia(setJornada, indice, { ativo: evento.target.checked })} />
                          Atende
                        </label>
                        <input type="time" className={CAMPO} value={dia.hora_entrada} disabled={!dia.ativo} onChange={(evento) => alterarDia(setJornada, indice, { hora_entrada: evento.target.value })} />
                        <input type="time" className={CAMPO} value={dia.hora_saida} disabled={!dia.ativo} onChange={(evento) => alterarDia(setJornada, indice, { hora_saida: evento.target.value })} />
                        <input type="time" className={CAMPO} value={dia.intervalo_inicio} disabled={!dia.ativo} onChange={(evento) => alterarDia(setJornada, indice, { intervalo_inicio: evento.target.value })} />
                        <input type="time" className={CAMPO} value={dia.intervalo_fim} disabled={!dia.ativo} onChange={(evento) => alterarDia(setJornada, indice, { intervalo_fim: evento.target.value })} />
                      </div>
                    ))}
                  </div>
                  <p className="mt-2 text-xs text-[#8a6e74]">Entrada, saída e, se houver, começo e fim do intervalo.</p>
                </div>
              ) : (
                <p className="mt-3 text-sm text-[#8a6e74]">Depois de criar, a jornada aparece aqui para ajuste.</p>
              )}
              <div className="mt-4 flex flex-wrap items-center justify-end gap-2">
                {escolhido ? <button type="button" className="mr-auto rounded-full border px-4 py-2 text-sm" onClick={arquivar}>Arquivar</button> : null}
                <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={fechar}>Cancelar</button>
                <button className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" type="submit">Salvar</button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function montarRegras(procedimentos: ServicoSalao[], gravadas: ProfissionalSalao["comissoes"] = [], tipoPadrao: Regra["tipo"] = "percentual") {
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
  setRegras((atual) => atual.map((regra, posicao) => posicao === indice ? { ...regra, ...parcial } : regra));
}

function alterarDia(setJornada: Dispatch<SetStateAction<JornadaDia[]>>, indice: number, parcial: Partial<JornadaDia>) {
  setJornada((atual) => atual.map((dia, posicao) => posicao === indice ? { ...dia, ...parcial } : dia));
}
