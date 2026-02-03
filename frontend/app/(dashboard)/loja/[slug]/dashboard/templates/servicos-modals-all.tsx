// TODOS OS MODAIS COMPLETOS - Dashboard Serviços
// Arquivo consolidado com CRUD completo para todas as funcionalidades

import { useState, useEffect } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

// Constantes
const STATUS_AGENDAMENTO = [
  { value: 'agendado', label: 'Agendado' },
  { value: 'confirmado', label: 'Confirmado' },
  { value: 'em_andamento', label: 'Em Andamento' },
  { value: 'concluido', label: 'Concluído' },
  { value: 'cancelado', label: 'Cancelado' }
];

const STATUS_OS = [
  { value: 'aberta', label: 'Aberta' },
  { value: 'em_andamento', label: 'Em Andamento' },
  { value: 'aguardando_peca', label: 'Aguardando Peça' },
  { value: 'concluida', label: 'Concluída' },
  { value: 'cancelada', label: 'Cancelada' }
];

const STATUS_ORCAMENTO = [
  { value: 'pendente', label: 'Pendente' },
  { value: 'aprovado', label: 'Aprovado' },
  { value: 'recusado', label: 'Recusado' },
  { value: 'expirado', label: 'Expirado' }
];

// Componente base para modais com CRUD
function ModalBase({ 
  loja, 
  onClose, 
  onSuccess,
  title,
  icon,
  endpoint,
  formFields,
  renderListItem,
  emptyMessage = "Nenhum registro cadastrado"
}: any) {
  const toast = useToast();
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [editando, setEditando] = useState<number | null>(null);
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingLista, setLoadingLista] = useState(true);
  const [formData, setFormData] = useState<any>({});

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    try {
      setLoadingLista(true);
      const res = await clinicaApiClient.get(endpoint);
      setItems(Array.isArray(res.data) ? res.data : res.data?.results ?? []);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoadingLista(false);
    }
  };

  const handleNovo = () => {
    setEditando(null);
    setFormData(formFields.reduce((acc: any, field: any) => ({ ...acc, [field.name]: field.defaultValue || '' }), {}));
    setMostrarFormulario(true);
  };

  const handleEditar = (item: any) => {
    setEditando(item.id);
    setFormData(formFields.reduce((acc: any, field: any) => ({ ...acc, [field.name]: field.getValue ? field.getValue(item) : item[field.name] || '' }), {}));
    setMostrarFormulario(true);
  };

  const handleExcluir = async (id: number, nome: string) => {
    if (!confirm(`Excluir "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`${endpoint}${id}/`);
      toast.success('Excluído com sucesso');
      loadItems();
      onSuccess?.();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao excluir');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = formFields.reduce((acc: any, field: any) => {
        const value = formData[field.name];
        return { ...acc, [field.apiName || field.name]: field.transform ? field.transform(value) : value };
      }, {});
      
      if (editando) {
        await clinicaApiClient.put(`${endpoint}${editando}/`, payload);
        toast.success('Atualizado com sucesso');
      } else {
        await clinicaApiClient.post(endpoint, payload);
        toast.success('Criado com sucesso');
      }
      setMostrarFormulario(false);
      loadItems();
      onSuccess?.();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setLoading(false);
    }
  };

  if (mostrarFormulario) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
          <h3 className="text-xl sm:text-2xl font-bold mb-6 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
            {icon} {editando ? 'Editar' : 'Novo'} {title}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {formFields.map((field: any) => (
                <div key={field.name} className={field.fullWidth ? 'md:col-span-2' : ''}>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {field.label} {field.required && '*'}
                  </label>
                  {field.type === 'select' ? (
                    <select
                      value={formData[field.name]}
                      onChange={(e) => setFormData((prev: any) => ({ ...prev, [field.name]: e.target.value }))}
                      required={field.required}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                    >
                      <option value="">Selecione...</option>
                      {field.options?.map((opt: any) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  ) : field.type === 'textarea' ? (
                    <textarea
                      value={formData[field.name]}
                      onChange={(e) => setFormData((prev: any) => ({ ...prev, [field.name]: e.target.value }))}
                      required={field.required}
                      rows={field.rows || 3}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                      placeholder={field.placeholder}
                    />
                  ) : (
                    <input
                      type={field.type || 'text'}
                      value={formData[field.name]}
                      onChange={(e) => setFormData((prev: any) => ({ ...prev, [field.name]: e.target.value }))}
                      required={field.required}
                      min={field.min}
                      step={field.step}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                      placeholder={field.placeholder}
                    />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <button type="button" onClick={() => setMostrarFormulario(false)} disabled={loading} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">Cancelar</button>
              <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{loading ? 'Salvando...' : (editando ? 'Atualizar' : 'Criar')}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto shadow-xl">
        <h3 className="text-xl sm:text-2xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>{icon} Gerenciar {title}</h3>
        {loadingLista ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : items.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400 mb-4">{emptyMessage}</p>
            <button onClick={handleNovo} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo</button>
          </div>
        ) : (
          <div className="space-y-4 mb-6">
            {items.map((item: any) => renderListItem(item, handleEditar, handleExcluir, loja))}
          </div>
        )}
        <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
          <button onClick={onClose} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">Fechar</button>
          <button onClick={handleNovo} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo</button>
        </div>
      </div>
    </div>
  );
}

// ==================== MODAL AGENDAMENTOS ====================
export function ModalAgendamentos({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const [clientes, setClientes] = useState<any[]>([]);
  const [servicos, setServicos] = useState<any[]>([]);
  const [profissionais, setProfissionais] = useState<any[]>([]);

  useEffect(() => {
    const loadDados = async () => {
      try {
        const [cliRes, servRes, profRes] = await Promise.all([
          clinicaApiClient.get('/servicos/clientes/'),
          clinicaApiClient.get('/servicos/servicos/'),
          clinicaApiClient.get('/servicos/profissionais/')
        ]);
        setClientes(Array.isArray(cliRes.data) ? cliRes.data : cliRes.data?.results ?? []);
        setServicos(Array.isArray(servRes.data) ? servRes.data : servRes.data?.results ?? []);
        setProfissionais(Array.isArray(profRes.data) ? profRes.data : profRes.data?.results ?? []);
      } catch (error) {
        console.error('Erro ao carregar dados:', error);
      }
    };
    loadDados();
  }, []);

  return (
    <ModalBase
      loja={loja}
      onClose={onClose}
      onSuccess={onSuccess}
      title="Agendamento"
      icon="📅"
      endpoint="/servicos/agendamentos/"
      formFields={[
        { name: 'cliente_id', apiName: 'cliente', label: 'Cliente', type: 'select', required: true, options: clientes.map(c => ({ value: c.id, label: c.nome })), fullWidth: true, transform: (v: string) => parseInt(v), getValue: (item: any) => String(item.cliente) },
        { name: 'servico_id', apiName: 'servico', label: 'Serviço', type: 'select', required: true, options: servicos.map(s => ({ value: s.id, label: s.nome })), transform: (v: string) => parseInt(v), getValue: (item: any) => String(item.servico) },
        { name: 'profissional_id', apiName: 'profissional', label: 'Profissional', type: 'select', options: profissionais.map(p => ({ value: p.id, label: p.nome })), transform: (v: string) => v ? parseInt(v) : null, getValue: (item: any) => item.profissional ? String(item.profissional) : '' },
        { name: 'data', label: 'Data', type: 'date', required: true },
        { name: 'horario', label: 'Horário', type: 'time', required: true },
        { name: 'status', label: 'Status', type: 'select', required: true, options: STATUS_AGENDAMENTO, defaultValue: 'agendado' },
        { name: 'valor', label: 'Valor (R$)', type: 'number', required: true, min: 0, step: 0.01, transform: (v: string) => parseFloat(v) },
        { name: 'endereco_atendimento', label: 'Endereço de Atendimento', type: 'text', fullWidth: true, placeholder: 'Se o serviço for no local do cliente', transform: (v: string) => v || null },
        { name: 'observacoes', label: 'Observações', type: 'textarea', fullWidth: true, transform: (v: string) => v || null }
      ]}
      renderListItem={(item: any, handleEditar: any, handleExcluir: any, loja: any) => (
        <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
          <div className="flex-1">
            <p className="font-semibold text-lg text-gray-900 dark:text-white">{item.cliente_nome}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.servico_nome} • {item.data} {item.horario}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.profissional_nome || 'Sem profissional'}</p>
            <span className="inline-block mt-2 px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-semibold rounded-full">{STATUS_AGENDAMENTO.find(s => s.value === item.status)?.label}</span>
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleEditar(item)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
            <button onClick={() => handleExcluir(item.id, item.cliente_nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
          </div>
        </div>
      )}
      emptyMessage="Nenhum agendamento cadastrado"
    />
  );
}

// ==================== MODAL CLIENTES ====================
export function ModalClientes({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <ModalBase
      loja={loja}
      onClose={onClose}
      title="Clientes"
      icon="👤"
      endpoint="/servicos/clientes/"
      formFields={[
        { name: 'nome', label: 'Nome', type: 'text', required: true, fullWidth: true },
        { name: 'email', label: 'Email', type: 'email', transform: (v: string) => v || null },
        { name: 'telefone', label: 'Telefone', type: 'tel', transform: (v: string) => v || null },
        { name: 'tipo_cliente', label: 'Tipo', type: 'select', required: true, options: [{ value: 'pf', label: 'Pessoa Física' }, { value: 'pj', label: 'Pessoa Jurídica' }], defaultValue: 'pf' },
        { name: 'observacoes', label: 'Observações', type: 'textarea', fullWidth: true, transform: (v: string) => v || null }
      ]}
      renderListItem={(item: any, handleEditar: any, handleExcluir: any, loja: any) => (
        <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
          <div className="flex-1">
            <p className="font-semibold text-lg text-gray-900 dark:text-white">{item.nome}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.email || 'Sem email'} • {item.telefone || 'Sem telefone'}</p>
            <span className="inline-block mt-2 px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 text-xs font-semibold rounded-full">{item.tipo_cliente === 'pf' ? 'Pessoa Física' : 'Pessoa Jurídica'}</span>
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleEditar(item)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
            <button onClick={() => handleExcluir(item.id, item.nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
          </div>
        </div>
      )}
    />
  );
}

// ==================== MODAL SERVIÇOS ====================
export function ModalServicos({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [categorias, setCategorias] = useState<any[]>([]);

  useEffect(() => {
    const loadCategorias = async () => {
      try {
        const res = await clinicaApiClient.get('/servicos/categorias/');
        setCategorias(Array.isArray(res.data) ? res.data : res.data?.results ?? []);
      } catch (error) {
        console.error('Erro ao carregar categorias:', error);
      }
    };
    loadCategorias();
  }, []);

  return (
    <ModalBase
      loja={loja}
      onClose={onClose}
      title="Serviços"
      icon="⚙️"
      endpoint="/servicos/servicos/"
      formFields={[
        { name: 'nome', label: 'Nome', type: 'text', required: true, fullWidth: true },
        { name: 'categoria_id', apiName: 'categoria', label: 'Categoria', type: 'select', options: categorias.map(c => ({ value: c.id, label: c.nome })), transform: (v: string) => v ? parseInt(v) : null, getValue: (item: any) => item.categoria ? String(item.categoria) : '' },
        { name: 'preco', label: 'Preço (R$)', type: 'number', required: true, min: 0, step: 0.01, transform: (v: string) => parseFloat(v) },
        { name: 'duracao_estimada', label: 'Duração (minutos)', type: 'number', required: true, min: 0, transform: (v: string) => parseInt(v) },
        { name: 'descricao', label: 'Descrição', type: 'textarea', required: true, fullWidth: true }
      ]}
      renderListItem={(item: any, handleEditar: any, handleExcluir: any, loja: any) => (
        <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
          <div className="flex-1">
            <p className="font-semibold text-lg text-gray-900 dark:text-white">{item.nome}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.descricao}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">R$ {Number(item.preco).toLocaleString('pt-BR', { minimumFractionDigits: 2 })} • {item.duracao_estimada} min</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleEditar(item)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
            <button onClick={() => handleExcluir(item.id, item.nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
          </div>
        </div>
      )}
    />
  );
}

// ==================== MODAL PROFISSIONAIS ====================
export function ModalProfissionais({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <ModalBase
      loja={loja}
      onClose={onClose}
      title="Profissionais"
      icon="👨‍🔧"
      endpoint="/servicos/profissionais/"
      formFields={[
        { name: 'nome', label: 'Nome', type: 'text', required: true, fullWidth: true },
        { name: 'email', label: 'Email', type: 'email', required: true },
        { name: 'telefone', label: 'Telefone', type: 'tel', required: true },
        { name: 'especialidade', label: 'Especialidade', type: 'text', required: true },
        { name: 'registro_profissional', label: 'Registro Profissional', type: 'text', placeholder: 'Ex: CREA, CRM, etc.', transform: (v: string) => v || null }
      ]}
      renderListItem={(item: any, handleEditar: any, handleExcluir: any, loja: any) => (
        <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
          <div className="flex-1">
            <p className="font-semibold text-lg text-gray-900 dark:text-white">{item.nome}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.especialidade}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.email} • {item.telefone}</p>
            {item.registro_profissional && <span className="inline-block mt-2 px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 text-xs font-semibold rounded-full">{item.registro_profissional}</span>}
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleEditar(item)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
            <button onClick={() => handleExcluir(item.id, item.nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
          </div>
        </div>
      )}
    />
  );
}

// ==================== MODAL ORDENS DE SERVIÇO ====================
export function ModalOrdensServico({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-xl">
        <h3 className="text-xl sm:text-2xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
          🔧 Gerenciar Ordens de Serviço
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">Funcionalidade em desenvolvimento...</p>
        <button onClick={onClose} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">
          Fechar
        </button>
      </div>
    </div>
  );
}

// ==================== MODAL ORÇAMENTOS ====================
export function ModalOrcamentos({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-xl">
        <h3 className="text-xl sm:text-2xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
          💰 Gerenciar Orçamentos
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">Funcionalidade em desenvolvimento...</p>
        <button onClick={onClose} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">
          Fechar
        </button>
      </div>
    </div>
  );
}

// ==================== MODAL FUNCIONÁRIOS ====================
export function ModalFuncionarios({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-xl">
        <h3 className="text-xl sm:text-2xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
          👥 Gerenciar Funcionários
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">Funcionalidade em desenvolvimento...</p>
        <button onClick={onClose} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">
          Fechar
        </button>
      </div>
    </div>
  );
}
