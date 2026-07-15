'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { Edit2, Trash2, Users } from 'lucide-react';
import {
  PacienteCadastroForm,
  PACIENTE_EMPTY_FORM,
  type PacienteFormState,
} from '@/components/clinica-beleza/paciente-cadastro/PacienteCadastroForm';
import { SalaoPageHeader } from '@/components/cabeleireiro/SalaoPageHeader';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';
import { CabeleireiroAPI, type SalaoCliente } from '@/lib/cabeleireiro-api';
import { consultaCep } from '@/lib/consulta-cep';
import { applyTelefoneInternacionalPayload, formatCep, formatTelefone, toUpperCase } from '@/lib/format-br';

function clienteToForm(c: SalaoCliente): PacienteFormState {
  return {
    ...PACIENTE_EMPTY_FORM,
    name: c.name || c.nome || '',
    phone: formatTelefone(c.phone || c.telefone || ''),
    email: c.email || '',
    cpf: c.cpf || '',
    birth_date: (c.birth_date || c.data_nascimento || '')?.toString().slice(0, 10) || '',
    cep: c.cep || '',
    logradouro: c.logradouro || '',
    numero: c.numero || '',
    complemento: c.complemento || '',
    bairro: c.bairro || '',
    cidade: c.cidade || '',
    uf: c.estado || '',
    notes: c.notes || c.observacoes || '',
    allow_whatsapp: c.allow_whatsapp !== false,
    foto_url: c.foto_url || '',
  };
}

export default function SalaoClientesPage() {
  const slug = useParams()?.slug as string;
  const router = useRouter();
  const searchParams = useSearchParams();
  const editId = searchParams?.get('id');
  const isNovo = searchParams?.get('novo') === '1';
  const isForm = isNovo || Boolean(editId);

  const [list, setList] = useState<SalaoCliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [form, setForm] = useState<PacienteFormState>(PACIENTE_EMPTY_FORM);
  const [editing, setEditing] = useState<SalaoCliente | null>(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [buscarCepLoading, setBuscarCepLoading] = useState(false);

  const base = `/loja/${slug}/cabeleireiro/clientes`;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setList(await CabeleireiroAPI.clientes.list({ search: search || undefined }));
    } catch {
      setList([]);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (isNovo) {
      setEditing(null);
      setForm(PACIENTE_EMPTY_FORM);
      setError('');
      return;
    }
    if (!editId) return;
    const found = list.find((c) => String(c.id) === editId);
    if (found) {
      setEditing(found);
      setForm(clienteToForm(found));
      return;
    }
    void CabeleireiroAPI.clientes
      .get(Number(editId))
      .then((c) => {
        setEditing(c);
        setForm(clienteToForm(c));
      })
      .catch(() => setError('Cliente não encontrado'));
  }, [isNovo, editId, list]);

  const voltar = () => router.push(base);
  const abrirNovo = () => router.push(`${base}?novo=1`);
  const abrirEditar = (id: number) => router.push(`${base}?id=${id}`);

  const handleCepChange = (value: string) => {
    setForm((f) => ({ ...f, cep: formatCep(value) }));
  };

  const handleBuscarCep = async () => {
    const digits = form.cep.replace(/\D/g, '');
    if (digits.length !== 8) return;
    setBuscarCepLoading(true);
    try {
      const data = await consultaCep(digits);
      if (data) {
        setForm((f) => ({
          ...f,
          logradouro: toUpperCase(data.logradouro || ''),
          bairro: toUpperCase(data.bairro || ''),
          cidade: toUpperCase(data.cidade || ''),
          uf: (data.uf || '').toUpperCase(),
        }));
      }
    } finally {
      setBuscarCepLoading(false);
    }
  };

  const save = async () => {
    if (!form.name.trim()) {
      setError('Nome é obrigatório');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const payload = applyTelefoneInternacionalPayload({
        name: form.name.trim(),
        nome: form.name.trim(),
        phone: form.phone,
        telefone: form.phone,
        email: form.email,
        cpf: form.cpf,
        birth_date: form.birth_date || null,
        data_nascimento: form.birth_date || null,
        cep: form.cep,
        logradouro: form.logradouro,
        numero: form.numero,
        complemento: form.complemento,
        bairro: form.bairro,
        cidade: form.cidade,
        estado: form.uf,
        notes: form.notes,
        observacoes: form.notes,
        allow_whatsapp: form.allow_whatsapp,
        foto_url: form.foto_url,
        endereco: [form.logradouro, form.numero, form.bairro].filter(Boolean).join(', '),
      });
      if (editing) await CabeleireiroAPI.clientes.update(editing.id, payload);
      else await CabeleireiroAPI.clientes.create(payload);
      await load();
      voltar();
    } catch (e: unknown) {
      const data =
        e && typeof e === 'object' && 'response' in e
          ? (e as { response?: { data?: Record<string, unknown> } }).response?.data
          : null;
      const detail =
        (typeof data?.detail === 'string' && data.detail) ||
        (typeof data?.cpf === 'string' && data.cpf) ||
        (Array.isArray(data?.cpf) && String(data.cpf[0])) ||
        (typeof data?.nome === 'string' && data.nome) ||
        (Array.isArray(data?.nome) && String(data.nome[0])) ||
        null;
      setError(detail || 'Erro ao salvar cliente');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (c: SalaoCliente) => {
    if (!confirm(`Excluir cliente "${c.nome || c.name}"?`)) return;
    try {
      await CabeleireiroAPI.clientes.remove(c.id);
      await load();
    } catch {
      alert('Erro ao excluir');
    }
  };

  if (isForm) {
    return (
      <div className="flex flex-col h-full min-h-[70vh]">
        <SalaoPageHeader
          title={editing ? 'Editar cliente' : 'Novo cliente'}
          subtitle="Cadastro no padrão da clínica"
          icon={Users}
          primary={SALAO_PRIMARY}
        />
        <PacienteCadastroForm
          showHeader={false}
          hideConvenio
          editing={Boolean(editing)}
          form={form}
          setForm={setForm}
          error={error}
          saving={saving}
          convenios={[]}
          buscarCepLoading={buscarCepLoading}
          onCepChange={handleCepChange}
          onBuscarCep={() => void handleBuscarCep()}
          onSave={() => void save()}
          onCancel={voltar}
          accentColor={SALAO_PRIMARY}
          lojaSlug={slug}
        />
      </div>
    );
  }

  return (
    <div>
      <SalaoPageHeader
        title="Clientes"
        subtitle={`${list.length} cadastrado(s)`}
        icon={Users}
        onNew={abrirNovo}
        newLabel="Novo cliente"
        primary={SALAO_PRIMARY}
      />
      <div className="p-4 md:p-6 space-y-4">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar por nome, telefone ou CPF..."
          className="w-full max-w-md px-3 py-2 rounded-lg border border-gray-200 text-sm bg-white"
        />
        {loading ? (
          <p className="text-sm text-gray-500 py-10 text-center">Carregando...</p>
        ) : list.length === 0 ? (
          <p className="text-sm text-gray-500 py-10 text-center">Nenhum cliente cadastrado</p>
        ) : (
          <div className="bg-white rounded-xl border border-[#E8D5DC] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#F7F0F3] text-left text-xs uppercase text-gray-500">
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3 hidden sm:table-cell">Telefone</th>
                  <th className="px-4 py-3 hidden md:table-cell">E-mail</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {list.map((c) => (
                  <tr key={c.id} className="hover:bg-[#F7F0F3]/50">
                    <td className="px-4 py-3 font-medium text-gray-900">{c.nome || c.name}</td>
                    <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">
                      {c.telefone || c.phone || '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-600 hidden md:table-cell">{c.email || '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1">
                        <button
                          type="button"
                          onClick={() => abrirEditar(c.id)}
                          className="p-2 rounded-md hover:bg-gray-100 text-gray-500"
                          title="Editar"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => void remove(c)}
                          className="p-2 rounded-md hover:bg-red-50 text-gray-400 hover:text-red-600"
                          title="Excluir"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
