"use client";

/**
 * Campanhas de Promoções - Clínica da Beleza
 * Criar promoções e enviar mensagem em massa por WhatsApp aos pacientes
 */

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Plus, Pencil, Trash2, X, Send } from "lucide-react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";

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

export default function CampanhasPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const [list, setList] = useState<Campanha[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Campanha | null>(null);
  const [form, setForm] = useState({
    titulo: "",
    mensagem: "",
    data_inicio: "",
    data_fim: "",
    ativa: true,
  });
  const [saving, setSaving] = useState(false);
  const [sendingId, setSendingId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await clinicaBelezaFetch("/campanhas/");
      const data = await res.json();
      if (res.ok) setList(Array.isArray(data) ? data : []);
      else setList([]);
    } catch {
      setList([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openNew = () => {
    setEditing(null);
    setForm({ titulo: "", mensagem: "", data_inicio: "", data_fim: "", ativa: true });
    setError("");
    setShowModal(true);
  };

  const openEdit = (c: Campanha) => {
    setEditing(c);
    setForm({
      titulo: c.titulo,
      mensagem: c.mensagem,
      data_inicio: c.data_inicio ? c.data_inicio.slice(0, 10) : "",
      data_fim: c.data_fim ? c.data_fim.slice(0, 10) : "",
      ativa: c.ativa,
    });
    setError("");
    setShowModal(true);
  };

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
        const res = await clinicaBelezaFetch(`/campanhas/${editing.id}/`, {
          method: "PUT",
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error || "Erro ao atualizar");
        }
      } else {
        const res = await clinicaBelezaFetch("/campanhas/", {
          method: "POST",
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error || "Erro ao cadastrar");
        }
      }
      setShowModal(false);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  };

  const enviarCampanha = async (c: Campanha) => {
    if (!confirm(`Enviar a campanha "${c.titulo}" para todos os pacientes com WhatsApp ativo?`)) return;
    setSendingId(c.id);
    try {
      const res = await clinicaBelezaFetch(`/campanhas/${c.id}/enviar/`, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.sent !== undefined) {
        alert(data.message || `Enviado para ${data.sent} paciente(s).`);
        load();
      } else {
        alert(data.error || "Não foi possível enviar. Verifique a integração WhatsApp em Configurações.");
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.message === "SESSION_ENDED") return;
      alert("Erro ao enviar. Tente novamente.");
    } finally {
      setSendingId(null);
    }
  };

  const exclude = async (c: Campanha) => {
    if (!confirm(`Excluir a campanha "${c.titulo}"?`)) return;
    try {
      await clinicaBelezaFetch(`/campanhas/${c.id}/`, { method: "DELETE" });
      load();
    } catch {
      alert("Erro ao excluir.");
    }
  };

  const [darkMode] = useClinicaBelezaDark();

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-white dark:from-neutral-900 dark:via-neutral-800 dark:to-neutral-900 text-gray-800 dark:text-gray-100 p-4 md:p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <button
            onClick={() => router.push(`/loja/${slug}/dashboard`)}
            className="p-2 hover:bg-white/80 dark:hover:bg-neutral-700 rounded-lg"
          >
            <ArrowLeft size={24} className="text-gray-800 dark:text-gray-200" />
          </button>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Campanhas de Promoções</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Crie promoções e envie por WhatsApp para os pacientes</p>
          </div>
          <button
            onClick={openNew}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            <Plus size={20} />
            Nova Campanha
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : list.length === 0 ? (
          <div className="bg-white dark:bg-neutral-800 rounded-xl p-8 text-center border border-gray-200 dark:border-neutral-700">
            <p className="text-gray-500 dark:text-gray-400 mb-4">Nenhuma campanha cadastrada.</p>
            <button
              onClick={openNew}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              Criar primeira campanha
            </button>
          </div>
        ) : (
          <ul className="space-y-3">
            {list.map((c) => (
              <li
                key={c.id}
                className="bg-white dark:bg-neutral-800 rounded-xl p-4 border border-gray-200 dark:border-neutral-700 flex flex-wrap items-center justify-between gap-3"
              >
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">{c.titulo}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mt-0.5">{c.mensagem}</p>
                  <div className="flex flex-wrap gap-2 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    {c.data_inicio && <span>De: {c.data_inicio.slice(0, 10)}</span>}
                    {c.data_fim && <span>Até: {c.data_fim.slice(0, 10)}</span>}
                    {c.enviada_em && (
                      <span className="text-green-600 dark:text-green-400">
                        Enviada em {new Date(c.enviada_em).toLocaleString("pt-BR")} — {c.total_enviados} paciente(s)
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => enviarCampanha(c)}
                    disabled={!!sendingId}
                    className="flex items-center gap-1.5 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm"
                    title="Enviar mensagem para todos os pacientes (WhatsApp)"
                  >
                    <Send size={16} />
                    {sendingId === c.id ? "Enviando…" : "Enviar WhatsApp"}
                  </button>
                  <button
                    onClick={() => openEdit(c)}
                    className="p-2 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-neutral-700 rounded-lg"
                    title="Editar"
                  >
                    <Pencil size={18} />
                  </button>
                  <button
                    onClick={() => exclude(c)}
                    className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-neutral-700 rounded-lg"
                    title="Excluir"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}

        {/* Modal criar/editar */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <div className="p-4 border-b dark:border-neutral-700 flex justify-between items-center">
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                  {editing ? "Editar campanha" : "Nova campanha"}
                </h2>
                <button onClick={() => setShowModal(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
                  <X size={20} />
                </button>
              </div>
              <div className="p-4 space-y-4">
                {error && (
                  <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">{error}</p>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Título da promoção *</label>
                  <input
                    value={form.titulo}
                    onChange={(e) => setForm((f) => ({ ...f, titulo: e.target.value }))}
                    className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                    placeholder="Ex: Black Friday - 30% off"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mensagem (WhatsApp) *</label>
                  <textarea
                    value={form.mensagem}
                    onChange={(e) => setForm((f) => ({ ...f, mensagem: e.target.value }))}
                    rows={5}
                    className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 resize-none"
                    placeholder="Texto que será enviado para os pacientes..."
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Vigência início</label>
                    <input
                      type="date"
                      value={form.data_inicio}
                      onChange={(e) => setForm((f) => ({ ...f, data_inicio: e.target.value }))}
                      className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Vigência fim</label>
                    <input
                      type="date"
                      value={form.data_fim}
                      onChange={(e) => setForm((f) => ({ ...f, data_fim: e.target.value }))}
                      className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                    />
                  </div>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.ativa}
                    onChange={(e) => setForm((f) => ({ ...f, ativa: e.target.checked }))}
                    className="rounded border-gray-300 dark:border-neutral-600 text-purple-600"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Campanha ativa</span>
                </label>
              </div>
              <div className="p-4 border-t dark:border-neutral-700 flex gap-2">
                <button
                  onClick={() => setShowModal(false)}
                  className="flex-1 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg hover:bg-gray-50 dark:hover:bg-neutral-700"
                >
                  Cancelar
                </button>
                <button
                  onClick={save}
                  disabled={saving}
                  className="flex-1 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                >
                  {saving ? "Salvando..." : "Salvar"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
