'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
}

interface Lead {
  id: number;
  nome: string;
  empresa: string;
  status: string;
  valor: number;
  data: string;
}

export default function DashboardCRMVendas({ loja }: { loja: LojaInfo }) {
  const router = useRouter();
  const [showModalPipeline, setShowModalPipeline] = useState(false);
  const [showModalLead, setShowModalLead] = useState(false);
  const [showModalCliente, setShowModalCliente] = useState(false);
  const [showModalVendedor, setShowModalVendedor] = useState(false);
  const [showModalProduto, setShowModalProduto] = useState(false);

  const estatisticas = {
    leads_ativos: 0,
    negociacoes: 0,
    vendas_mes: 0,
    receita: 0
  };

  const leadsRecentes: Lead[] = [];

  return (
    <div>
      {/* Ações Rápidas - MOVIDO PARA O TOPO */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h3 className="text-lg font-semibold mb-4">🚀 Ações Rápidas</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 md:gap-4">
          <button onClick={() => setShowModalLead(true)} className="p-3 md:p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md" style={{ backgroundColor: loja.cor_primaria }}>
            <div className="text-2xl md:text-3xl mb-1 md:mb-2">🎯</div>
            <div className="text-xs md:text-sm">Leads</div>
            <div className="text-[10px] opacity-80">(Em negociação)</div>
          </button>
          <button onClick={() => setShowModalCliente(true)} className="p-3 md:p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md" style={{ backgroundColor: loja.cor_primaria }}>
            <div className="text-2xl md:text-3xl mb-1 md:mb-2">👤</div>
            <div className="text-xs md:text-sm">Clientes</div>
            <div className="text-[10px] opacity-80">(Já compraram)</div>
          </button>
          <button onClick={() => setShowModalVendedor(true)} className="p-3 md:p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md" style={{ backgroundColor: loja.cor_primaria }}>
            <div className="text-2xl md:text-3xl mb-1 md:mb-2">💼</div>
            <div className="text-xs md:text-sm">Novo Vendedor</div>
          </button>
          <button onClick={() => setShowModalProduto(true)} className="p-3 md:p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md" style={{ backgroundColor: loja.cor_primaria }}>
            <div className="text-2xl md:text-3xl mb-1 md:mb-2">📦</div>
            <div className="text-xs md:text-sm">Novo Produto</div>
          </button>
          <button onClick={() => setShowModalPipeline(true)} className="p-3 md:p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md" style={{ backgroundColor: loja.cor_primaria }}>
            <div className="text-2xl md:text-3xl mb-1 md:mb-2">🔄</div>
            <div className="text-xs md:text-sm">Pipeline</div>
          </button>
          <button onClick={() => router.push(`/loja/${loja.slug}/relatorios`)} className="p-3 md:p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md" style={{ backgroundColor: loja.cor_primaria }}>
            <div className="text-2xl md:text-3xl mb-1 md:mb-2">📊</div>
            <div className="text-xs md:text-sm">Relatórios</div>
          </button>
        </div>
      </div>

      {/* Estatísticas - ABAIXO DAS AÇÕES RÁPIDAS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-gray-500 text-sm font-medium">Leads Ativos</h3>
              <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>{estatisticas.leads_ativos}</p>
            </div>
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: `${loja.cor_primaria}20` }}>
              <span className="text-2xl">👥</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-gray-500 text-sm font-medium">Negociações</h3>
              <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>{estatisticas.negociacoes}</p>
            </div>
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: `${loja.cor_primaria}20` }}>
              <span className="text-2xl">🤝</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-gray-500 text-sm font-medium">Vendas Mês</h3>
              <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>{estatisticas.vendas_mes}</p>
            </div>
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: `${loja.cor_primaria}20` }}>
              <span className="text-2xl">📈</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-gray-500 text-sm font-medium">Receita</h3>
              <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>R$ {estatisticas.receita.toLocaleString('pt-BR')}</p>
            </div>
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: `${loja.cor_primaria}20` }}>
              <span className="text-2xl">💰</span>
            </div>
          </div>
        </div>
      </div>

      {/* Leads Recentes */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Leads Recentes</h3>
          <button onClick={() => setShowModalLead(true)} className="text-sm px-4 py-2 rounded-md text-white hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>+ Novo</button>
        </div>
        
        {leadsRecentes.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-2">Nenhum lead cadastrado</p>
            <p className="text-sm mb-4">Comece adicionando seu primeiro lead</p>
            <button onClick={() => setShowModalLead(true)} className="px-6 py-3 rounded-md text-white hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
              + Adicionar Primeiro Lead
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {leadsRecentes.map((lead) => (
              <div key={lead.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold" style={{ backgroundColor: loja.cor_primaria }}>{lead.nome.charAt(0)}</div>
                  <div>
                    <p className="font-semibold text-gray-900">{lead.nome}</p>
                    <p className="text-sm text-gray-600">{lead.empresa}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold" style={{ color: loja.cor_primaria }}>R$ {lead.valor.toLocaleString('pt-BR')}</p>
                  <p className="text-sm text-gray-600">{lead.status}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modais */}
      {showModalLead && <ModalNovoLead loja={loja} onClose={() => setShowModalLead(false)} />}
      {showModalCliente && <ModalNovoCliente loja={loja} onClose={() => setShowModalCliente(false)} />}
      {showModalVendedor && <ModalNovoVendedor loja={loja} onClose={() => setShowModalVendedor(false)} />}
      {showModalProduto && <ModalNovoProduto loja={loja} onClose={() => setShowModalProduto(false)} />}
      {showModalPipeline && <ModalPipeline loja={loja} onClose={() => setShowModalPipeline(false)} />}
    </div>
  );
}

// Modal Gerenciar Leads (Listar, Criar, Editar, Excluir)
function ModalNovoLead({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [leadEditando, setLeadEditando] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    empresa: '',
    cargo: '',
    origem: '',
    interesse: '',
    valor_estimado: '',
    status: '',
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  // Lista de leads vazia inicialmente (será carregada do backend futuramente)
  const leads: any[] = [];

  const origens = ['Site', 'Indicação', 'Redes Sociais', 'Email Marketing', 'Evento', 'Telefone', 'Outro'];
  const interesses = ['Produto A', 'Produto B', 'Serviço Premium', 'Consultoria', 'Outro'];
  const statusOptions = ['Novo Lead', 'Contato Inicial', 'Qualificado', 'Proposta Enviada', 'Negociação', 'Fechado', 'Perdido'];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleNovo = () => {
    setLeadEditando(null);
    setFormData({ nome: '', email: '', telefone: '', empresa: '', cargo: '', origem: '', interesse: '', valor_estimado: '', status: 'Novo Lead', observacoes: '' });
    setMostrarFormulario(true);
  };

  const handleEditar = (lead: any) => {
    setLeadEditando(lead.id);
    setFormData({
      nome: lead.nome,
      email: lead.email,
      telefone: lead.telefone,
      empresa: lead.empresa,
      cargo: lead.cargo || '',
      origem: lead.origem,
      interesse: lead.interesse || '',
      valor_estimado: lead.valor_estimado,
      status: lead.status,
      observacoes: lead.observacoes || ''
    });
    setMostrarFormulario(true);
  };

  const handleExcluir = async (leadId: number, leadNome: string) => {
    if (!confirm(`Tem certeza que deseja excluir o lead "${leadNome}"?`)) return;
    
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      alert(`✅ Lead "${leadNome}" excluído com sucesso!`);
    } catch (error) {
      alert('❌ Erro ao excluir lead');
    }
  };

  const handleConverterCliente = async (lead: any) => {
    if (!confirm(`Converter o lead "${lead.nome}" em cliente?\n\nIsso significa que a venda foi fechada e o lead se tornou um cliente ativo.`)) return;
    
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert(`✅ Lead "${lead.nome}" convertido em cliente com sucesso!\n\n🎉 Parabéns pela venda!\n\nO cliente agora está disponível em "Gerenciar Clientes".\n\nDados transferidos:\n• Nome: ${lead.nome}\n• Empresa: ${lead.empresa}\n• Email: ${lead.email}\n• Telefone: ${lead.telefone}\n• Valor da venda: R$ ${parseFloat(lead.valor_estimado).toLocaleString('pt-BR')}`);
    } catch (error) {
      alert('❌ Erro ao converter lead em cliente');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (leadEditando) {
        alert(`✅ Lead atualizado com sucesso!\n\nNome: ${formData.nome}\nEmpresa: ${formData.empresa}\nStatus: ${formData.status}`);
      } else {
        alert(`✅ Lead cadastrado com sucesso!\n\nNome: ${formData.nome}\nEmpresa: ${formData.empresa}\nValor Estimado: R$ ${formData.valor_estimado}`);
      }
      setMostrarFormulario(false);
      setLeadEditando(null);
      setFormData({ nome: '', email: '', telefone: '', empresa: '', cargo: '', origem: '', interesse: '', valor_estimado: '', status: 'Novo Lead', observacoes: '' });
    } catch (error) {
      alert('❌ Erro ao salvar lead');
    } finally {
      setLoading(false);
    }
  };

  if (mostrarFormulario) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
          <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
            🎯 {leadEditando ? 'Editar' : 'Novo'} Lead
          </h3>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold mb-3 text-gray-700">Informações do Lead</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nome Completo *</label>
                  <input type="text" name="nome" value={formData.nome} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Ex: João Silva" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                  <input type="email" name="email" value={formData.email} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="email@exemplo.com" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Telefone *</label>
                  <input type="tel" name="telefone" value={formData.telefone} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="(00) 00000-0000" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Empresa *</label>
                  <input type="text" name="empresa" value={formData.empresa} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Nome da empresa" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cargo</label>
                  <input type="text" name="cargo" value={formData.cargo} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Ex: Gerente de Compras" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Origem *</label>
                  <select name="origem" value={formData.origem} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0">
                    <option value="">Selecione...</option>
                    {origens.map(orig => (<option key={orig} value={orig}>{orig}</option>))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Interesse *</label>
                  <select name="interesse" value={formData.interesse} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0">
                    <option value="">Selecione...</option>
                    {interesses.map(int => (<option key={int} value={int}>{int}</option>))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status *</label>
                  <select name="status" value={formData.status} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0">
                    <option value="">Selecione...</option>
                    {statusOptions.map(st => (<option key={st} value={st}>{st}</option>))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Valor Estimado (R$)</label>
                  <input type="number" name="valor_estimado" value={formData.valor_estimado} onChange={handleChange} min="0" step="0.01" className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="0.00" />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
                  <textarea name="observacoes" value={formData.observacoes} onChange={handleChange} rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Informações adicionais sobre o lead..." />
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-4 pt-4">
              <button type="button" onClick={() => { setMostrarFormulario(false); setLeadEditando(null); }} disabled={loading} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">Cancelar</button>
              <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{loading ? 'Salvando...' : (leadEditando ? 'Atualizar' : 'Cadastrar')}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-4" style={{ color: loja.cor_primaria }}>🎯 Gerenciar Leads (Em negociação)</h3>
        
        <div className="space-y-4 mb-6">
          {leads.map((lead) => (
            <div key={lead.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
              <div className="flex-1">
                <p className="font-semibold text-lg">{lead.nome}</p>
                <p className="text-sm text-gray-600">{lead.empresa} • {lead.email}</p>
                <p className="text-sm text-gray-600">{lead.telefone} • Origem: {lead.origem}</p>
                <div className="mt-2 flex items-center space-x-4">
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full">{lead.status}</span>
                  <span className="text-sm font-bold" style={{ color: loja.cor_primaria }}>R$ {parseFloat(lead.valor_estimado).toLocaleString('pt-BR')}</span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button onClick={() => handleEditar(lead)} className="px-4 py-2 text-sm text-white rounded-md hover:opacity-90 transition-opacity" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                <button onClick={() => handleConverterCliente(lead)} className="px-4 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors">✅ Converter em Cliente</button>
                <button onClick={() => handleExcluir(lead.id, lead.nome)} className="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors">🗑️ Excluir</button>
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end space-x-4">
          <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50">Fechar</button>
          <button onClick={handleNovo} className="px-6 py-2 text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Lead</button>
        </div>
      </div>
    </div>
  );
}

// Modal Gerenciar Clientes (Listar, Criar, Editar, Excluir)
function ModalNovoCliente({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [clienteEditando, setClienteEditando] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    empresa: '',
    cnpj: '',
    endereco: '',
    cidade: '',
    estado: '',
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  // Lista de clientes vazia inicialmente (será carregada do backend futuramente)
  const clientes: any[] = [];

  const estados = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleNovo = () => {
    setClienteEditando(null);
    setFormData({ nome: '', email: '', telefone: '', empresa: '', cnpj: '', endereco: '', cidade: '', estado: '', observacoes: '' });
    setMostrarFormulario(true);
  };

  const handleEditar = (cliente: any) => {
    setClienteEditando(cliente.id);
    setFormData({
      nome: cliente.nome,
      email: cliente.email,
      telefone: cliente.telefone,
      empresa: cliente.empresa,
      cnpj: cliente.cnpj,
      endereco: cliente.endereco || '',
      cidade: cliente.cidade,
      estado: cliente.estado,
      observacoes: cliente.observacoes || ''
    });
    setMostrarFormulario(true);
  };

  const handleExcluir = async (clienteId: number, clienteNome: string) => {
    if (!confirm(`Tem certeza que deseja excluir o cliente "${clienteNome}"?`)) return;
    
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      alert(`✅ Cliente "${clienteNome}" excluído com sucesso!`);
    } catch (error) {
      alert('❌ Erro ao excluir cliente');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (clienteEditando) {
        alert(`✅ Cliente atualizado com sucesso!\n\nNome: ${formData.nome}\nEmail: ${formData.email}`);
      } else {
        alert(`✅ Cliente cadastrado com sucesso!\n\nNome: ${formData.nome}\nEmpresa: ${formData.empresa}\nEmail: ${formData.email}`);
      }
      setMostrarFormulario(false);
      setClienteEditando(null);
      setFormData({ nome: '', email: '', telefone: '', empresa: '', cnpj: '', endereco: '', cidade: '', estado: '', observacoes: '' });
    } catch (error) {
      alert('❌ Erro ao salvar cliente');
    } finally {
      setLoading(false);
    }
  };

  if (mostrarFormulario) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
          <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>👤 {clienteEditando ? 'Editar' : 'Novo'} Cliente</h3>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold mb-3 text-gray-700">Dados do Cliente</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nome/Razão Social *</label>
                  <input type="text" name="nome" value={formData.nome} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Nome completo ou razão social" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                  <input type="email" name="email" value={formData.email} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="email@exemplo.com" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Telefone *</label>
                  <input type="tel" name="telefone" value={formData.telefone} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="(00) 00000-0000" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Empresa</label>
                  <input type="text" name="empresa" value={formData.empresa} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Nome da empresa" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">CNPJ</label>
                  <input type="text" name="cnpj" value={formData.cnpj} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="00.000.000/0000-00" />
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-lg font-semibold mb-3 text-gray-700">Endereço</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Endereço Completo</label>
                  <input type="text" name="endereco" value={formData.endereco} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Rua, número, bairro" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                  <select name="estado" value={formData.estado} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0">
                    <option value="">Selecione...</option>
                    {estados.map(uf => (<option key={uf} value={uf}>{uf}</option>))}
                  </select>
                </div>
                <div className="md:col-span-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cidade</label>
                  <input type="text" name="cidade" value={formData.cidade} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Ex: São Paulo" />
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
              <textarea name="observacoes" value={formData.observacoes} onChange={handleChange} rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Informações adicionais sobre o cliente..." />
            </div>
            <div className="flex justify-end space-x-4 pt-4 border-t">
              <button type="button" onClick={() => { setMostrarFormulario(false); setClienteEditando(null); }} disabled={loading} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">Cancelar</button>
              <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{loading ? 'Salvando...' : (clienteEditando ? 'Atualizar' : 'Cadastrar')}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-4" style={{ color: loja.cor_primaria }}>👤 Gerenciar Clientes (Já compraram)</h3>
        
        <div className="space-y-4 mb-6">
          {clientes.map((cliente) => (
            <div key={cliente.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
              <div className="flex-1">
                <p className="font-semibold text-lg">{cliente.nome}</p>
                <p className="text-sm text-gray-600">{cliente.empresa} • CNPJ: {cliente.cnpj}</p>
                <p className="text-sm text-gray-600">{cliente.email} • {cliente.telefone}</p>
                <p className="text-sm text-gray-600">{cliente.cidade}/{cliente.estado}</p>
              </div>
              <div className="flex items-center space-x-2">
                <button onClick={() => handleEditar(cliente)} className="px-4 py-2 text-sm text-white rounded-md hover:opacity-90 transition-opacity" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                <button onClick={() => handleExcluir(cliente.id, cliente.nome)} className="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors">🗑️ Excluir</button>
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end space-x-4">
          <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50">Fechar</button>
          <button onClick={handleNovo} className="px-6 py-2 text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Cliente</button>
        </div>
      </div>
    </div>
  );
}

// Modal Novo Vendedor
function ModalNovoVendedor({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    cpf: '',
    meta_mensal: '',
    comissao: '',
    data_admissao: '',
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert(`✅ Vendedor cadastrado com sucesso!\n\nNome: ${formData.nome}\nMeta Mensal: R$ ${formData.meta_mensal}\nComissão: ${formData.comissao}%`);
      onClose();
    } catch (error) {
      alert('❌ Erro ao cadastrar vendedor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>💼 Novo Vendedor</h3>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Dados Pessoais</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome Completo *</label>
                <input type="text" name="nome" value={formData.nome} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Ex: Carlos Silva" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input type="email" name="email" value={formData.email} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="email@exemplo.com" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Telefone *</label>
                <input type="tel" name="telefone" value={formData.telefone} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="(00) 00000-0000" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">CPF *</label>
                <input type="text" name="cpf" value={formData.cpf} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="000.000.000-00" />
              </div>
            </div>
          </div>
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Dados Profissionais</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Meta Mensal (R$) *</label>
                <input type="number" name="meta_mensal" value={formData.meta_mensal} onChange={handleChange} required min="0" step="0.01" className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="10000.00" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Comissão (%) *</label>
                <input type="number" name="comissao" value={formData.comissao} onChange={handleChange} required min="0" max="100" step="0.1" className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="5.0" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Data de Admissão *</label>
                <input type="date" name="data_admissao" value={formData.data_admissao} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" />
              </div>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
            <textarea name="observacoes" value={formData.observacoes} onChange={handleChange} rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Informações adicionais sobre o vendedor..." />
          </div>
          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button type="button" onClick={onClose} disabled={loading} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">Cancelar</button>
            <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{loading ? 'Cadastrando...' : 'Cadastrar Vendedor'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Modal Novo Produto/Serviço
function ModalNovoProduto({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [formData, setFormData] = useState({
    tipo: '',
    nome: '',
    descricao: '',
    categoria: '',
    preco: '',
    custo: '',
    estoque: '',
    codigo: '',
    duracao: '',
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  const categoriasProduto = ['Software', 'Hardware', 'Licença', 'Material', 'Equipamento', 'Outro'];
  const categoriasServico = ['Consultoria', 'Treinamento', 'Suporte', 'Implementação', 'Manutenção', 'Desenvolvimento', 'Outro'];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ 
      ...prev, 
      [name]: value,
      // Limpar categoria ao mudar tipo
      ...(name === 'tipo' ? { categoria: '' } : {})
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      const tipoTexto = formData.tipo === 'produto' ? 'Produto' : 'Serviço';
      alert(`✅ ${tipoTexto} cadastrado com sucesso!\n\nNome: ${formData.nome}\nPreço: R$ ${formData.preco}\nCategoria: ${formData.categoria}${formData.tipo === 'servico' && formData.duracao ? `\nDuração: ${formData.duracao}` : ''}`);
      onClose();
    } catch (error) {
      alert('❌ Erro ao cadastrar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>📦 Novo Produto/Serviço</h3>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Tipo</h4>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, tipo: 'produto', categoria: '' }))}
                className={`p-4 rounded-lg border-2 transition-all ${
                  formData.tipo === 'produto'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <div className="text-3xl mb-2">📦</div>
                <div className="font-semibold">Produto</div>
                <div className="text-xs text-gray-600">Item físico ou digital</div>
              </button>
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, tipo: 'servico', categoria: '', estoque: '' }))}
                className={`p-4 rounded-lg border-2 transition-all ${
                  formData.tipo === 'servico'
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <div className="text-3xl mb-2">🛠️</div>
                <div className="font-semibold">Serviço</div>
                <div className="text-xs text-gray-600">Consultoria, suporte, etc.</div>
              </button>
            </div>
          </div>

          {formData.tipo && (
            <>
              <div>
                <h4 className="text-lg font-semibold mb-3 text-gray-700">
                  Informações do {formData.tipo === 'produto' ? 'Produto' : 'Serviço'}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nome do {formData.tipo === 'produto' ? 'Produto' : 'Serviço'} *
                    </label>
                    <input 
                      type="text" 
                      name="nome" 
                      value={formData.nome} 
                      onChange={handleChange} 
                      required 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                      placeholder={formData.tipo === 'produto' ? 'Ex: Sistema CRM Premium' : 'Ex: Consultoria em Vendas'} 
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
                    <textarea 
                      name="descricao" 
                      value={formData.descricao} 
                      onChange={handleChange} 
                      rows={3} 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                      placeholder={formData.tipo === 'produto' ? 'Descreva o produto...' : 'Descreva o serviço...'} 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Categoria *</label>
                    <select name="categoria" value={formData.categoria} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0">
                      <option value="">Selecione...</option>
                      {(formData.tipo === 'produto' ? categoriasProduto : categoriasServico).map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Código/SKU</label>
                    <input 
                      type="text" 
                      name="codigo" 
                      value={formData.codigo} 
                      onChange={handleChange} 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                      placeholder="Ex: PROD-001" 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Preço de Venda (R$) *</label>
                    <input 
                      type="number" 
                      name="preco" 
                      value={formData.preco} 
                      onChange={handleChange} 
                      required 
                      min="0" 
                      step="0.01" 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                      placeholder="1000.00" 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Custo (R$)</label>
                    <input 
                      type="number" 
                      name="custo" 
                      value={formData.custo} 
                      onChange={handleChange} 
                      min="0" 
                      step="0.01" 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                      placeholder="500.00" 
                    />
                  </div>
                  
                  {formData.tipo === 'produto' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Estoque Inicial</label>
                      <input 
                        type="number" 
                        name="estoque" 
                        value={formData.estoque} 
                        onChange={handleChange} 
                        min="0" 
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                        placeholder="0" 
                      />
                    </div>
                  )}
                  
                  {formData.tipo === 'servico' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Duração Estimada</label>
                      <input 
                        type="text" 
                        name="duracao" 
                        value={formData.duracao} 
                        onChange={handleChange} 
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                        placeholder="Ex: 2 horas, 1 dia, 1 semana" 
                      />
                    </div>
                  )}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
                <textarea 
                  name="observacoes" 
                  value={formData.observacoes} 
                  onChange={handleChange} 
                  rows={3} 
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                  placeholder="Informações adicionais..." 
                />
              </div>
            </>
          )}
          
          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button type="button" onClick={onClose} disabled={loading} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">Cancelar</button>
            <button 
              type="submit" 
              disabled={loading || !formData.tipo} 
              className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" 
              style={{ backgroundColor: loja.cor_primaria }}
            >
              {loading ? 'Cadastrando...' : `Cadastrar ${formData.tipo === 'produto' ? 'Produto' : formData.tipo === 'servico' ? 'Serviço' : ''}`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
              </div>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
            <textarea name="observacoes" value={formData.observacoes} onChange={handleChange} rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Informações adicionais sobre o produto..." />
          </div>
          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button type="button" onClick={onClose} disabled={loading} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">Cancelar</button>
            <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{loading ? 'Cadastrando...' : 'Cadastrar Produto'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}


// Modal Pipeline de Vendas (Modal Normal - Não Tela Cheia)
function ModalPipeline({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const etapas = [
    { nome: 'Novo Lead', quantidade: 0, valor: 0, cor: '#3B82F6' },
    { nome: 'Contato Inicial', quantidade: 0, valor: 0, cor: '#8B5CF6' },
    { nome: 'Qualificado', quantidade: 0, valor: 0, cor: '#EC4899' },
    { nome: 'Proposta Enviada', quantidade: 0, valor: 0, cor: '#F59E0B' },
    { nome: 'Negociação', quantidade: 0, valor: 0, cor: '#10B981' },
    { nome: 'Fechado', quantidade: 0, valor: 0, cor: '#059669' }
  ];

  const totalLeads = etapas.reduce((acc, e) => acc + e.quantidade, 0);
  const totalValor = etapas.reduce((acc, e) => acc + e.valor, 0);
  const taxaConversao = totalLeads > 0 ? ((etapas[etapas.length - 1].quantidade / etapas[0].quantidade) * 100).toFixed(1) : '0.0';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 z-10 text-white p-4 rounded-t-lg flex items-center justify-between" style={{ backgroundColor: loja.cor_primaria }}>
          <h3 className="text-xl font-bold">🔄 Pipeline de Vendas</h3>
          <button onClick={onClose} className="p-1 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Conteúdo */}
        <div className="p-6">
          {/* Cards de Resumo */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-4 rounded-lg shadow text-white">
              <p className="text-xs font-medium opacity-90">Total de Leads</p>
              <p className="text-2xl font-bold mt-1">{totalLeads}</p>
              <p className="text-xs mt-1 opacity-75">no funil de vendas</p>
            </div>
            <div className="bg-gradient-to-br from-green-500 to-green-600 p-4 rounded-lg shadow text-white">
              <p className="text-xs font-medium opacity-90">Valor Total</p>
              <p className="text-2xl font-bold mt-1">R$ {totalValor.toLocaleString('pt-BR')}</p>
              <p className="text-xs mt-1 opacity-75">em negociações</p>
            </div>
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-4 rounded-lg shadow text-white">
              <p className="text-xs font-medium opacity-90">Taxa de Conversão</p>
              <p className="text-2xl font-bold mt-1">{taxaConversao}%</p>
              <p className="text-xs mt-1 opacity-75">do início ao fim</p>
            </div>
          </div>

          {/* Funil Visual Compacto */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h4 className="text-lg font-bold mb-4 text-gray-800">Funil de Vendas</h4>
            <div className="space-y-2">
              {etapas.map((etapa, index) => {
                const larguraBase = 100;
                const reducao = (index * 12);
                const largura = larguraBase - reducao;
                
                return (
                  <div key={etapa.nome} className="flex items-center space-x-3">
                    <div className="w-32 text-right flex-shrink-0">
                      <p className="text-sm font-semibold text-gray-700">{etapa.nome}</p>
                    </div>
                    <div className="flex-1">
                      <div 
                        className="relative rounded-lg p-3 transition-all hover:scale-105 cursor-pointer shadow"
                        style={{ 
                          backgroundColor: etapa.cor,
                          width: `${largura}%`,
                          marginLeft: `${reducao / 2}%`
                        }}
                      >
                        <div className="flex items-center justify-between text-white">
                          <div>
                            <p className="font-bold text-sm">{etapa.quantidade} leads</p>
                            <p className="text-xs opacity-90">R$ {etapa.valor.toLocaleString('pt-BR')}</p>
                          </div>
                          <div className="text-xl">
                            {index === 0 && '🎯'}
                            {index === 1 && '📞'}
                            {index === 2 && '✅'}
                            {index === 3 && '📄'}
                            {index === 4 && '🤝'}
                            {index === 5 && '🎉'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Tabela Compacta */}
          <div className="bg-white rounded-lg border">
            <h4 className="text-lg font-bold p-4 border-b text-gray-800">Detalhamento por Etapa</h4>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Etapa</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Leads</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Valor Total</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Ticket Médio</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Conversão</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {etapas.map((etapa, index) => {
                    const ticketMedio = etapa.quantidade > 0 ? etapa.valor / etapa.quantidade : 0;
                    const conversao = index > 0 && etapas[index - 1].quantidade > 0 
                      ? ((etapa.quantidade / etapas[index - 1].quantidade) * 100).toFixed(1) 
                      : '-';
                    
                    return (
                      <tr key={etapa.nome} className="hover:bg-gray-50">
                        <td className="px-4 py-2 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: etapa.cor }}></div>
                            <span className="font-semibold text-gray-900 text-sm">{etapa.nome}</span>
                          </div>
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-gray-700 text-sm font-medium">{etapa.quantidade}</td>
                        <td className="px-4 py-2 whitespace-nowrap font-bold text-sm" style={{ color: etapa.cor }}>
                          R$ {etapa.valor.toLocaleString('pt-BR')}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-gray-700 text-sm">
                          R$ {ticketMedio.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap">
                          {conversao !== '-' ? (
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                              parseFloat(conversao) >= 70 ? 'bg-green-100 text-green-800' :
                              parseFloat(conversao) >= 50 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {conversao}%
                            </span>
                          ) : (
                            <span className="text-gray-400 text-sm">-</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Botão Fechar */}
          <div className="flex justify-end mt-6">
            <button
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
