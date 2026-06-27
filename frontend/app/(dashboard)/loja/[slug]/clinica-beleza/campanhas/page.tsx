"use client";

/**
 * Campanhas de Promoções — lista tela cheia; novo/editar via ?novo=1 / ?id=X
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeft, Megaphone, Pencil, Save, Send, Trash2 } from "lucide-react";
import { CampanhaEnviarModal } from "@/components/clinica-beleza/CampanhaEnviarModal";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { EntityListTable } from "@/components/clinica-beleza/EntityListTable";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { useToast } from "@/components/ui/Toast";
import {
  CLINICA_BELEZA_ONLINE_ONLY,
  CLINICA_FORM_INPUT,
  deleteClinicaBelezaEntity,
  saveClinicaBelezaEntity,
  useClinicaBelezaEntityList,
} from "@/lib/clinica-beleza-crud";
import { formatClinicaDataCurta, formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";
import { useClinicaBelezaFormRouting } from "@/hooks/clinica-beleza/useClinicaBelezaFormRouting";
import { toUpperCase } from "@/lib/format-br";

interface Campanha {
  id: number;
  titulo: string;
  mensagem: string;
  data_inicio: string | null;
  data_fim: string | null;
  ativa: boolean;
  enviada_em: string | null;
  total_enviados: number;
  created_at: string;
}

const EMPTY_FORM = {
  titulo: "",
  mensagem: "",
  data_inicio: "",
  data_fim: "",
  ativa: true,
};

function campanhaToForm(c: Campanha) {
  return {
    titulo: c.titulo,
    mensagem: c.mensagem,
    data_inicio: c.data_inicio ? c.data_inicio.slice(0, 10) : "",
    data_fim: c.data_fim ? c.data_fim.slice(0, 10) : "",
    ativa: c.ativa,
  };
}

function extractSaveError(e: unknown, fallback: string): string {
  if (e instanceof Error && e.message === "SESSION_ENDED") return "SESSION_ENDED";
  if (e && typeof e === "object" && "error" in e && typeof (e as { error?: string }).error === "string") {
    return (e as { error: string }).error;
  }
  return e instanceof Error ? e.message : fallback;
}

export default function CampanhasPage() {
  const slug = useParams().slug as string;
  const toast = useToast();
  const basePath = `/loja/${slug}/clinica-beleza/campanhas`;
  const { isNovo, editId, editIdParam, isFormView, voltarLista, abrirNovo, abrirEditar } =
    useClinicaBelezaFormRouting(basePath);

  const { list, loading, load, page, setPage, totalPages, pageSize, totalCount } = useClinicaBelezaEntityList<Campanha>({
    path: "/campanhas/",
    ...CLINICA_BELEZA_ONLINE_ONLY,
  });

  const [editing, setEditing] = useState<Campanha | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [enviarCampanha, setEnviarCampanha] = useState<Campanha | null>(null);
  const [excluirCampanha, setExcluirCampanha] = useState<Campanha | null>(null);
  const [excluindo, setExcluindo] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isNovo) {
      setEditing(null);
      setForm(EMPTY_FORM);
      setError("");
      return;
    }
    if (editIdParam && list.length > 0) {
      const c = list.find((x) => String(x.id) === editIdParam);
      if (c) {
        setEditing(c);
        setForm(campanhaToForm(c));
        setError("");
      }
    }
  }, [isNovo, editIdParam, list]);

  const save = async () => {
    if (!form.titulo.trim() || !form.mensagem.trim()) {
      setError("Título e mensagem são obrigatórios.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const body = {
        titulo: form.titulo.trim(),
        mensagem: form.mensagem.trim(),
        data_inicio: form.data_inicio || null,
        data_fim: form.data_fim || null,
        ativa: form.ativa,
      };
      if (editing) {
        await saveClinicaBelezaEntity(`/campanhas/${editing.id}/`, "PUT", body);
        toast.success("Campanha atualizada.");
      } else {
        await saveClinicaBelezaEntity("/campanhas/", "POST", body);
        toast.success("Campanha criada.");
      }
      voltarLista();
      load();
    } catch (e: unknown) {
      const msg = extractSaveError(e, "Erro ao salvar");
      if (msg === "SESSION_ENDED") return;
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const confirmarExclusao = async () => {
    const c = excluirCampanha;
    if (!c) return;
    setExcluindo(true);
    try {
      await deleteClinicaBelezaEntity(`/campanhas/${c.id}/`, "Erro ao excluir.");
      toast.success("Campanha excluída.");
      if (editId === c.id) voltarLista();
      setExcluirCampanha(null);
      load();
    } catch (e: unknown) {
      if (e instanceof Error && e.message === "SESSION_ENDED") return;
      toast.error("Erro ao excluir campanha.");
    } finally {
      setExcluindo(false);
    }
  };

  if (isFormView) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title={editing ? "Editar campanha" : "Nova campanha"}
          subtitle={editing ? editing.titulo : "Crie promoções para enviar por WhatsApp"}
          backHref={basePath}
          icon={Megaphone}
        />
        <ClinicaBelezaPageContent>
          <ClinicaBelezaPanel className="p-6 md:p-8 max-w-2xl">
            {error && (
              <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg mb-4">{error}</p>
            )}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Título da promoção *</label>
                <input
                  value={form.titulo}
                  onChange={(e) => setForm((f) => ({ ...f, titulo: toUpperCase(e.target.value) }))}
                  className={CLINICA_FORM_INPUT}
                  placeholder="Ex: Black Friday - 30% off"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mensagem (WhatsApp) *</label>
                <textarea
                  value={form.mensagem}
                  onChange={(e) => setForm((f) => ({ ...f, mensagem: e.target.value }))}
                  rows={6}
                  className={`${CLINICA_FORM_INPUT} resize-none`}
                  placeholder="Texto que será enviado para os pacientes..."
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Vigência início</label>
                  <input
                    type="date"
                    value={form.data_inicio}
                    onChange={(e) => setForm((f) => ({ ...f, data_inicio: e.target.value }))}
                    className={CLINICA_FORM_INPUT}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Vigência fim</label>
                  <input
                    type="date"
                    value={form.data_fim}
                    onChange={(e) => setForm((f) => ({ ...f, data_fim: e.target.value }))}
                    className={CLINICA_FORM_INPUT}
                  />
                </div>
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.ativa}
                  onChange={(e) => setForm((f) => ({ ...f, ativa: e.target.checked }))}
                  className="rounded border-gray-300 dark:border-neutral-600"
                  style={{ accentColor: CLINICA_BELEZA_PRIMARY }}
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Campanha ativa</span>
              </label>
            </div>
            <div className="flex gap-3 mt-8 pt-6 border-t border-gray-200 dark:border-neutral-700">
              <button
                type="button"
                onClick={voltarLista}
                className="flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium"
              >
                <ArrowLeft size={16} />
                Cancelar
              </button>
              <button
                type="button"
                onClick={save}
                disabled={saving}
                className="flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-white text-sm font-medium disabled:opacity-50"
                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
              >
                <Save size={16} />
                {saving ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </ClinicaBelezaPanel>
        </ClinicaBelezaPageContent>
      </>
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Campanhas de Promoções"
        subtitle="Crie promoções e envie por WhatsApp para os pacientes"
        icon={Megaphone}
        newLabel="Nova Campanha"
        onNew={abrirNovo}
      />
      <ClinicaBelezaPageContent>
        {loading ? (
          <div className="text-center py-16 text-gray-500">Carregando...</div>
        ) : list.length === 0 ? (
          <ClinicaBelezaPanel className="p-12 text-center text-gray-500 text-sm">
            Nenhuma campanha cadastrada. Clique em <strong>Nova Campanha</strong> para começar.
          </ClinicaBelezaPanel>
        ) : (
          <ClinicaBelezaPanel>
            <EntityListTable
              rows={list}
              rowKey={(c) => c.id}
              onRowClick={(c) => abrirEditar(c.id)}
              columns={[
                {
                  key: "titulo",
                  header: "Campanha",
                  render: (c) => (
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{c.titulo}</p>
                      <p className="text-sm text-gray-500 line-clamp-1 mt-0.5">{c.mensagem}</p>
                    </div>
                  ),
                },
                {
                  key: "vigencia",
                  header: "Vigência",
                  className: "hidden md:table-cell",
                  render: (c) => (
                    <span className="text-xs text-gray-500">
                      {c.data_inicio ? formatClinicaDataCurta(new Date(c.data_inicio)) : "—"}
                      {c.data_fim ? ` → ${formatClinicaDataCurta(new Date(c.data_fim))}` : ""}
                    </span>
                  ),
                },
                {
                  key: "envio",
                  header: "Envio",
                  className: "hidden lg:table-cell",
                  render: (c) =>
                    c.enviada_em ? (
                      <span className="text-xs text-green-600 dark:text-green-400">
                        {formatClinicaDateTime(new Date(c.enviada_em))} · {c.total_enviados} pac.
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">Não enviada</span>
                    ),
                },
              ]}
              trailingCell={(c) => (
                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    onClick={() => setEnviarCampanha(c)}
                    className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg"
                    title="Enviar WhatsApp"
                  >
                    <Send size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={() => abrirEditar(c.id)}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-700"
                    title="Editar"
                  >
                    <Pencil size={16} style={{ color: CLINICA_BELEZA_PRIMARY }} />
                  </button>
                  <button
                    type="button"
                    onClick={() => setExcluirCampanha(c)}
                    className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                    title="Excluir"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              )}
            />
            <EntityListLoadMore
              page={page}
              totalPages={totalPages}
              totalCount={totalCount ?? 0}
              pageSize={pageSize}
              loading={loading}
              onPageChange={setPage}
              itemLabel="campanhas"
            />
          </ClinicaBelezaPanel>
        )}
      </ClinicaBelezaPageContent>

      <CampanhaEnviarModal
        open={!!enviarCampanha}
        campanha={enviarCampanha}
        onClose={() => setEnviarCampanha(null)}
        onSent={load}
      />

      {excluirCampanha && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Excluir campanha</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              Excluir <strong>{excluirCampanha.titulo}</strong>? Esta ação não pode ser desfeita.
            </p>
            <div className="flex gap-3 mt-6">
              <button
                type="button"
                onClick={() => setExcluirCampanha(null)}
                className="flex-1 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={confirmarExclusao}
                disabled={excluindo}
                className="flex-1 py-2.5 rounded-lg bg-red-600 text-white text-sm font-medium disabled:opacity-50"
              >
                {excluindo ? "Excluindo..." : "Excluir"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
