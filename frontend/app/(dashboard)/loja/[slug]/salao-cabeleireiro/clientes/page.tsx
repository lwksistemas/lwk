"use client";

import { useState, useEffect } from "react";
import { SalaoAPI, type ClienteSalao } from "@/lib/salao-api";
import { consultaCep } from "@/lib/consulta-cep";
import { formatCep, formatCpf } from "@/lib/format-br";

const CAMPO = "w-full rounded-lg border px-2 py-2";
const UFS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"];
const VAZIO = {
  nome: "",
  telefone: "",
  email: "",
  cpf: "",
  data_nascimento: "",
  cep: "",
  logradouro: "",
  numero: "",
  complemento: "",
  bairro: "",
  cidade: "",
  estado: "",
};

export default function ClientesSalaoPage() {
  const [lista, setLista] = useState<ClienteSalao[]>([]);
  const [escolhido, setEscolhido] = useState<number | null>(null);
  const [form, setForm] = useState(VAZIO);
  const [aberto, setAberto] = useState(false);
  const [erro, setErro] = useState("");
  const [buscandoCep, setBuscandoCep] = useState(false);

  function carregar() {
    SalaoAPI.clientes().then(setLista).catch((exc: Error) => setErro(exc.message));
  }
  useEffect(() => { carregar(); }, []);

  function novo() {
    setEscolhido(null);
    setForm(VAZIO);
    setErro("");
    setAberto(true);
  }

  function abrir(item: ClienteSalao) {
    setEscolhido(item.id);
    setErro("");
    setForm({
      nome: item.nome,
      telefone: item.telefone,
      email: item.email || "",
      cpf: formatCpf(item.cpf || ""),
      data_nascimento: item.data_nascimento || "",
      cep: formatCep(item.cep || ""),
      logradouro: item.logradouro || "",
      numero: item.numero || "",
      complemento: item.complemento || "",
      bairro: item.bairro || "",
      cidade: item.cidade || "",
      estado: item.estado || "",
    });
    setAberto(true);
  }

  function fechar() {
    setAberto(false);
    setEscolhido(null);
    setForm(VAZIO);
    setErro("");
  }

  async function salvar(evento: React.FormEvent) {
    evento.preventDefault();
    setErro("");
    try {
      await SalaoAPI.salvarCliente({
        ...form,
        email: form.email || null,
        data_nascimento: form.data_nascimento || null,
        cpf: form.cpf || "",
        cidade: form.cidade || "",
        estado: form.estado || "",
      }, escolhido ?? undefined);
      fechar();
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível salvar.");
    }
  }

  async function buscarCep() {
    const digitos = form.cep.replace(/\D/g, "");
    if (digitos.length !== 8) return;
    setBuscandoCep(true);
    try {
      const endereco = await consultaCep(digitos);
      if (!endereco) {
        setErro("CEP não encontrado.");
        return;
      }
      setErro("");
      setForm((atual) => ({
        ...atual,
        logradouro: endereco.logradouro || atual.logradouro,
        bairro: endereco.bairro || atual.bairro,
        cidade: endereco.cidade || atual.cidade,
        estado: endereco.uf || atual.estado,
      }));
    } finally {
      setBuscandoCep(false);
    }
  }

  async function arquivar() {
    if (!escolhido) return;
    try {
      await SalaoAPI.arquivar(`/clientes/${escolhido}/`);
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
          <h1 className="text-2xl font-semibold sm:text-3xl">Clientes</h1>
          <p className="text-sm text-[#8a6e74]">CPF e endereço completo entram na NFS-e e na NFC-e. O cliente pode ser salvo antes de preencher os dois.</p>
        </div>
        <button type="button" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" onClick={novo}>Adicionar cliente</button>
      </div>
      {!aberto && erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
      {lista.length === 0 ? <p className="text-sm text-[#8a6e74]">Nenhum cliente cadastrado.</p> : null}
      <ul className="grid gap-3 md:grid-cols-2">
        {lista.map((item) => (
          <li key={item.id}>
            <button type="button" className="flex h-full w-full items-start justify-between gap-3 rounded-3xl border border-[#f0e4e6] bg-white px-4 py-3 text-left hover:bg-[#fbf6f4]" onClick={() => abrir(item)}>
              <span>
                <span className="block font-medium">{item.nome}</span>
                <span className="mt-0.5 block text-sm text-[#8a6e74]">{[item.cpf ? formatCpf(item.cpf) : "", item.cidade, item.email].filter(Boolean).join(" · ") || "Sem e-mail"}</span>
              </span>
              <span className="shrink-0 text-sm text-[#8a6e74]">{item.telefone}</span>
            </button>
          </li>
        ))}
      </ul>
      {aberto ? (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="cliente-formulario" onClick={(evento) => { if (evento.target === evento.currentTarget) fechar(); }}>
          <form className="max-h-[90vh] w-full max-w-lg overflow-auto rounded-3xl bg-white p-5" onSubmit={salvar}>
            <h2 id="cliente-formulario" className="mb-3 text-lg font-semibold">{escolhido ? "Editar cliente" : "Adicionar cliente"}</h2>
            {erro ? <p className="mb-2 text-sm text-red-700">{erro}</p> : null}
            <div className="grid gap-2 sm:grid-cols-2">
              <label className="text-sm">Nome
                <input className={`mt-1 ${CAMPO}`} value={form.nome} onChange={(evento) => setForm({ ...form, nome: evento.target.value })} required />
              </label>
              <label className="text-sm">Telefone
                <input className={`mt-1 ${CAMPO}`} value={form.telefone} onChange={(evento) => setForm({ ...form, telefone: evento.target.value })} required />
              </label>
              <label className="text-sm">E-mail
                <input className={`mt-1 ${CAMPO}`} value={form.email} onChange={(evento) => setForm({ ...form, email: evento.target.value })} />
              </label>
              <label className="text-sm">Aniversário
                <input type="date" className={`mt-1 ${CAMPO}`} value={form.data_nascimento} onChange={(evento) => setForm({ ...form, data_nascimento: evento.target.value })} />
              </label>
              <label className="text-sm sm:col-span-2">CPF
                <input className={`mt-1 ${CAMPO}`} inputMode="numeric" value={form.cpf} onChange={(evento) => setForm({ ...form, cpf: formatCpf(evento.target.value) })} placeholder="000.000.000-00" />
              </label>
            </div>
            <p className="mb-2 mt-4 text-sm font-medium">Endereço</p>
            <div className="grid gap-2 sm:grid-cols-2">
              <label className="text-sm">CEP
                <span className="mt-1 flex gap-2">
                  <input className={CAMPO} inputMode="numeric" value={form.cep} onChange={(evento) => setForm({ ...form, cep: formatCep(evento.target.value) })} onBlur={buscarCep} placeholder="00000-000" />
                  <button type="button" className="shrink-0 rounded-lg border px-3 text-sm" onClick={buscarCep} disabled={buscandoCep}>{buscandoCep ? "..." : "Buscar"}</button>
                </span>
              </label>
              <label className="text-sm">Logradouro
                <input className={`mt-1 ${CAMPO}`} value={form.logradouro} onChange={(evento) => setForm({ ...form, logradouro: evento.target.value })} />
              </label>
              <label className="text-sm">Número
                <input className={`mt-1 ${CAMPO}`} value={form.numero} onChange={(evento) => setForm({ ...form, numero: evento.target.value })} />
              </label>
              <label className="text-sm">Complemento
                <input className={`mt-1 ${CAMPO}`} value={form.complemento} onChange={(evento) => setForm({ ...form, complemento: evento.target.value })} />
              </label>
              <label className="text-sm">Bairro
                <input className={`mt-1 ${CAMPO}`} value={form.bairro} onChange={(evento) => setForm({ ...form, bairro: evento.target.value })} />
              </label>
              <label className="text-sm">Cidade
                <input className={`mt-1 ${CAMPO}`} value={form.cidade} onChange={(evento) => setForm({ ...form, cidade: evento.target.value })} />
              </label>
              <label className="text-sm">Estado
                <select className={`mt-1 ${CAMPO}`} value={form.estado} onChange={(evento) => setForm({ ...form, estado: evento.target.value })}>
                  <option value="">—</option>
                  {UFS.map((uf) => <option key={uf} value={uf}>{uf}</option>)}
                </select>
              </label>
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-end gap-2">
              {escolhido ? <button type="button" className="mr-auto rounded-full border px-4 py-2 text-sm" onClick={arquivar}>Arquivar</button> : null}
              <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={fechar}>Cancelar</button>
              <button className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" type="submit">Salvar</button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  );
}
