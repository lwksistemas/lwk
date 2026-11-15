"use client";

import { useEffect, useState, type Dispatch, type FormEvent, type SetStateAction } from "react";
import { SalaoAPI, type BloqueioSalao, type JornadaDia, type ProfissionalSalao } from "@/lib/salao-api";

const DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];
const CAMPO = "w-full rounded-lg border px-2 py-2";

const VAZIO = { nome: "", telefone: "", especialidade: "Cabeleireiro", comissao_percentual: "0" };

export default function ProfissionaisSalaoPage() {
  const [lista, setLista] = useState<ProfissionalSalao[]>([]);
  const [bloqueios, setBloqueios] = useState<BloqueioSalao[]>([]);
  const [escolhido, setEscolhido] = useState<number | null>(null);
  const [form, setForm] = useState(VAZIO);
  const [jornada, setJornada] = useState<JornadaDia[]>([]);
  const [folga, setFolga] = useState({ titulo: "", data_inicio: "", data_fim: "", horario_inicio: "", horario_fim: "" });
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");

  function carregar() {
    Promise.all([SalaoAPI.profissionais(), SalaoAPI.bloqueios()])
      .then(([pessoas, folgas]) => {
        setLista(pessoas);
        setBloqueios(folgas);
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
      comissao_percentual: String(item.comissao_percentual),
    });
    setJornada(await SalaoAPI.jornada(item.id));
  }

  function novo() {
    setEscolhido(null);
    setForm(VAZIO);
    setJornada([]);
    setAviso("");
  }

  async function salvar(evento: FormEvent) {
    evento.preventDefault();
    setErro("");
    setAviso("");
    try {
      const corpo = { ...form, comissao_percentual: form.comissao_percentual.replace(",", ".") };
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
      novo();
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível arquivar.");
    }
  }

  async function criarFolga(evento: FormEvent) {
    evento.preventDefault();
    if (!escolhido) return;
    setErro("");
    try {
      await SalaoAPI.bloquear({
        titulo: folga.titulo,
        tipo: "folga",
        profissional: escolhido,
        data_inicio: folga.data_inicio,
        data_fim: folga.data_fim || folga.data_inicio,
        horario_inicio: folga.horario_inicio,
        horario_fim: folga.horario_fim,
      });
      setFolga({ titulo: "", data_inicio: "", data_fim: "", horario_inicio: "", horario_fim: "" });
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível gravar a folga.");
    }
  }

  const folgasDele = bloqueios.filter((item) => item.profissional === escolhido);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold sm:text-3xl">Profissionais</h1>
          <p className="text-sm text-[#8a6e74]">A jornada padrão é de segunda a sábado, das 9h às 19h. Domingo começa como folga.</p>
        </div>
        <button type="button" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" onClick={novo}>Novo profissional</button>
      </div>
      {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      {aviso ? <p className="mb-2 text-sm text-[#1f8a4c]">{aviso}</p> : null}
      {lista.length === 0 ? <p className="mb-3 text-sm text-[#8a6e74]">Nenhum profissional cadastrado.</p> : null}
      <div className="grid gap-4 lg:grid-cols-[16rem_minmax(0,1fr)]">
        <ul className="rounded-3xl border border-[#f0e4e6] bg-white">
          {lista.map((item) => (
            <li key={item.id}>
              <button type="button" className={`w-full px-4 py-3 text-left text-sm ${escolhido === item.id ? "bg-[#f6ecee]" : ""}`} onClick={() => abrir(item)}>
                <span className="block font-medium">{item.nome}</span>
                <span className="text-[#8a6e74]">{item.especialidade} · {item.comissao_percentual}%</span>
              </button>
            </li>
          ))}
        </ul>
        <form className="rounded-3xl border border-[#f0e4e6] bg-white p-4" onSubmit={salvar}>
          <div className="grid gap-2 sm:grid-cols-2">
            <input className={CAMPO} placeholder="Nome" value={form.nome} onChange={(evento) => setForm({ ...form, nome: evento.target.value })} required />
            <input className={CAMPO} placeholder="Telefone" value={form.telefone} onChange={(evento) => setForm({ ...form, telefone: evento.target.value })} required />
            <input className={CAMPO} placeholder="Função" value={form.especialidade} onChange={(evento) => setForm({ ...form, especialidade: evento.target.value })} />
            <input className={CAMPO} placeholder="Comissão %" value={form.comissao_percentual} onChange={(evento) => setForm({ ...form, comissao_percentual: evento.target.value })} />
          </div>
          {escolhido && jornada.length === 7 ? (
            <div className="mt-4 overflow-auto">
              <h2 className="mb-2 text-sm font-medium">Jornada</h2>
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
          <div className="mt-4 flex flex-wrap gap-2">
            <button className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" type="submit">{escolhido ? "Salvar" : "Adicionar profissional"}</button>
            {escolhido ? <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={arquivar}>Arquivar</button> : null}
          </div>
        </form>
      </div>
      {escolhido ? (
        <section className="mt-4 rounded-3xl border border-[#f0e4e6] bg-white p-4">
          <h2 className="mb-2 text-sm font-medium">Folgas e bloqueios</h2>
          <form className="grid gap-2 sm:grid-cols-5" onSubmit={criarFolga}>
            <input className={CAMPO} placeholder="Motivo" value={folga.titulo} onChange={(evento) => setFolga({ ...folga, titulo: evento.target.value })} required />
            <input type="date" className={CAMPO} value={folga.data_inicio} onChange={(evento) => setFolga({ ...folga, data_inicio: evento.target.value })} required />
            <input type="date" className={CAMPO} value={folga.data_fim} onChange={(evento) => setFolga({ ...folga, data_fim: evento.target.value })} />
            <input type="time" className={CAMPO} value={folga.horario_inicio} onChange={(evento) => setFolga({ ...folga, horario_inicio: evento.target.value })} />
            <input type="time" className={CAMPO} value={folga.horario_fim} onChange={(evento) => setFolga({ ...folga, horario_fim: evento.target.value })} />
            <button className="rounded-full border px-4 py-2 text-sm sm:col-span-5" type="submit">Registrar folga</button>
          </form>
          <p className="mt-2 text-xs text-[#8a6e74]">Sem horário, o dia inteiro fica bloqueado.</p>
          {folgasDele.length === 0 ? <p className="mt-3 text-sm text-[#8a6e74]">Nenhuma folga cadastrada.</p> : null}
          <ul>
            {folgasDele.map((item) => (
              <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f0e4e6] py-2 text-sm">
                <span>{item.titulo} · {item.data_inicio}{item.data_fim !== item.data_inicio ? ` a ${item.data_fim}` : ""}{item.horario_inicio ? ` · ${item.horario_inicio.slice(0, 5)}–${item.horario_fim?.slice(0, 5)}` : " · dia inteiro"}</span>
                <button type="button" className="text-[#8a6e74]" onClick={() => SalaoAPI.removerBloqueio(item.id).then(carregar).catch((exc: Error) => setErro(exc.message))}>Remover</button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function alterarDia(setJornada: Dispatch<SetStateAction<JornadaDia[]>>, indice: number, parcial: Partial<JornadaDia>) {
  setJornada((atual) => atual.map((dia, posicao) => posicao === indice ? { ...dia, ...parcial } : dia));
}
