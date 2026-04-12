'use client';

import { X } from 'lucide-react';

export interface ContaFormData {
  nome: string; razao_social: string; cnpj: string; inscricao_estadual: string;
  segmento: string; telefone: string; email: string; site: string;
  cep: string; logradouro: string; numero: string; complemento: string;
  bairro: string; cidade: string; uf: string; observacoes: string;
}

interface Props {
  title: string;
  formData: ContaFormData;
  submitting: boolean;
  consultingCNPJ: boolean;
  onChange: (data: ContaFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  onClose: () => void;
  onConsultarCNPJ: () => void;
  onConsultarCEP: () => void;
}

const inputClass = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent";

export function ContaFormModal({ title, formData, submitting, consultingCNPJ, onChange, onSubmit, onClose, onConsultarCNPJ, onConsultarCEP }: Props) {
  const set = (field: keyof ContaFormData, value: string) => onChange({ ...formData, [field]: value });

  return (
    <ModalShell title={title} onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-4">
        {/* CNPJ Lookup */}
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">CNPJ</label>
              <input type="text" value={formData.cnpj} onChange={(e) => set('cnpj', e.target.value)} className={inputClass} placeholder="00.000.000/0000-00" maxLength={18} />
            </div>
            <div className="flex items-end">
              <button type="button" onClick={onConsultarCNPJ} disabled={consultingCNPJ || !formData.cnpj} className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition-colors disabled:opacity-50">
                {consultingCNPJ ? 'Consultando...' : 'Consultar CNPJ'}
              </button>
            </div>
          </div>
          <p className="text-xs text-blue-700 dark:text-blue-300 mt-2">💡 Consulte o CNPJ para preencher automaticamente</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Razão Social</label>
            <input type="text" value={formData.razao_social} onChange={(e) => set('razao_social', e.target.value)} className={inputClass} />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome Fantasia <span className="text-red-500">*</span></label>
            <input type="text" value={formData.nome} onChange={(e) => set('nome', e.target.value)} className={inputClass} required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Inscrição Estadual</label>
            <input type="text" value={formData.inscricao_estadual} onChange={(e) => set('inscricao_estadual', e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Segmento</label>
            <input type="text" value={formData.segmento} onChange={(e) => set('segmento', e.target.value)} className={inputClass} placeholder="Ex: Tecnologia, Varejo" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label>
            <input type="tel" value={formData.telefone} onChange={(e) => set('telefone', e.target.value)} className={inputClass} placeholder="(00) 00000-0000" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
            <input type="email" value={formData.email} onChange={(e) => set('email', e.target.value)} className={inputClass} />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Site</label>
            <input type="url" value={formData.site} onChange={(e) => set('site', e.target.value)} className={inputClass} placeholder="https://exemplo.com.br" />
          </div>

          {/* Endereço */}
          <div className="md:col-span-2"><hr className="border-gray-200 dark:border-gray-700 my-2" /><h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Endereço</h3></div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">CEP</label>
            <input type="text" value={formData.cep} onChange={(e) => set('cep', e.target.value)} onBlur={onConsultarCEP} className={inputClass} placeholder="00000-000" maxLength={9} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">UF</label>
            <input type="text" value={formData.uf} onChange={(e) => set('uf', e.target.value.toUpperCase())} className={inputClass} placeholder="SP" maxLength={2} />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Logradouro</label>
            <input type="text" value={formData.logradouro} onChange={(e) => set('logradouro', e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Número</label>
            <input type="text" value={formData.numero} onChange={(e) => set('numero', e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Complemento</label>
            <input type="text" value={formData.complemento} onChange={(e) => set('complemento', e.target.value)} className={inputClass} placeholder="Apto, Sala" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Bairro</label>
            <input type="text" value={formData.bairro} onChange={(e) => set('bairro', e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cidade</label>
            <input type="text" value={formData.cidade} onChange={(e) => set('cidade', e.target.value)} className={inputClass} />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
            <textarea value={formData.observacoes} onChange={(e) => set('observacoes', e.target.value)} rows={3} className={inputClass} />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} disabled={submitting} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">Cancelar</button>
          <button type="submit" disabled={submitting} className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded disabled:opacity-50">{submitting ? 'Salvando...' : 'Salvar'}</button>
        </div>
      </form>
    </ModalShell>
  );
}

export function ModalShell({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{title}</h2>
            <button type="button" onClick={onClose} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"><X size={20} /></button>
          </div>
          <div className="p-6">{children}</div>
        </div>
      </div>
    </>
  );
}
