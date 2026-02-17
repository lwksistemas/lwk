"use client";

/**
 * Cadastro de Pacientes - Clínica da Beleza
 * Listagem + criar/editar (integrado com API e permissões)
 */

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Plus, Pencil, Trash2, X, Moon, Sun } from "lucide-react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import { OfflineIndicator } from "@/components/clinica-beleza/OfflineIndicator";
import { buscarPacientesOffline, salvarPacientesOffline } from "@/lib/offline-db";

/** Monta mensagem legível a partir de serializer.errors (400) da API */
function formatApiValidationErrors(err: Record<string, unknown>): string {
  if (err?.detail && typeof err.detail === "string") return err.detail;
  const msgs: string[] = [];
  const labels: Record<string, string> = {
    name: "Nome",
    phone: "Telefone",
    email: "E-mail",
    cpf: "CPF",
    birth_date: "Data de Nascimento",
    address: "Endereço",
    notes: "Observações",
  };
  for (const [key, val] of Object.entries(err)) {
    if (Array.isArray(val) && val.length) {
      const label = labels[key] || key;
      msgs.push(`${label}: ${val[0]}`);
    }
  }
  return msgs.length ? msgs.join(". ") : "";
}

interface Patient {
  id: number;
  name: string;
  phone: string;
  email: string | null;
  cpf: string | null;
  birth_date: string | null;
  address: string | null;
  notes: string | null;
  active: boolean;
  allow_whatsapp?: boolean;
}

export default function PacientesPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const [list, setList] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Patient | null>(null);
  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    cpf: "",
    birth_date: "",
    address: "",
    notes: "",
    allow_whatsapp: true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      if (!navigator.onLine) {
        const data = await buscarPacientesOffline();
        setList(Array.isArray(data) ? (data as Patient[]) : []);
      } else {
        const res = await clinicaBelezaFetch("/patients/");
        const data = await res.json();
        if (res.ok) {
          const arr = Array.isArray(data) ? data : [];
          setList(arr);
          await salvarPacientesOffline(arr);
        } else setList([]);
      }
    } catch {
      setList([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (searchParams.get("novo") === "1") openNew();
  }, [searchParams]);

  const openNew = () => {
    setEditing(null);
    setForm({
      name: "",
      phone: "",
      email: "",
      cpf: "",
      birth_date: "",
      address: "",
      notes: "",
      allow_whatsapp: true,
    });
    setError("");
    setShowModal(true);
  };

  const openEdit = (p: Patient) => {
    setEditing(p);
    setForm({
      name: p.name,
      phone: p.phone || "",
      email: p.email || "",
      cpf: p.cpf || "",
      birth_date: p.birth_date ? p.birth_date.slice(0, 10) : "",
      address: p.address || "",
      notes: p.notes || "",
      allow_whatsapp: p.allow_whatsapp !== false,
    });
    setError("");
    setShowModal(true);
  };

  const save = async () => {
    if (!form.name.trim()) {
      setError("Nome é obrigatório.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const body = {
        name: form.name.trim(),
        phone: form.phone.trim() || null,
        email: form.email.trim() || null,
        cpf: form.cpf.trim() || null,
        birth_date: form.birth_date || null,
        address: form.address.trim() || null,
        notes: form.notes.trim() || null,
        active: true,
        allow_whatsapp: form.allow_whatsapp,
      };
      if (editing) {
        const res = await clinicaBelezaFetch(`/patients/${editing.id}/`, {
          method: "PUT",
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(formatApiValidationErrors(err) || "Erro ao atualizar");
        }
      } else {
        const res = await clinicaBelezaFetch("/patients/", {
          method: "POST",
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(formatApiValidationErrors(err) || "Erro ao cadastrar");
        }
      }
      setShowModal(false);
      load();
    } catch (e: unknown) {
      if (e instanceof Error && e.message === "SESSION_ENDED") return;
      setError(e instanceof Error ? e.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  };

  const exclude = async (p: Patient) => {
    if (!confirm(`Desativar o paciente "${p.name}"?`)) return;
    try {
      await clinicaBelezaFetch(`/patients/${p.id}/`, { method: "DELETE" });
      load();
    } catch {
      alert("Erro ao desativar.");
    }
  };

  const activeList = list.filter((p) => p.active);

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
            <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Pacientes</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Cadastro de pacientes da clínica</p>
          </div>
          <div className="flex items-center gap-2">
            <OfflineIndicator />
            <button
              onClick={openNew}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              <Plus size={20} />
              Novo Paciente
            </button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : activeList.length === 0 ? (
          <div className="bg-white/80 dark:bg-neutral-800/80 rounded-xl p-8 text-center text-gray-500 dark:text-gray-400">
            Nenhum paciente cadastrado. Clique em &quot;Novo Paciente&quot; para começar.
          </div>
        ) : (
          <div className="bg-white/80 dark:bg-neutral-800/80 rounded-xl shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 dark:bg-neutral-700 text-gray-600 dark:text-gray-300">
                  <tr>
                    <th className="text-left p-3">Nome</th>
                    <th className="text-left p-3">Telefone</th>
                    <th className="text-left p-3 hidden md:table-cell">E-mail</th>
                    <th className="w-24 p-3">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {activeList.map((p) => (
                    <tr key={p.id} className="border-t border-gray-100 dark:border-neutral-700">
                      <td className="p-3 font-medium text-gray-800 dark:text-gray-200">{p.name}</td>
                      <td className="p-3 text-gray-700 dark:text-gray-300">{p.phone || "—"}</td>
                      <td className="p-3 hidden md:table-cell text-gray-700 dark:text-gray-300">{p.email || "—"}</td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => openEdit(p)}
                            className="p-2 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded"
                            title="Editar"
                          >
                            <Pencil size={18} />
                          </button>
                          <button
                            onClick={() => exclude(p)}
                            className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                            title="Desativar"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center p-4 border-b dark:border-neutral-600">
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editing ? "Editar Paciente" : "Novo Paciente"}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded">
                <X size={20} className="text-gray-700 dark:text-gray-300" />
              </button>
            </div>
            <div className="p-4 space-y-3">
              {error && (
                <div className="p-2 rounded bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">{error}</div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="Nome completo"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label>
                <input
                  value={form.phone}
                  onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="(00) 00000-0000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">E-mail</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="email@exemplo.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">CPF</label>
                <input
                  value={form.cpf}
                  onChange={(e) => setForm((f) => ({ ...f, cpf: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="000.000.000-00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data de Nascimento</label>
                <input
                  type="date"
                  value={form.birth_date}
                  onChange={(e) => setForm((f) => ({ ...f, birth_date: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Endereço</label>
                <input
                  value={form.address}
                  onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="Rua, número, bairro"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                  rows={2}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg resize-none bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="Observações"
                />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.allow_whatsapp}
                  onChange={(e) => setForm((f) => ({ ...f, allow_whatsapp: e.target.checked }))}
                  className="rounded border-gray-300 dark:border-neutral-600 text-purple-600"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Permitir WhatsApp (lembretes e cobranças) — LGPD: o paciente pode optar por não receber
                </span>
              </label>
            </div>
            <div className="flex gap-2 p-4 border-t dark:border-neutral-600">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 text-gray-700 dark:text-gray-300"
              >
                Cancelar
              </button>
              <button
                onClick={save}
                disabled={saving}
                className="flex-1 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
              >
                {saving ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
