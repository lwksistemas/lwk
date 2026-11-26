"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Tag } from "lucide-react";
import { AppPageContent, AppPanel } from "@/components/shared/layout/PageContent";
import { EntityListTable, type EntityListColumn } from "@/components/shared/layout/EntityListTable";
import { StandardPageHeader } from "@/components/shared/layout/StandardPageHeader";
import { useFormRouting } from "@/hooks/shared/useFormRouting";
import { SalaoAPI, type CategoriaSalao, type ServicoSalao } from "@/lib/salao-api";

const CAMPO = "w-full rounded-lg border px-2 py-2";
const VAZIO = { nome: "", categoria: "", duracao_minutos: "60", preco: "", descricao: "" };

export function SalaoServicosPageContent() {
  const { isNovo, editId, isFormView, voltarLista, abrirNovo, abrirEditar } = useFormRouting();
  const [lista, setLista] = useState<ServicoSalao[]>([]);
  const [categorias, setCategorias] = useState<CategoriaSalao[]>([]);
  const [form, setForm] = useState(VAZIO);
  const [erro, setErro] = useState("");
  const [categoriasAberto, setCategoriasAberto] = useState(false);
  const [nomeCategoria, setNomeCategoria] = useState("");
  const [editando, setEditando] = useState<number | null>(null);
  const [nomeEdicao, setNomeEdicao] = useState("");

  const carregar = useCallback(() => {
    Promise.all([SalaoAPI.servicos(), SalaoAPI.categorias()])
      .then(([servicos, grupos]) => {
        setLista(servicos);
        setCategorias(grupos);
      })
      .catch((exc: Error) => setErro(exc.message));
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
      setForm({ ...VAZIO, categoria: categorias[0]?.nome || "" });
      setErro("");
      return;
    }
    let ativo = true;
    Promise.all([SalaoAPI.servicos(), SalaoAPI.categorias()])
      .then(([servicos, grupos]) => {
        if (!ativo) return;
        setLista(servicos);
        setCategorias(grupos);
        const item = servicos.find((s) => s.id === editId);
        if (!item) {
          setErro("Serviço não encontrado.");
          return;
        }
        setForm({
          nome: item.nome,
          categoria: item.categoria,
          duracao_minutos: String(item.duracao_minutos),
          preco: String(item.preco),
          descricao: item.descricao || "",
        });
        setErro("");
      })
      .catch((exc: Error) => {
        if (ativo) setErro(exc.message);
      });
    return () => {
      ativo = false;
    };
  }, [isFormView, isNovo, editId]);

  async function salvar(evento: React.FormEvent) {
    evento.preventDefault();
    setErro("");
    try {
      await SalaoAPI.salvarServico(
        {
          ...form,
          duracao_minutos: Number(form.duracao_minutos),
          preco: form.preco.replace(",", "."),
          descricao: form.descricao,
        },
        editId ?? undefined,
      );
      carregar();
      voltarLista();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível salvar.");
    }
  }

  async function arquivar() {
    if (!editId) return;
    try {
      await SalaoAPI.arquivar(`/servicos/${editId}/`);
      carregar();
      voltarLista();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível arquivar.");
    }
  }

  async function adicionarCategoria(evento: React.FormEvent) {
    evento.preventDefault();
    setErro("");
    try {
      await SalaoAPI.criarCategoria(nomeCategoria);
      setNomeCategoria("");
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível criar a categoria.");
    }
  }

  async function gravarCategoria(id: number) {
    setErro("");
    try {
      await SalaoAPI.renomearCategoria(id, nomeEdicao);
      setEditando(null);
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível renomear a categoria.");
    }
  }

  async function arquivarCategoria(id: number) {
    setErro("");
    try {
      await SalaoAPI.arquivarCategoria(id);
      carregar();
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível arquivar a categoria.");
    }
  }

  const columns: EntityListColumn<ServicoSalao>[] = [
    { key: "nome", header: "Nome", render: (row) => <span className="font-medium">{row.nome}</span> },
    { key: "categoria", header: "Categoria", render: (row) => row.categoria },
    { key: "duracao", header: "Duração", render: (row) => `${row.duracao_minutos} min` },
    { key: "preco", header: "Preço", render: (row) => `R$ ${row.preco}` },
  ];

  const gruposComServico = useMemo(
    () => categorias.filter((grupo) => lista.some((item) => item.categoria === grupo.nome)),
    [categorias, lista],
  );

  if (isFormView) {
    return (
      <AppPageContent>
        <StandardPageHeader
          title={editId ? "Editar serviço" : "Adicionar serviço"}
          subtitle="O tempo fica no serviço. A mesma categoria pode ter serviços com durações diferentes."
          icon={Tag}
          onBack={voltarLista}
          showBack
        />
        <AppPanel className="p-4 sm:p-6">
          {erro ? <p className="mb-3 text-sm text-red-700">{erro}</p> : null}
          <form onSubmit={salvar}>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-sm">Nome
                <input className={`mt-1 ${CAMPO}`} value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
              </label>
              <label className="text-sm">Minutos
                <input className={`mt-1 ${CAMPO}`} inputMode="numeric" value={form.duracao_minutos} onChange={(e) => setForm({ ...form, duracao_minutos: e.target.value })} required />
              </label>
              <label className="text-sm sm:col-span-2">Categoria
                <select className={`mt-1 ${CAMPO}`} value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value })} required>
                  <option value="">Escolha</option>
                  {categorias.map((item) => (
                    <option key={item.id} value={item.nome}>{item.nome}</option>
                  ))}
                </select>
              </label>
              <label className="text-sm sm:col-span-2">Preço
                <input className={`mt-1 ${CAMPO}`} inputMode="decimal" value={form.preco} onChange={(e) => setForm({ ...form, preco: e.target.value })} required />
              </label>
              <label className="text-sm sm:col-span-2">Descrição
                <textarea className={`mt-1 ${CAMPO}`} value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
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
        title="Serviços"
        subtitle="O tempo fica no serviço. A mesma categoria pode ter serviços com durações diferentes."
        icon={Tag}
        newLabel="Adicionar serviço"
        onNew={abrirNovo}
        extraActions={
          <button
            type="button"
            className="rounded-full border border-[#7a3044] px-4 py-2 text-sm text-[#7a3044]"
            onClick={() => {
              setErro("");
              setCategoriasAberto(true);
            }}
          >
            Categorias
          </button>
        }
      />
      {erro && !categoriasAberto ? <p className="mb-3 text-sm text-red-700">{erro}</p> : null}
      {lista.length === 0 ? (
        <AppPanel>
          <p className="px-4 py-8 text-sm text-[#8a6e74]">Nenhum serviço registrado.</p>
        </AppPanel>
      ) : (
        <div className="space-y-5">
          {gruposComServico.map((grupo) => (
            <AppPanel key={grupo.id}>
              <div className="border-b border-gray-100 px-4 py-3 text-sm font-semibold uppercase tracking-wide text-[#7a3044]">
                {grupo.nome}
              </div>
              <EntityListTable
                columns={columns.filter((c) => c.key !== "categoria")}
                rows={lista.filter((item) => item.categoria === grupo.nome)}
                rowKey={(row) => row.id}
                onRowClick={(row) => abrirEditar(row.id)}
              />
            </AppPanel>
          ))}
        </div>
      )}
      {categoriasAberto ? (
        <div
          className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="categoria-formulario"
          onClick={(evento) => {
            if (evento.target === evento.currentTarget) setCategoriasAberto(false);
          }}
        >
          <div className="max-h-[90vh] w-full max-w-lg overflow-auto rounded-2xl bg-white p-5">
            <h2 id="categoria-formulario" className="text-lg font-semibold">Categorias</h2>
            <p className="mt-1 text-sm text-[#8a6e74]">A categoria só agrupa. O tempo fica no nome de cada serviço.</p>
            {erro ? <p className="mt-2 text-sm text-red-700">{erro}</p> : null}
            <ul className="mt-3">
              {categorias.length === 0 ? <li className="text-sm text-[#8a6e74]">Nenhuma categoria cadastrada.</li> : null}
              {categorias.map((item) => (
                <li key={item.id} className="flex items-center gap-2 border-t border-[#f0e4e6] py-2 text-sm">
                  {editando === item.id ? (
                    <input className="min-w-0 flex-1 rounded-lg border px-2 py-1" value={nomeEdicao} onChange={(e) => setNomeEdicao(e.target.value)} />
                  ) : (
                    <span className="min-w-0 flex-1">{item.nome}</span>
                  )}
                  {editando === item.id ? (
                    <button type="button" className="text-[#7a3044]" onClick={() => void gravarCategoria(item.id)}>Salvar</button>
                  ) : (
                    <button type="button" className="text-[#7a3044]" onClick={() => { setEditando(item.id); setNomeEdicao(item.nome); }}>Renomear</button>
                  )}
                  <button type="button" className="text-[#8a6e74]" onClick={() => void arquivarCategoria(item.id)}>Arquivar</button>
                </li>
              ))}
            </ul>
            <form className="mt-4 flex flex-wrap gap-2" onSubmit={adicionarCategoria}>
              <input
                className="min-w-40 flex-1 rounded-lg border px-3 py-2 text-sm"
                value={nomeCategoria}
                onChange={(e) => setNomeCategoria(e.target.value)}
                placeholder="Nova categoria"
                required
              />
              <button className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" type="submit">Salvar</button>
            </form>
            <div className="mt-4 flex justify-end">
              <button
                type="button"
                className="rounded-full border px-4 py-2 text-sm"
                onClick={() => {
                  setCategoriasAberto(false);
                  setEditando(null);
                  setErro("");
                }}
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </AppPageContent>
  );
}
