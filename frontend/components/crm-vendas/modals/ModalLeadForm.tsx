'use client';

import { useState } from 'react';
import { X } from 'lucide-react';
import { consultaCep } from '@/lib/consulta-cep';

export interface FormDataLead {
  nome: string;
  empresa: string;
  email: string;
  telefone: string;
  origem: string;
  status: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  uf: string;
}

interface ModalLeadFormProps {
  title: string;
  form: FormDataLead;
  formErro: string | null;
  enviando: boolean;
  origensAtivas: () => Array<{ key: string; label: string }>;
  statusOpcoes: Array<{ value: string; label: string }>;
  onFormChange: (updater: (f: FormDataLead) => FormDataLead) => void;
  onSubmit: (e: React.FormEvent) => void;
  onClose: () => void;
  /** Tela cheia no desktop (computador) */
  fullScreenOnDesktop?: boolean;
}

export default function ModalLeadForm({
  title,
  form,
  formErro,
  enviando,
  origensAtivas,
  statusOpcoes,
  onFormChange,
  onSubmit,
  onClose,
  fullScreenOnDesktop = false,
}: ModalLeadFormProps) {
  const [buscarCepLoading, setBuscarCepLoading] = useState(false);

  const handleBuscarCep = async () => {
    const cep = form.cep.replace(/\D/g, '');
    if (cep.length !== 8) {
      alert('Informe um CEP válido com 8 dígitos.');
      return;
    }
    setBuscarCepLoading(true);
    try {
      const endereco = await consultaCep(form.cep);
      if (endereco) {
        onFormChange((f) => ({
          ...f,
          logradouro: endereco.logradouro,
          bairro: endereco.bairro,
          cidade: endereco.cidade,
          uf: endereco.uf,
        }));
      } else {
        alert('Erro ao consultar CEP. Verifique sua conexão ou tente novamente em instantes.');
      }
    } finally {
      setBuscarCepLoading(false);
    }
  };

  const handleCepChange = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 8);
    const formatted = digits.length > 5 ? `${digits.slice(0, 5)}-${digits.slice(5)}` : digits;
    onFormChange((f) => ({ ...f, cep: formatted }));
  };

  return (
    <div
      className={`fixed inset-0 z-50 bg-black/50 ${fullScreenOnDesktop ? 'md:p-0 md:relative flex md:block' : 'flex items-center justify-center p-4'}`}
      onClick={() => !enviando && onClose()}
    >
      <div
        className={`bg-white dark:bg-gray-800 shadow-xl border border-gray-200 dark:border-gray-700 w-full overflow-y-auto
          ${fullScreenOnDesktop
            ? 'max-w-md max-h-[90vh] rounded-2xl md:absolute md:inset-4 md:max-w-none md:max-h-none md:rounded-xl'
            : 'max-w-md max-h-[90vh] rounded-2xl'
          }`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 z-10">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h2>
          <button
            type="button"
            onClick={() => !enviando && onClose()}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>
        <form onSubmit={onSubmit} className={`p-4 space-y-4 ${fullScreenOnDesktop ? 'md:max-w-3xl md:mx-auto md:grid md:grid-cols-2 md:gap-x-6' : ''}`}>
          {formErro && (
            <p className={`text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg ${fullScreenOnDesktop ? 'md:col-span-2' : ''}`}>
              {formErro}
            </p>
          )}
          <div className={`space-y-3 border-b border-gray-200 dark:border-gray-600 pb-4 ${fullScreenOnDesktop ? 'md:col-span-2' : ''}`}>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Endereço</p>
            <div className="flex gap-2">
              <div className="flex-1">
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-0.5">CEP</label>
                <input
                  type="text"
                  value={form.cep}
                  onChange={(e) => handleCepChange(e.target.value)}
                  onBlur={() => form.cep.replace(/\D/g, '').length === 8 && handleBuscarCep()}
                  maxLength={9}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  placeholder="00000-000"
                />
              </div>
              <div className="flex items-end">
                <button
                  type="button"
                  onClick={handleBuscarCep}
                  disabled={buscarCepLoading || form.cep.replace(/\D/g, '').length !== 8}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap text-sm"
                  title="Buscar endereço pelo CEP"
                >
                  {buscarCepLoading ? '...' : 'Buscar'}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-0.5">Logradouro</label>
              <input
                type="text"
                value={form.logradouro}
                onChange={(e) => onFormChange((f) => ({ ...f, logradouro: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                placeholder="Rua, avenida..."
              />
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-0.5">Nº</label>
                <input
                  type="text"
                  value={form.numero}
                  onChange={(e) => onFormChange((f) => ({ ...f, numero: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  placeholder="Nº"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-0.5">Complemento</label>
                <input
                  type="text"
                  value={form.complemento}
                  onChange={(e) => onFormChange((f) => ({ ...f, complemento: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  placeholder="Apto, sala..."
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-0.5">Bairro</label>
                <input
                  type="text"
                  value={form.bairro}
                  onChange={(e) => onFormChange((f) => ({ ...f, bairro: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  placeholder="Bairro"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-0.5">Cidade</label>
                <input
                  type="text"
                  value={form.cidade}
                  onChange={(e) => onFormChange((f) => ({ ...f, cidade: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  placeholder="Cidade"
                />
              </div>
            </div>
            <div className="max-w-[80px]">
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-0.5">UF</label>
              <input
                type="text"
                value={form.uf}
                onChange={(e) => onFormChange((f) => ({ ...f, uf: e.target.value.toUpperCase().slice(0, 2) }))}
                maxLength={2}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                placeholder="UF"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
            <input
              type="text"
              value={form.nome}
              onChange={(e) => onFormChange((f) => ({ ...f, nome: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Nome do lead"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Empresa</label>
            <input
              type="text"
              value={form.empresa}
              onChange={(e) => onFormChange((f) => ({ ...f, empresa: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Empresa"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => onFormChange((f) => ({ ...f, email: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="email@exemplo.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label>
            <input
              type="text"
              value={form.telefone}
              onChange={(e) => onFormChange((f) => ({ ...f, telefone: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="(00) 00000-0000"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Origem</label>
            <select
              value={form.origem}
              onChange={(e) => onFormChange((f) => ({ ...f, origem: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {origensAtivas().map((o) => (
                <option key={o.key} value={o.key}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
            <select
              value={form.status}
              onChange={(e) => onFormChange((f) => ({ ...f, status: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {statusOpcoes.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className={`flex gap-2 pt-2 ${fullScreenOnDesktop ? 'md:col-span-2' : ''}`}>
            <button
              type="button"
              onClick={() => !enviando && onClose()}
              className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={enviando}
              className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium"
            >
              {enviando ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
