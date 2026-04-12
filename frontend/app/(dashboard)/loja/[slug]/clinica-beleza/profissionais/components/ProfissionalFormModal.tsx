'use client';

import { X } from 'lucide-react';

type PerfilAcesso = 'administrador' | 'profissional' | 'recepcao';

interface FormData {
  name: string;
  specialty: string;
  phone: string;
  email: string;
  criar_acesso: boolean;
  perfil: PerfilAcesso;
}

interface Props {
  editing: boolean;
  form: FormData;
  saving: boolean;
  error: string;
  onChange: (form: FormData) => void;
  onSave: () => void;
  onClose: () => void;
}

const inputClass = 'w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100';

export function ProfissionalFormModal({ editing, form, saving, error, onChange, onSave, onClose }: Props) {
  const set = (field: keyof FormData, value: string | boolean) => onChange({ ...form, [field]: value });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-md border dark:border-neutral-700">
        <div className="flex justify-between items-center p-4 border-b dark:border-neutral-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
            {editing ? 'Editar Profissional' : 'Novo Profissional'}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded"><X size={20} /></button>
        </div>
        <div className="p-4 space-y-3">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
              <div className="flex items-start gap-2">
                <span className="text-red-600 dark:text-red-400 text-lg">⚠️</span>
                <p className="text-sm font-medium text-red-800 dark:text-red-300 whitespace-pre-line">{error}</p>
              </div>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
            <input value={form.name} onChange={(e) => set('name', e.target.value)} className={inputClass} placeholder="Nome completo" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Especialidade *</label>
            <input value={form.specialty} onChange={(e) => set('specialty', e.target.value)} className={inputClass} placeholder="Ex.: Esteticista" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label>
            <input value={form.phone} onChange={(e) => set('phone', e.target.value)} className={inputClass} placeholder="(00) 00000-0000" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">E-mail</label>
            <input type="email" value={form.email} onChange={(e) => set('email', e.target.value)} className={inputClass} placeholder="email@exemplo.com" />
          </div>
          {!editing && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo (permissões)</label>
                <select value={form.perfil} onChange={(e) => set('perfil', e.target.value)} className={inputClass}>
                  <option value="administrador">Administrador</option>
                  <option value="profissional">Profissional</option>
                  <option value="recepcao">Recepção</option>
                </select>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Define as permissões se criar login abaixo.</p>
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={form.criar_acesso} onChange={(e) => set('criar_acesso', e.target.checked)} className="rounded border-gray-300 dark:border-neutral-600 text-purple-600" />
                <span className="text-sm text-gray-700 dark:text-gray-300">Criar acesso e enviar senha por e-mail</span>
              </label>
            </>
          )}
        </div>
        <div className="flex gap-2 p-4 border-t dark:border-neutral-700">
          <button onClick={onClose} className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 text-gray-700 dark:text-gray-300">Cancelar</button>
          <button onClick={onSave} disabled={saving} className="flex-1 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50">{saving ? 'Salvando...' : 'Salvar'}</button>
        </div>
      </div>
    </div>
  );
}
