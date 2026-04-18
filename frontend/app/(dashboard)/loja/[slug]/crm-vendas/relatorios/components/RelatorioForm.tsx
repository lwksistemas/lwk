'use client';

import { Download, Mail, Calendar, DollarSign, Users, TrendingUp, Building2 } from 'lucide-react';

interface Vendedor { id: number; nome: string; }
interface EmpresaPrestadora { id: number; nome: string; cnpj?: string; }

interface Props {
  tipoRelatorio: string;
  periodo: string;
  vendedorSelecionado: string;
  vendedores: Vendedor[];
  empresasPrestadoras: EmpresaPrestadora[];
  empresaPrestadoraSelecionada: string;
  isVendedor: boolean;
  gerando: boolean;
  loading: boolean;
  onTipoChange: (tipo: string) => void;
  onPeriodoChange: (periodo: string) => void;
  onVendedorChange: (id: string) => void;
  onEmpresaPrestadoraChange: (id: string) => void;
  onGerar: (acao: 'pdf' | 'email') => void;
}

const TIPOS = [
  { key: 'vendas_total', label: 'Total de Vendas', desc: 'Todos os vendedores', icon: DollarSign, adminOnly: true },
  { key: 'vendas_vendedor', label: 'Vendas por Vendedor', desc: 'Com comissões', icon: Users, adminOnly: false },
  { key: 'comissoes', label: 'Apenas Comissões', desc: 'Detalhamento completo', icon: TrendingUp, adminOnly: false },
];

const PERIODOS = [
  { value: 'hoje', label: 'Hoje' },
  { value: 'ontem', label: 'Ontem' },
  { value: 'semana_atual', label: 'Esta Semana' },
  { value: 'semana_passada', label: 'Semana Passada' },
  { value: 'mes_atual', label: 'Este Mês' },
  { value: 'mes_passado', label: 'Mês Passado' },
  { value: 'trimestre_atual', label: 'Este Trimestre' },
  { value: 'ano_atual', label: 'Este Ano' },
  { value: 'personalizado', label: 'Período Personalizado' },
];

export function RelatorioForm({ tipoRelatorio, periodo, vendedorSelecionado, vendedores, empresasPrestadoras, empresaPrestadoraSelecionada, isVendedor, gerando, loading, onTipoChange, onPeriodoChange, onVendedorChange, onEmpresaPrestadoraChange, onGerar }: Props) {
  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Gerar Relatório</h2>
      <div className="space-y-4">
        {/* Tipo */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Tipo de Relatório</label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {TIPOS.filter((t) => !t.adminOnly || !isVendedor).map((t) => {
              const Icon = t.icon;
              return (
                <button key={t.key} type="button" onClick={() => onTipoChange(t.key)}
                  className={`p-4 rounded-lg border-2 transition-all text-left ${tipoRelatorio === t.key ? 'border-[#0176d3] bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <Icon size={18} className="text-[#0176d3]" />
                    <span className="font-medium text-gray-900 dark:text-white text-sm">{t.label}</span>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{t.desc}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Período */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            <Calendar size={16} className="inline mr-1" /> Período
          </label>
          <select value={periodo} onChange={(e) => onPeriodoChange(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
            {PERIODOS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
        </div>

        {/* Vendedor */}
        {tipoRelatorio === 'vendas_vendedor' && !isVendedor && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Vendedor</label>
            <select value={vendedorSelecionado} onChange={(e) => onVendedorChange(e.target.value)} disabled={loading} className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="todos">Todos os Vendedores</option>
              {vendedores.map((v) => <option key={v.id} value={v.id}>{v.nome}</option>)}
            </select>
          </div>
        )}
        {tipoRelatorio === 'vendas_vendedor' && isVendedor && (
          <p className="text-sm text-gray-600 dark:text-gray-400">Relatório das suas vendas</p>
        )}

        {/* Empresa Prestadora */}
        {empresasPrestadoras.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              <Building2 size={16} className="inline mr-1" /> Empresa Prestadora
            </label>
            <select value={empresaPrestadoraSelecionada} onChange={(e) => onEmpresaPrestadoraChange(e.target.value)} disabled={loading} className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="todas">Todas as Empresas</option>
              {empresasPrestadoras.map((ep) => <option key={ep.id} value={ep.id}>{ep.nome}{ep.cnpj ? ` (${ep.cnpj})` : ''}</option>)}
            </select>
          </div>
        )}

        {/* Ações */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button type="button" onClick={() => onGerar('pdf')} disabled={gerando} className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg font-medium disabled:opacity-50">
            <Download size={18} /> {gerando ? 'Gerando...' : 'Exportar PDF'}
          </button>
          <button type="button" onClick={() => onGerar('email')} disabled={gerando} className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium disabled:opacity-50">
            <Mail size={18} /> {gerando ? 'Enviando...' : 'Enviar por Email'}
          </button>
        </div>
      </div>
    </div>
  );
}
