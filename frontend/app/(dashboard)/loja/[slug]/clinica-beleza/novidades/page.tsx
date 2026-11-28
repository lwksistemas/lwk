"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  Loader2,
  Newspaper,
  Plus,
  Search,
  Trash2,
} from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { ImageUploadMedia } from "@/components/ImageUploadMedia";
import { useToast } from "@/components/ui/Toast";
import {
  mensagemErroNovidade,
  novidadesAdminApi,
  type Novidade,
  type NovidadeConfig,
  type NovidadePayload,
} from "@/lib/clinica-beleza-api/novidades";

const VAZIO: NovidadePayload = {
  titulo: "",
  descricao: "",
  imagem_url: "",
  selo: "Novidades",
  condicao_especial: "",
  preco_de: null,
  preco_por: null,
  botao_texto: "Agende agora",
  botao_url: "",
  beneficios: [],
  ativo: true,
};

export default function ClinicaBelezaNovidadesPage() {
  const { primary } = useClinicaBelezaTheme();
  const toast = useToast();
  const [cfg, setCfg] = useState<NovidadeConfig | null>(null);
  const [itens, setItens] = useState<Novidade[]>([]);
  const [busca, setBusca] = useState("");
  const [filtro, setFiltro] = useState<"all" | "ativo" | "inativo">("all");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [modal, setModal] = useState<null | { mode: "novo" | "editar"; item?: Novidade }>(null);
  const [form, setForm] = useState<NovidadePayload>(VAZIO);
  const [beneficiosTxt, setBeneficiosTxt] = useState("");

  const carregar = useCallback(async () => {
    setLoading(true);
    try {
      const [c, lista] = await Promise.all([
        novidadesAdminApi.getConfig(),
        novidadesAdminApi.list(),
      ]);
      setCfg(c);
      setItens(lista);
    } catch (err) {
      toast.error(mensagemErroNovidade(err, "Não foi possível carregar as novidades."));
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const filtrados = useMemo(() => {
    const q = busca.trim().toLowerCase();
    return itens.filter((n) => {
      if (filtro === "ativo" && !n.ativo) return false;
      if (filtro === "inativo" && n.ativo) return false;
      if (q && !n.titulo.toLowerCase().includes(q) && !n.descricao.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [itens, busca, filtro]);

  const abrirNovo = () => {
    setForm(VAZIO);
    setBeneficiosTxt("");
    setModal({ mode: "novo" });
  };

  const abrirEditar = (item: Novidade) => {
    setForm({
      titulo: item.titulo,
      descricao: item.descricao,
      imagem_url: item.imagem_url,
      selo: item.selo,
      condicao_especial: item.condicao_especial,
      preco_de: item.preco_de,
      preco_por: item.preco_por,
      botao_texto: item.botao_texto,
      botao_url: item.botao_url,
      beneficios: item.beneficios,
      ativo: item.ativo,
      data_inicio: item.data_inicio,
      data_fim: item.data_fim,
      ordem: item.ordem,
    });
    setBeneficiosTxt((item.beneficios || []).join("\n"));
    setModal({ mode: "editar", item });
  };

  const salvar = async () => {
    if (!form.titulo?.trim()) {
      toast.error("Informe o título.");
      return;
    }
    setSaving(true);
    try {
      const payload: NovidadePayload = {
        ...form,
        titulo: form.titulo.trim(),
        beneficios: beneficiosTxt
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean),
      };
      if (modal?.mode === "editar" && modal.item) {
        await novidadesAdminApi.update(modal.item.id, payload);
        toast.success("Novidade atualizada.");
      } else {
        await novidadesAdminApi.create(payload);
        toast.success("Novidade criada.");
      }
      setModal(null);
      await carregar();
    } catch (err) {
      toast.error(mensagemErroNovidade(err, "Não foi possível salvar."));
    } finally {
      setSaving(false);
    }
  };

  const excluir = async (item: Novidade) => {
    if (!confirm(`Excluir “${item.titulo}”?`)) return;
    try {
      await novidadesAdminApi.remove(item.id);
      toast.success("Novidade excluída.");
      await carregar();
    } catch (err) {
      toast.error(mensagemErroNovidade(err, "Não foi possível excluir."));
    }
  };

  const mover = async (item: Novidade, dir: "up" | "down") => {
    const idx = itens.findIndex((n) => n.id === item.id);
    const swapIdx = dir === "up" ? idx - 1 : idx + 1;
    if (swapIdx < 0 || swapIdx >= itens.length) return;
    const outro = itens[swapIdx];
    try {
      await Promise.all([
        novidadesAdminApi.update(item.id, { ordem: outro.ordem }),
        novidadesAdminApi.update(outro.id, { ordem: item.ordem }),
      ]);
      await carregar();
    } catch (err) {
      toast.error(mensagemErroNovidade(err, "Não foi possível reordenar."));
    }
  };

  const salvarConfig = async (patch: Partial<NovidadeConfig>) => {
    try {
      const next = await novidadesAdminApi.patchConfig(patch);
      setCfg(next);
      toast.success("Configuração salva.");
    } catch (err) {
      toast.error(mensagemErroNovidade(err, "Não foi possível salvar a configuração."));
    }
  };

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Novidades"
        subtitle="Campanhas e promoções do Agendamento Online"
        showOffline={false}
        icon={Newspaper}
      />
      <ClinicaBelezaPageContent>
        {loading || !cfg ? (
          <div className="flex items-center gap-2 py-12 text-sm text-[#8a6e74]">
            <Loader2 className="h-4 w-4 animate-spin" /> Carregando…
          </div>
        ) : (
          <div className="space-y-4">
            <section className="rounded-3xl border border-[#f0e4e6] bg-white p-4 dark:border-gray-700 dark:bg-gray-800 sm:p-5">
              <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">Carrossel público</h2>
              <p className="mt-0.5 text-sm text-[#8a6e74]">
                As novidades ativas aparecem ao lado do fluxo de agendamento online.
              </p>
              <div className="mt-4 flex flex-wrap items-center gap-4">
                <label className="flex items-center gap-2 text-sm font-medium">
                  <input
                    type="checkbox"
                    checked={cfg.ativo}
                    onChange={(e) => void salvarConfig({ ativo: e.target.checked })}
                    className="rounded border-gray-300"
                    style={{ accentColor: primary }}
                  />
                  Exibir novidades na página pública
                </label>
                <label className="flex items-center gap-2 text-sm">
                  Intervalo (segundos)
                  <input
                    type="number"
                    min={3}
                    max={30}
                    value={cfg.intervalo_carrossel}
                    onChange={(e) =>
                      setCfg({ ...cfg, intervalo_carrossel: Number(e.target.value) || 5 })
                    }
                    onBlur={() => void salvarConfig({ intervalo_carrossel: cfg.intervalo_carrossel })}
                    className="w-20 rounded-xl border border-[#e8d9dc] px-3 py-1.5 text-sm"
                  />
                </label>
              </div>
            </section>

            <section className="rounded-3xl border border-[#f0e4e6] bg-white p-4 dark:border-gray-700 dark:bg-gray-800 sm:p-5">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-base font-semibold">Publicações</h2>
                <button
                  type="button"
                  onClick={abrirNovo}
                  className="inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold text-white"
                  style={{ backgroundColor: primary }}
                >
                  <Plus className="h-4 w-4" /> Nova novidade
                </button>
              </div>

              <div className="mb-4 flex flex-wrap gap-2">
                <div className="relative min-w-[220px] flex-1">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                  <input
                    value={busca}
                    onChange={(e) => setBusca(e.target.value)}
                    placeholder="Buscar por título…"
                    className="w-full rounded-full border border-[#e8d9dc] py-2 pl-9 pr-3 text-sm"
                  />
                </div>
                <select
                  value={filtro}
                  onChange={(e) => setFiltro(e.target.value as typeof filtro)}
                  className="rounded-full border border-[#e8d9dc] px-3 py-2 text-sm"
                >
                  <option value="all">Todas</option>
                  <option value="ativo">Ativas</option>
                  <option value="inativo">Inativas</option>
                </select>
              </div>

              {filtrados.length === 0 ? (
                <p className="py-8 text-center text-sm text-[#8a6e74]">Nenhuma novidade encontrada.</p>
              ) : (
                <ul className="space-y-3">
                  {filtrados.map((n, idx) => (
                    <li
                      key={n.id}
                      className="flex flex-wrap items-center gap-3 rounded-2xl border border-[#f0e4e6] p-3 dark:border-gray-700"
                    >
                      {n.imagem_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={n.imagem_url} alt="" className="h-16 w-24 rounded-xl object-cover" />
                      ) : (
                        <div className="flex h-16 w-24 items-center justify-center rounded-xl bg-pink-50 text-xs text-pink-400">
                          Sem imagem
                        </div>
                      )}
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-gray-900 dark:text-gray-100">{n.titulo}</p>
                        <p className="truncate text-xs text-[#8a6e74]">
                          {n.ativo ? "Ativa" : "Inativa"}
                          {n.condicao_especial ? ` · ${n.condicao_especial}` : ""}
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          aria-label="Subir"
                          disabled={idx === 0}
                          onClick={() => void mover(n, "up")}
                          className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 disabled:opacity-30"
                        >
                          <ArrowUp className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          aria-label="Descer"
                          disabled={idx === filtrados.length - 1}
                          onClick={() => void mover(n, "down")}
                          className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 disabled:opacity-30"
                        >
                          <ArrowDown className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => abrirEditar(n)}
                          className="rounded-full px-3 py-1.5 text-sm font-medium"
                          style={{ color: primary }}
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          aria-label="Excluir"
                          onClick={() => void excluir(n)}
                          className="rounded-lg p-2 text-red-500 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        )}
      </ClinicaBelezaPageContent>

      {modal ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4">
          <div className="max-h-[92dvh] w-full max-w-2xl overflow-y-auto rounded-t-3xl bg-white p-5 shadow-xl dark:bg-gray-800 sm:rounded-3xl">
            <h3 className="text-lg font-semibold">
              {modal.mode === "novo" ? "Nova novidade" : "Editar novidade"}
            </h3>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <label className="block text-sm sm:col-span-2">
                <span className="mb-1 block font-medium">Título</span>
                <input
                  value={form.titulo || ""}
                  onChange={(e) => setForm({ ...form, titulo: e.target.value })}
                  className="w-full rounded-xl border border-[#e8d9dc] px-3 py-2"
                />
              </label>
              <label className="block text-sm sm:col-span-2">
                <span className="mb-1 block font-medium">Descrição</span>
                <textarea
                  rows={3}
                  value={form.descricao || ""}
                  onChange={(e) => setForm({ ...form, descricao: e.target.value })}
                  className="w-full rounded-xl border border-[#e8d9dc] px-3 py-2"
                />
              </label>
              <label className="block text-sm">
                <span className="mb-1 block font-medium">Selo</span>
                <input
                  value={form.selo || ""}
                  onChange={(e) => setForm({ ...form, selo: e.target.value })}
                  className="w-full rounded-xl border border-[#e8d9dc] px-3 py-2"
                />
              </label>
              <label className="block text-sm">
                <span className="mb-1 block font-medium">Condição especial</span>
                <input
                  value={form.condicao_especial || ""}
                  onChange={(e) => setForm({ ...form, condicao_especial: e.target.value })}
                  className="w-full rounded-xl border border-[#e8d9dc] px-3 py-2"
                  placeholder="Ex.: 10% OFF na primeira sessão"
                />
              </label>
              <label className="block text-sm">
                <span className="mb-1 block font-medium">Preço de</span>
                <input
                  value={form.preco_de || ""}
                  onChange={(e) => setForm({ ...form, preco_de: e.target.value || null })}
                  className="w-full rounded-xl border border-[#e8d9dc] px-3 py-2"
                />
              </label>
              <label className="block text-sm">
                <span className="mb-1 block font-medium">Preço por</span>
                <input
                  value={form.preco_por || ""}
                  onChange={(e) => setForm({ ...form, preco_por: e.target.value || null })}
                  className="w-full rounded-xl border border-[#e8d9dc] px-3 py-2"
                />
              </label>
              <label className="block text-sm">
                <span className="mb-1 block font-medium">Texto do botão</span>
                <input
                  value={form.botao_texto || ""}
                  onChange={(e) => setForm({ ...form, botao_texto: e.target.value })}
                  className="w-full rounded-xl border border-[#e8d9dc] px-3 py-2"
                />
              </label>
              <label className="block text-sm">
                <span className="mb-1 block font-medium">URL do botão (opcional)</span>
                <input
                  value={form.botao_url || ""}
                  onChange={(e) => setForm({ ...form, botao_url: e.target.value })}
                  className="w-full rounded-xl border border-[#e8d9dc] px-3 py-2"
                  placeholder="Vazio = inicia o agendamento"
                />
              </label>
              <div className="sm:col-span-2">
                <ImageUploadMedia
                  label="Imagem do slide"
                  folder="fotos"
                  value={form.imagem_url || ""}
                  onChange={(url) => setForm({ ...form, imagem_url: url })}
                />
              </div>
              <label className="block text-sm sm:col-span-2">
                <span className="mb-1 block font-medium">Benefícios (um por linha)</span>
                <textarea
                  rows={3}
                  value={beneficiosTxt}
                  onChange={(e) => setBeneficiosTxt(e.target.value)}
                  className="w-full rounded-xl border border-[#e8d9dc] px-3 py-2"
                />
              </label>
              <label className="flex items-center gap-2 text-sm sm:col-span-2">
                <input
                  type="checkbox"
                  checked={Boolean(form.ativo)}
                  onChange={(e) => setForm({ ...form, ativo: e.target.checked })}
                  style={{ accentColor: primary }}
                />
                Publicação ativa
              </label>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setModal(null)}
                className="rounded-full border border-[#e8d9dc] px-4 py-2 text-sm font-medium"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={() => void salvar()}
                className="inline-flex items-center gap-2 rounded-full px-5 py-2 text-sm font-semibold text-white disabled:opacity-60"
                style={{ backgroundColor: primary }}
              >
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Salvar
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
