"use client";

import { useCallback, useEffect, useState } from "react";
import { Users } from "lucide-react";
import { AppPageContent, AppPanel } from "@/components/shared/layout/PageContent";
import { EntityListTable, type EntityListColumn } from "@/components/shared/layout/EntityListTable";
import { StandardPageHeader } from "@/components/shared/layout/StandardPageHeader";
import { useFormRouting } from "@/hooks/shared/useFormRouting";
import { consultaCep } from "@/lib/consulta-cep";
import { formatCep, formatCpf } from "@/lib/format-br";
import { SalaoAPI, type ClienteSalao } from "@/lib/salao-api";

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

export function SalaoClientesPageContent() {
  const { isNovo, editId, isFormView, voltarLista, abrirNovo, abrirEditar } = useFormRouting();
  const [lista, setLista] = useState<ClienteSalao[]>([]);
  const [form, setForm] = useState(VAZIO);
  const [erro, setErro] = useState("");
  const [buscandoCep, setBuscandoCep] = useState(false);
  const [carregandoForm, setCarregandoForm] = useState(false);

  const carregar = useCallback(() => {
    SalaoAPI.clientes().then(setLista).catch((exc: Error) => setErro(exc.message));
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  useEffect(() => {
    if (!isFormView) {
      setForm(VAZIO);
      setErro("");
      return;
    }
    if (isNovo || !editId) {
      setForm(VAZIO);
      setErro("");
      return;
    }
    let ativo = true;
    setCarregandoForm(true);
    SalaoAPI.clientes()
      .then((todos) => {
        if (!ativo) return;
        setLista(todos);
        const achado = todos.find((c) => c.id === editId);
        if (!achado) {
          setErro("Cliente não encontrado.");
          return;
        }
        setForm({
          nome: achado.nome,
          telefone: achado.telefone,
          email: achado.email || "",
          cpf: formatCpf(achado.cpf || ""),
          data_nascimento: achado.data_nascimento || "",
          cep: formatCep(achado.cep || ""),
          logradouro: achado.logradouro || "",
          numero: achado.numero || "",
          complemento: achado.complemento || "",
          bairro: achado.bairro || "",
          cidade: achado.cidade || "",
          estado: achado.estado || "",
        });
        setErro("");
      })
      .catch((exc: Error) => {
        if (ativo) setErro(exc.message);
      })
      .finally(() => {
        if (ativo) setCarregandoForm(false);
      });
    return () => {
      ativo = false;
    };
  }, [isFormView, isNovo, editId]);

  async function salvar(evento: React.FormEvent) {
    evento.preventDefault();
    setErro("");
    try {
      await SalaoAPI.salvarCliente(
        {
          ...form,
          email: form.email || null,
          data_nascimento: form.data_nascimento || null,
          cpf: form.cpf || "",
          cidade: form.cidade || "",
          estado: form.estado || "",
        },
        editId ?? undefined,
      );
      carregar();
      voltarLista();
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
    if (!editId) return;
    try {
      await SalaoAPI.arquivar(`/clientes/${editId}/`);
      carregar();
      voltarLista();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível arquivar.");
    }
  }

  const columns: EntityListColumn<ClienteSalao>[] = [
    { key: "nome", header: "Nome", render: (row) => <span className="font-medium">{row.nome}</span> },
    { key: "telefone", header: "Telefone", render: (row) => row.telefone },
    {
      key: "email",
      header: "E-mail",
      render: (row) => [row.cpf ? formatCpf(row.cpf) : "", row.cidade, row.email].filter(Boolean).join(" · ") || "—",
    },
  ];

  if (isFormView) {
    return (
      <AppPageContent>
        <StandardPageHeader
          title={editId ? "Editar cliente" : "Adicionar cliente"}
          subtitle="CPF e endereço completo entram na NFS-e e na NFC-e."
          icon={Users}
          onBack={voltarLista}
          showBack
        />
        <AppPanel className="p-4 sm:p-6">
          {carregandoForm ? <p className="text-sm text-[#8a6e74]">Carregando…</p> : null}
          {erro ? <p className="mb-3 text-sm text-red-700">{erro}</p> : null}
          <form onSubmit={salvar}>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-sm">Nome
                <input className={`mt-1 ${CAMPO}`} value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
              </label>
              <label className="text-sm">Telefone
                <input className={`mt-1 ${CAMPO}`} value={form.telefone} onChange={(e) => setForm({ ...form, telefone: e.target.value })} required />
              </label>
              <label className="text-sm">E-mail
                <input className={`mt-1 ${CAMPO}`} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </label>
              <label className="text-sm">Aniversário
                <input type="date" className={`mt-1 ${CAMPO}`} value={form.data_nascimento} onChange={(e) => setForm({ ...form, data_nascimento: e.target.value })} />
              </label>
              <label className="text-sm sm:col-span-2">CPF
                <input className={`mt-1 ${CAMPO}`} inputMode="numeric" value={form.cpf} onChange={(e) => setForm({ ...form, cpf: formatCpf(e.target.value) })} placeholder="000.000.000-00" />
              </label>
            </div>
            <p className="mb-2 mt-5 text-sm font-medium">Endereço</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-sm">CEP
                <span className="mt-1 flex gap-2">
                  <input className={CAMPO} inputMode="numeric" value={form.cep} onChange={(e) => setForm({ ...form, cep: formatCep(e.target.value) })} onBlur={buscarCep} placeholder="00000-000" />
                  <button type="button" className="shrink-0 rounded-lg border px-3 text-sm" onClick={buscarCep} disabled={buscandoCep}>{buscandoCep ? "..." : "Buscar"}</button>
                </span>
              </label>
              <label className="text-sm">Logradouro
                <input className={`mt-1 ${CAMPO}`} value={form.logradouro} onChange={(e) => setForm({ ...form, logradouro: e.target.value })} />
              </label>
              <label className="text-sm">Número
                <input className={`mt-1 ${CAMPO}`} value={form.numero} onChange={(e) => setForm({ ...form, numero: e.target.value })} />
              </label>
              <label className="text-sm">Complemento
                <input className={`mt-1 ${CAMPO}`} value={form.complemento} onChange={(e) => setForm({ ...form, complemento: e.target.value })} />
              </label>
              <label className="text-sm">Bairro
                <input className={`mt-1 ${CAMPO}`} value={form.bairro} onChange={(e) => setForm({ ...form, bairro: e.target.value })} />
              </label>
              <label className="text-sm">Cidade
                <input className={`mt-1 ${CAMPO}`} value={form.cidade} onChange={(e) => setForm({ ...form, cidade: e.target.value })} />
              </label>
              <label className="text-sm">Estado
                <select className={`mt-1 ${CAMPO}`} value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })}>
                  <option value="">—</option>
                  {UFS.map((uf) => <option key={uf} value={uf}>{uf}</option>)}
                </select>
              </label>
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
        title="Clientes"
        subtitle="CPF e endereço completo entram na NFS-e e na NFC-e. O cliente pode ser salvo antes de preencher os dois."
        icon={Users}
        newLabel="Adicionar cliente"
        onNew={abrirNovo}
      />
      {erro ? <p className="mb-3 text-sm text-red-700">{erro}</p> : null}
      <AppPanel>
        <EntityListTable
          columns={columns}
          rows={lista}
          rowKey={(row) => row.id}
          onRowClick={(row) => abrirEditar(row.id)}
          emptyMessage={<p className="px-4 py-8 text-sm text-[#8a6e74]">Nenhum cliente cadastrado.</p>}
        />
      </AppPanel>
    </AppPageContent>
  );
}
