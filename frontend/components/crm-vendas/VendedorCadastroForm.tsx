'use client';

import { ArrowLeft, Shield, User } from 'lucide-react';
import Link from 'next/link';
import { CrmFormPageShell } from '@/components/crm-vendas/CrmFormPageShell';
import { formatTelefone, toUpperCase } from '@/lib/format-br';
import {
  suggestLoginFromNome,
  type CrmFuncionarioFormData,
  type CrmFuncionarioGrupo,
  type CrmPermissaoCategoria,
} from '@/lib/crm-funcionarios';

const inputClass =
  'w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0176d3] focus:ring-offset-0';
const labelClass = 'block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1';
const sectionTitleClass =
  'text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-[#0d1f3c] pb-2 flex items-center gap-2';

interface Props {
  listHref: string;
  editing?: boolean;
  form: CrmFuncionarioFormData;
  setForm: React.Dispatch<React.SetStateAction<CrmFuncionarioFormData>>;
  grupos: CrmFuncionarioGrupo[];
  permissoesCategorias: CrmPermissaoCategoria[];
  loading?: boolean;
  error?: string | null;
  saving?: boolean;
  onGrupoChange: (grupoId: string) => void;
  onTogglePermissao: (permId: number, checked: boolean) => void;
  onToggleCriarAcesso: (checked: boolean) => void;
  onSave: () => void;
  onCancel: () => void;
}

export function VendedorCadastroForm({
  listHref,
  editing = false,
  form,
  setForm,
  grupos,
  permissoesCategorias,
  loading = false,
  error,
  saving = false,
  onGrupoChange,
  onTogglePermissao,
  onToggleCriarAcesso,
  onSave,
  onCancel,
}: Props) {
  if (loading) {
    return (
      <div className="-m-4 sm:-m-6 lg:-m-8 flex items-center justify-center min-h-[calc(100dvh-3.5rem)] text-gray-500">
        Carregando...
      </div>
    );
  }

  return (
    <div className="-m-4 sm:-m-6 lg:-m-8 flex flex-col min-h-[calc(100dvh-3.5rem)]">
      <div className="shrink-0 px-4 md:px-6 lg:px-8 py-4 bg-[#f3f2f2] dark:bg-[#0d1f3c] border-b border-gray-200 dark:border-[#0d1f3c]">
        <Link
          href={listHref}
          className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-[#0176d3]"
        >
          <ArrowLeft size={16} />
          Voltar à listagem
        </Link>
        <h1 className="mt-3 text-xl font-semibold text-gray-900 dark:text-white">
          {editing ? 'Editar funcionário' : 'Novo funcionário'}
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Dados pessoais e permissões de acesso ao CRM
        </p>
      </div>

      <CrmFormPageShell
        error={error}
        saving={saving}
        saveLabel={editing ? 'Salvar alterações' : 'Cadastrar funcionário'}
        onSave={onSave}
        onCancel={onCancel}
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full">
          <section className="space-y-4">
            <h2 className={sectionTitleClass}>
              <User size={16} className="text-[#0176d3]" />
              Dados pessoais
            </h2>
            <div>
              <label className={labelClass}>Nome *</label>
              <input
                type="text"
                value={form.nome}
                onChange={(e) => {
                  const nome = toUpperCase(e.target.value);
                  setForm((f) => ({
                    ...f,
                    nome,
                    username:
                      f.criar_acesso && (!f.username || f.username === suggestLoginFromNome(f.nome))
                        ? suggestLoginFromNome(nome)
                        : f.username,
                  }));
                }}
                className={inputClass}
                placeholder="Nome do vendedor"
              />
            </div>
            <div>
              <label className={labelClass}>Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                className={inputClass}
                placeholder="email@exemplo.com"
              />
            </div>
            <div>
              <label className={labelClass}>Telefone</label>
              <input
                type="text"
                value={form.telefone}
                onChange={(e) => setForm((f) => ({ ...f, telefone: formatTelefone(e.target.value) }))}
                className={inputClass}
                placeholder="(11) 99999-9999"
              />
            </div>
            <div>
              <label className={labelClass}>Cargo</label>
              <input
                type="text"
                value={form.cargo}
                onChange={(e) => setForm((f) => ({ ...f, cargo: toUpperCase(e.target.value) }))}
                className={inputClass}
                placeholder="Vendedor"
              />
            </div>
            <div>
              <label className={labelClass}>Comissão padrão (%)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={form.comissao_padrao}
                onChange={(e) => setForm((f) => ({ ...f, comissao_padrao: e.target.value }))}
                className={inputClass}
                placeholder="Ex: 5.00"
              />
            </div>
          </section>

          <section className="space-y-4">
            <h2 className={sectionTitleClass}>
              <Shield size={16} className="text-[#0176d3]" />
              Acesso e permissões
            </h2>

            <div>
              <label className={labelClass}>Perfil / grupo</label>
              <select
                value={form.grupo_id}
                onChange={(e) => onGrupoChange(e.target.value)}
                className={inputClass}
              >
                <option value="">Selecione um perfil (opcional)</option>
                {grupos.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.name}
                  </option>
                ))}
              </select>
            </div>

            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={form.criar_acesso}
                onChange={(e) => onToggleCriarAcesso(e.target.checked)}
                className="mt-1 rounded border-gray-300 dark:border-gray-600 text-[#0176d3]"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {editing
                  ? 'Criar ou reenviar acesso ao sistema e enviar senha provisória por e-mail'
                  : 'Criar acesso ao sistema e enviar senha provisória por e-mail'}
              </span>
            </label>

            {form.criar_acesso && (
              <div className="space-y-3 pl-4 border-l-2 border-blue-200 dark:border-blue-800">
                <div>
                  <label className={labelClass}>Usuário para login *</label>
                  <input
                    type="text"
                    value={form.username}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        username: e.target.value.toLowerCase().replace(/[^a-z0-9._-]/g, ''),
                      }))
                    }
                    className={inputClass}
                    placeholder="Ex: daniel"
                  />
                </div>
                <div>
                  <label className={labelClass}>E-mail para envio da senha *</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                    className={inputClass}
                    placeholder="email@exemplo.com"
                  />
                </div>
              </div>
            )}

            <div className="space-y-4 pt-2">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Permissões granulares</p>
              {permissoesCategorias.map((cat) => (
                <div key={cat.categoria} className="space-y-2">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    {cat.categoria}
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {cat.permissoes.map((perm) => (
                      <label
                        key={perm.id}
                        className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={form.permissoes_ids.includes(perm.id)}
                          onChange={(e) => onTogglePermissao(perm.id, e.target.checked)}
                          className="mt-0.5 rounded border-gray-300 dark:border-gray-600 text-[#0176d3]"
                        />
                        <span>{perm.nome}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </CrmFormPageShell>
    </div>
  );
}
