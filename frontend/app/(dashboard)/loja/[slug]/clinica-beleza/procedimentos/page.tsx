"use client";

/**
 * Cadastro de Procedimentos - Clínica da Beleza
 */

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Plus, Pencil, Trash2, X } from "lucide-react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";

interface Procedure {
  id: number;
  name: string;
  description: string | null;
  price: string;
  duration: number;
  active: boolean;
}

export default function ProcedimentosPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const [list, setList] = useState<Procedure[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Procedure | null>(null);
  const [form, setForm] = useState({
    name: "",
    description: "",
    price: "",
    duration: "30",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await clinicaBelezaFetch("/procedures/");
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
    setForm({ name: "", description: "", price: "", duration: "30" });
    setError("");
    setShowModal(true);
  };

  const openEdit = (p: Procedure) => {
    setEditing(p);
    setForm({
      name: p.name,
      description: p.description || "",
      price: String(p.price),
      duration: String(p.duration),
    });
    setError("");
    setShowModal(true);
  };

  const save = async () => {
    if (!form.name.trim()) {
      setError("Nome é obrigatório.");
      return;
    }
    const duration = parseInt(form.duration, 10);
    const price = parseFloat(form.price.replace(",", "."));
    if (isNaN(duration) || duration < 1) {
      setError("Duração deve ser um número positivo (minutos).");
      return;
    }
    if (isNaN(price) || price < 0) {
      setError("Preço inválido.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const body = {
        name: form.name.trim(),
        description: form.description.trim() || null,
        price: price.toFixed(2),
        duration,
        active: true,
      };
      if (editing) {
        const res = await clinicaBelezaFetch(`/procedures/${editing.id}/`, {
          method: "PUT",
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.name?.[0] || err.detail || "Erro ao atualizar");
        }
      } else {
        const res = await clinicaBelezaFetch("/procedures/", {
          method: "POST",
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.name?.[0] || err.detail || "Erro ao cadastrar");
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

  const exclude = async (p: Procedure) => {
    if (!confirm(`Desativar o procedimento "${p.name}"?`)) return;
    try {
      await clinicaBelezaFetch(`/procedures/${p.id}/`, { method: "DELETE" });
      load();
    } catch {
      alert("Erro ao desativar.");
    }
  };

  const activeList = list.filter((p) => p.active);

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-white p-4 md:p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={() => router.push(`/loja/${slug}/dashboard`)}
            className="p-2 hover:bg-white/80 rounded-lg"
          >
            <ArrowLeft size={24} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Procedimentos</h1>
            <p className="text-sm text-gray-500">Serviços e procedimentos oferecidos</p>
          </div>
          <button
            onClick={openNew}
            className="ml-auto flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            <Plus size={20} />
            Novo Procedimento
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500">Carregando...</div>
        ) : activeList.length === 0 ? (
          <div className="bg-white/80 rounded-xl p-8 text-center text-gray-500">
            Nenhum procedimento cadastrado. Clique em &quot;Novo Procedimento&quot; para começar.
          </div>
        ) : (
          <div className="bg-white/80 rounded-xl shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 text-gray-600">
                  <tr>
                    <th className="text-left p-3">Nome</th>
                    <th className="text-left p-3">Duração</th>
                    <th className="text-left p-3">Preço</th>
                    <th className="w-24 p-3">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {activeList.map((p) => (
                    <tr key={p.id} className="border-t border-gray-100">
                      <td className="p-3 font-medium">{p.name}</td>
                      <td className="p-3">{p.duration} min</td>
                      <td className="p-3">R$ {Number(p.price).toFixed(2).replace(".", ",")}</td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => openEdit(p)}
                            className="p-2 text-purple-600 hover:bg-purple-50 rounded"
                            title="Editar"
                          >
                            <Pencil size={18} />
                          </button>
                          <button
                            onClick={() => exclude(p)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded"
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
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex justify-between items-center p-4 border-b">
              <h2 className="text-lg font-bold">
                {editing ? "Editar Procedimento" : "Novo Procedimento"}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-gray-100 rounded">
                <X size={20} />
              </button>
            </div>
            <div className="p-4 space-y-3">
              {error && (
                <div className="p-2 rounded bg-red-50 text-red-700 text-sm">{error}</div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="Ex.: Limpeza de pele"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Duração (min) *</label>
                <input
                  type="number"
                  min={1}
                  value={form.duration}
                  onChange={(e) => setForm((f) => ({ ...f, duration: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Preço (R$) *</label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={form.price}
                  onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="0,00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  rows={2}
                  className="w-full px-3 py-2 border rounded-lg resize-none"
                  placeholder="Descrição opcional"
                />
              </div>
            </div>
            <div className="flex gap-2 p-4 border-t">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 py-2 rounded-lg border border-gray-300 hover:bg-gray-50"
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
