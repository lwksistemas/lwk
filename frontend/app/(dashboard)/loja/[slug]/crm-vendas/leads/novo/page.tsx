'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { STATUS_LEAD_OPCOES } from '@/constants/crm';
import { ArrowLeft } from 'lucide-react';
import { consultaCep } from '@/lib/consulta-cep';
import { consultaCnpj, formatCpfCnpj } from '@/lib/consulta-cnpj';

const inputClass = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white';
const labelClass = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';

export default function NovoLeadPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const { origensAtivas } = useCRMConfig();
  const [form, setForm] = useState({
    nome: '',
    empresa: '',
    cpf_cnpj: '',
    email: '',
    telefone: '',
    origem: 'site',
    status: 'novo',
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    uf: '',
  });
  const [enviando, setEnviando] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [buscarCepLoading, setBuscarCepLoading] = useState(false);
  const [buscarCnpjLoading, setBuscarCnpjLoading] = useState(false);

  const handleCpfCnpjChange = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 14);
    setForm((f) => ({ ...f, cpf_cnpj: formatCpfCnpj(digits) }));
  };

  const handleBuscarCnpj = async () => {
    const cnpj = form.cpf_cnpj.replace(/\D/g, '');
    if (cnpj.length !== 14) {
      alert('Informe um CNPJ válido com 14 dígitos para buscar.');
      return;
    }
    setBuscarCnpjLoading(true);
    try {
      const data = await consultaCnpj(form.cpf_cnpj);
      if (data) {
        setForm((f) => ({
          ...f,
          nome: data.razao_social || f.nome,
          empresa: data.nome_fantasia || f.empresa,
          cep: data.cep || f.cep,
          logradouro: data.logradouro || f.logradouro,
          numero: data.numero || f.numero,
          complemento: data.complemento || f.complemento,
          bairro: data.bairro || f.bairro,
          cidade: data.municipio || f.cidade,
          uf: data.uf || f.uf,
        }));
      } else {
        alert('CNPJ não encontrado ou serviço indisponível.');
      }
    } catch {
      alert('Erro ao consultar CNPJ. Tente novamente.');
    } finally {
      setBuscarCnpjLoading(false);
    }
  };

  const handleCepChange = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 8);
    const formatted = digits.length > 5 ? `${digits.slice(0, 5)}-${digits.slice(5)}` : digits;
    setForm((f) => ({ ...f, cep: formatted }));
  };

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
        setForm((f) => ({
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormErro(null);
    if (!form.nome.trim()) {
      setFormErro('Informe o nome.');
      return;
    }
    setEnviando(true);
    apiClient
      .post('/crm-vendas/leads/', {
        nome: form.nome.trim(),
        empresa: form.empresa.trim() || undefined,
        cpf_cnpj: form.cpf_cnpj.trim() || undefined,
        email: form.email.trim() || undefined,
        telefone: form.telefone.trim() || undefined,
        origem: form.origem,
        status: form.status,
        cep: form.cep.trim() || undefined,
        logradouro: form.logradouro.trim() || undefined,
        numero: form.numero.trim() || undefined,
        complemento: form.complemento.trim() || undefined,
        bairro: form.bairro.trim() || undefined,
        cidade: form.cidade.trim() || undefined,
        uf: form.uf.trim().toUpperCase() || undefined,
      })
      .then(() => {
        router.push(`/loja/${slug}/crm-vendas/leads`);
      })
      .catch((err) => {
        setFormErro(
          err.response?.data?.nome?.[0] || err.response?.data?.detail || 'Erro ao salvar lead.'
        );
      })
      .finally(() => setEnviando(false));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          href={`/loja/${slug}/crm-vendas/leads`}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
          aria-label="Voltar"
        >
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 className="text-2xl font-semibold text-gray-800 dark:text-white">Novo Lead</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            Preencha os dados do cliente
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="max-w-2xl space-y-8">
        {formErro && (
          <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
            {formErro}
          </div>
        )}

        {/* Dados do lead */}
        <div className="bg-white dark:bg-[#16325c] rounded-xl border border-gray-200 dark:border-[#0d1f3c] p-6 space-y-4">
          <h2 className="text-lg font-medium text-gray-800 dark:text-white border-b border-gray-200 dark:border-gray-600 pb-2">
            Dados do lead
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className={labelClass}>Nome *</label>
              <input
                type="text"
                value={form.nome}
                onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
                className={inputClass}
                placeholder="Nome completo do lead"
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className={labelClass}>CPF ou CNPJ</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={form.cpf_cnpj}
                  onChange={(e) => handleCpfCnpjChange(e.target.value)}
                  className={inputClass}
                  placeholder="000.000.000-00 ou 00.000.000/0001-00"
                />
                <button
                  type="button"
                  onClick={handleBuscarCnpj}
                  disabled={buscarCnpjLoading || form.cpf_cnpj.replace(/\D/g, '').length !== 14}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap text-sm font-medium"
                  title="Buscar dados do CNPJ na Receita Federal"
                >
                  {buscarCnpjLoading ? '...' : 'Buscar CNPJ'}
                </button>
              </div>
            </div>
            <div>
              <label className={labelClass}>Empresa</label>
              <input
                type="text"
                value={form.empresa}
                onChange={(e) => setForm((f) => ({ ...f, empresa: e.target.value }))}
                className={inputClass}
                placeholder="Nome da empresa"
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
                onChange={(e) => setForm((f) => ({ ...f, telefone: e.target.value }))}
                className={inputClass}
                placeholder="(00) 00000-0000"
              />
            </div>
            <div>
              <label className={labelClass}>Origem</label>
              <select
                value={form.origem}
                onChange={(e) => setForm((f) => ({ ...f, origem: e.target.value }))}
                className={inputClass}
              >
                {origensAtivas().map((o) => (
                  <option key={o.key} value={o.key}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass}>Status</label>
              <select
                value={form.status}
                onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
                className={inputClass}
              >
                {STATUS_LEAD_OPCOES.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Endereço */}
        <div className="bg-white dark:bg-[#16325c] rounded-xl border border-gray-200 dark:border-[#0d1f3c] p-6 space-y-4">
          <h2 className="text-lg font-medium text-gray-800 dark:text-white border-b border-gray-200 dark:border-gray-600 pb-2">
            Endereço
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex gap-2">
              <div className="flex-1">
                <label className={labelClass}>CEP</label>
                <input
                  type="text"
                  value={form.cep}
                  onChange={(e) => handleCepChange(e.target.value)}
                  onBlur={() => form.cep.replace(/\D/g, '').length === 8 && handleBuscarCep()}
                  maxLength={9}
                  className={inputClass}
                  placeholder="00000-000"
                />
              </div>
              <div className="flex items-end">
                <button
                  type="button"
                  onClick={handleBuscarCep}
                  disabled={buscarCepLoading || form.cep.replace(/\D/g, '').length !== 8}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap text-sm font-medium"
                  title="Buscar endereço pelo CEP"
                >
                  {buscarCepLoading ? '...' : 'Buscar'}
                </button>
              </div>
            </div>
            <div className="md:col-span-2">
              <label className={labelClass}>Logradouro</label>
              <input
                type="text"
                value={form.logradouro}
                onChange={(e) => setForm((f) => ({ ...f, logradouro: e.target.value }))}
                className={inputClass}
                placeholder="Rua, avenida..."
              />
            </div>
            <div>
              <label className={labelClass}>Número</label>
              <input
                type="text"
                value={form.numero}
                onChange={(e) => setForm((f) => ({ ...f, numero: e.target.value }))}
                className={inputClass}
                placeholder="Nº"
              />
            </div>
            <div>
              <label className={labelClass}>Complemento</label>
              <input
                type="text"
                value={form.complemento}
                onChange={(e) => setForm((f) => ({ ...f, complemento: e.target.value }))}
                className={inputClass}
                placeholder="Apto, sala..."
              />
            </div>
            <div>
              <label className={labelClass}>Bairro</label>
              <input
                type="text"
                value={form.bairro}
                onChange={(e) => setForm((f) => ({ ...f, bairro: e.target.value }))}
                className={inputClass}
                placeholder="Bairro"
              />
            </div>
            <div>
              <label className={labelClass}>Cidade</label>
              <input
                type="text"
                value={form.cidade}
                onChange={(e) => setForm((f) => ({ ...f, cidade: e.target.value }))}
                className={inputClass}
                placeholder="Cidade"
              />
            </div>
            <div className="max-w-[100px]">
              <label className={labelClass}>UF</label>
              <input
                type="text"
                value={form.uf}
                onChange={(e) => setForm((f) => ({ ...f, uf: e.target.value.toUpperCase().slice(0, 2) }))}
                maxLength={2}
                className={inputClass}
                placeholder="UF"
              />
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          <Link
            href={`/loja/${slug}/crm-vendas/leads`}
            className="px-6 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 font-medium"
          >
            Cancelar
          </Link>
          <button
            type="submit"
            disabled={enviando}
            className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium"
          >
            {enviando ? 'Salvando...' : 'Salvar lead'}
          </button>
        </div>
      </form>
    </div>
  );
}
