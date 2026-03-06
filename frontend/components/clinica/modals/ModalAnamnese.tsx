'use client';
import { ensureArray } from '@/lib/array-helpers';

import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { CrudModal } from '../shared/CrudModal';
import { FormField } from '../shared/FormField';
import type { LojaInfo } from '../shared/CrudModal';

interface Anamnese {
  id: number;
  cliente_nome: string;
  template_nome: string;
  created_at: string;
  data_assinatura?: string;
}

interface Template {
  id: number;
  nome: string;
  procedimento: number;
  procedimento_nome?: string;
  descricao?: string;
  perguntas: string;
  created_at: string;
}

interface Procedimento {
  id: number;
  nome: string;
}

interface Pergunta {
  pergunta: string;
  tipo: string;
  obrigatoria: boolean;
}

interface ModalAnamneseProps {
  loja: LojaInfo;
  onClose: () => void;
}

const initialFormData = {
  nome: '',
  procedimento: '',
  descricao: '',
  perguntas: [{ pergunta: '', tipo: 'texto', obrigatoria: true }] as Pergunta[]
};

export function ModalAnamnese({ loja, onClose }: ModalAnamneseProps) {
  const [anamneses, setAnamneses] = useState<Anamnese[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [procedimentos, setProcedimentos] = useState<Procedimento[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'anamneses' | 'templates'>('templates');
  const [showForm, setShowForm] = useState(false);
  const [showAnamneseForm, setShowAnamneseForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [formData, setFormData] = useState(initialFormData);
  // Estados para nova anamnese
  const [clientes, setClientes] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [selectedCliente, setSelectedCliente] = useState<string>('');
  const [respostas, setRespostas] = useState<Record<number, string>>({});
  const [submitting, setSubmitting] = useState(false);

  const loadClientes = useCallback(async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/clientes/');
      setClientes(ensureArray<any>(response.data));
    } catch (error) {
      console.error('Erro ao carregar clientes:', error);
    }
  }, []);

  const loadAnamneses = useCallback(async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/anamneses/');
      setAnamneses(ensureArray<Anamnese>(response.data));
    } catch (error) {
      console.error('Erro ao carregar anamneses:', error);
    }
  }, []);

  const loadTemplates = useCallback(async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/anamneses-templates/');
      setTemplates(ensureArray<Template>(response.data));
    } catch (error) {
      console.error('Erro ao carregar templates:', error);
    }
  }, []);

  const loadProcedimentos = useCallback(async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/procedimentos/');
      setProcedimentos(ensureArray<Procedimento>(response.data));
    } catch (error) {
      console.error('Erro ao carregar procedimentos:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAnamneses();
    loadTemplates();
    loadProcedimentos();
    loadClientes();
  }, [loadAnamneses, loadTemplates, loadProcedimentos, loadClientes]);

  const handleEditTemplate = (template: Template) => {
    setEditingTemplate(template);
    const perguntas = template.perguntas ? JSON.parse(template.perguntas) : [{ pergunta: '', tipo: 'texto', obrigatoria: true }];
    setFormData({
      nome: template.nome || '',
      procedimento: template.procedimento?.toString() || '',
      descricao: template.descricao || '',
      perguntas: perguntas
    });
    setShowForm(true);
  };

  const handleDeleteTemplate = async (template: Template) => {
    if (!confirm(`Tem certeza que deseja excluir o template ${template.nome}?`)) return;
    
    try {
      await clinicaApiClient.delete(`/clinica/anamneses-templates/${template.id}/`);
      alert('✅ Template excluído com sucesso!');
      loadTemplates();
    } catch (error) {
      console.error('Erro ao excluir template:', error);
      alert('❌ Erro ao excluir template');
    }
  };

  const resetForm = () => {
    setFormData(initialFormData);
    setEditingTemplate(null);
    setShowForm(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handlePerguntaChange = (index: number, field: string, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      perguntas: prev.perguntas.map((p, i) => 
        i === index ? { ...p, [field]: value } : p
      )
    }));
  };

  const addPergunta = () => {
    setFormData(prev => ({
      ...prev,
      perguntas: [...prev.perguntas, { pergunta: '', tipo: 'texto', obrigatoria: true }]
    }));
  };

  const removePergunta = (index: number) => {
    if (formData.perguntas.length > 1) {
      setFormData(prev => ({
        ...prev,
        perguntas: prev.perguntas.filter((_, i) => i !== index)
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      const templateData = {
        nome: formData.nome || null,
        procedimento: formData.procedimento || null,
        descricao: formData.descricao || null,
        perguntas: JSON.stringify(formData.perguntas)
      };
      
      if (editingTemplate) {
        await clinicaApiClient.put(`/clinica/anamneses-templates/${editingTemplate.id}/`, templateData);
        alert('✅ Template atualizado com sucesso!');
      } else {
        await clinicaApiClient.post('/clinica/anamneses-templates/', templateData);
        alert('✅ Template de anamnese criado com sucesso!');
      }
      loadTemplates();
      resetForm();
    } catch (error) {
      console.error('Erro ao salvar template:', error);
      alert('❌ Erro ao salvar template');
    } finally {
      setSubmitting(false);
    }
  };

  const procedimentosOptions = procedimentos.map(p => ({ value: p.id, label: p.nome }));

  // Formulário de nova anamnese (preencher)
  if (showAnamneseForm) {
    const templateSelecionado = templates.find(t => t.id.toString() === selectedTemplate);
    const perguntas: Pergunta[] = templateSelecionado ? JSON.parse(templateSelecionado.perguntas || '[]') : [];

    const handleSubmitAnamnese = async (e: React.FormEvent) => {
      e.preventDefault();
      setSubmitting(true);

      try {
        const anamneseData = {
          cliente: parseInt(selectedCliente),
          template: parseInt(selectedTemplate),
          respostas: JSON.stringify(respostas),
          data_preenchimento: new Date().toISOString().split('T')[0]
        };

        await clinicaApiClient.post('/clinica/anamneses/', anamneseData);
        alert('✅ Anamnese preenchida com sucesso!');
        loadAnamneses();
        setShowAnamneseForm(false);
        setSelectedTemplate('');
        setSelectedCliente('');
        setRespostas({});
      } catch (error) {
        console.error('Erro ao salvar anamnese:', error);
        alert('❌ Erro ao salvar anamnese');
      } finally {
        setSubmitting(false);
      }
    };

    return (
      <CrudModal loja={loja} onClose={() => {
        setShowAnamneseForm(false);
        setSelectedTemplate('');
        setSelectedCliente('');
        setRespostas({});
      }} title="Nova Anamnese" icon="📝" maxWidth="4xl">
        <form onSubmit={handleSubmitAnamnese} className="space-y-6">
          {/* Seleção de Cliente e Template */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-4 border-b dark:border-gray-700">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Cliente *
              </label>
              <select
                value={selectedCliente}
                onChange={(e) => setSelectedCliente(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Selecione um cliente...</option>
                {clientes.map(cliente => (
                  <option key={cliente.id} value={cliente.id}>
                    {cliente.nome}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Template *
              </label>
              <select
                value={selectedTemplate}
                onChange={(e) => {
                  setSelectedTemplate(e.target.value);
                  setRespostas({});
                }}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Selecione um template...</option>
                {templates.map(template => (
                  <option key={template.id} value={template.id}>
                    {template.nome} - {template.procedimento_nome}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Perguntas do Template */}
          {templateSelecionado && perguntas.length > 0 && (
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                {templateSelecionado.nome}
              </h4>
              {templateSelecionado.descricao && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {templateSelecionado.descricao}
                </p>
              )}

              {perguntas.map((pergunta, index) => (
                <div key={index} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {index + 1}. {pergunta.pergunta}
                    {pergunta.obrigatoria && <span className="text-red-500 ml-1">*</span>}
                  </label>

                  {pergunta.tipo === 'texto' && (
                    <textarea
                      value={respostas[index] || ''}
                      onChange={(e) => setRespostas(prev => ({ ...prev, [index]: e.target.value }))}
                      required={pergunta.obrigatoria}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white 
                                 resize-none"
                      placeholder="Digite sua resposta..."
                    />
                  )}

                  {pergunta.tipo === 'sim_nao' && (
                    <div className="flex space-x-4">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name={`pergunta_${index}`}
                          value="Sim"
                          checked={respostas[index] === 'Sim'}
                          onChange={(e) => setRespostas(prev => ({ ...prev, [index]: e.target.value }))}
                          required={pergunta.obrigatoria}
                          className="mr-2"
                        />
                        <span className="text-gray-700 dark:text-gray-300">Sim</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name={`pergunta_${index}`}
                          value="Não"
                          checked={respostas[index] === 'Não'}
                          onChange={(e) => setRespostas(prev => ({ ...prev, [index]: e.target.value }))}
                          required={pergunta.obrigatoria}
                          className="mr-2"
                        />
                        <span className="text-gray-700 dark:text-gray-300">Não</span>
                      </label>
                    </div>
                  )}

                  {pergunta.tipo === 'numero' && (
                    <input
                      type="number"
                      value={respostas[index] || ''}
                      onChange={(e) => setRespostas(prev => ({ ...prev, [index]: e.target.value }))}
                      required={pergunta.obrigatoria}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="Digite um número..."
                    />
                  )}

                  {pergunta.tipo === 'data' && (
                    <input
                      type="date"
                      value={respostas[index] || ''}
                      onChange={(e) => setRespostas(prev => ({ ...prev, [index]: e.target.value }))}
                      required={pergunta.obrigatoria}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  )}
                </div>
              ))}
            </div>
          )}

          {!templateSelecionado && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <p>Selecione um cliente e um template para começar</p>
            </div>
          )}

          {/* Botões */}
          <div className="flex justify-end space-x-4 pt-4 border-t dark:border-gray-700">
            <button
              type="button"
              onClick={() => {
                setShowAnamneseForm(false);
                setSelectedTemplate('');
                setSelectedCliente('');
                setRespostas({});
              }}
              disabled={submitting}
              className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                         hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 
                         text-gray-900 dark:text-white"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || !selectedTemplate || !selectedCliente}
              className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              {submitting ? 'Salvando...' : '💾 Salvar Anamnese'}
            </button>
          </div>
        </form>
      </CrudModal>
    );
  }

  // Formulário de template
  if (showForm) {
    return (
      <CrudModal loja={loja} onClose={resetForm} title={editingTemplate ? 'Editar Template' : 'Novo Template de Anamnese'} icon="📝" maxWidth="4xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Nome do Template" name="nome" value={formData.nome} onChange={handleChange} required placeholder="Ex: Anamnese Limpeza de Pele" colSpan={2} />
            <FormField label="Procedimento" name="procedimento" type="select" value={formData.procedimento} onChange={handleChange} required options={procedimentosOptions} />
            <FormField label="Descrição" name="descricao" type="textarea" value={formData.descricao} onChange={handleChange} rows={2} placeholder="Descreva o objetivo desta anamnese..." colSpan={2} />
          </div>

          <div>
            <div className="flex justify-between items-center mb-4">
              <h4 className="text-lg font-semibold text-gray-700 dark:text-gray-300">Perguntas</h4>
              <button type="button" onClick={addPergunta} className="px-4 py-2 text-sm text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
                + Adicionar Pergunta
              </button>
            </div>

            <div className="space-y-4">
              {formData.perguntas.map((pergunta, index) => (
                <div key={index} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 bg-gray-50 dark:bg-gray-700/50">
                  <div className="flex justify-between items-start mb-3">
                    <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Pergunta {index + 1}</span>
                    {formData.perguntas.length > 1 && (
                      <button type="button" onClick={() => removePergunta(index)} className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-sm">
                        🗑️ Remover
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Pergunta *</label>
                      <input
                        type="text"
                        value={pergunta.pergunta}
                        onChange={(e) => handlePerguntaChange(index, 'pergunta', e.target.value)}
                        required
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        placeholder="Ex: Possui alguma alergia conhecida?"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo de Resposta</label>
                      <select
                        value={pergunta.tipo}
                        onChange={(e) => handlePerguntaChange(index, 'tipo', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      >
                        <option value="texto">Texto</option>
                        <option value="sim_nao">Sim/Não</option>
                        <option value="multipla_escolha">Múltipla Escolha</option>
                        <option value="numero">Número</option>
                        <option value="data">Data</option>
                      </select>
                    </div>

                    <div className="md:col-span-3">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={pergunta.obrigatoria}
                          onChange={(e) => handlePerguntaChange(index, 'obrigatoria', e.target.checked)}
                          className="mr-2"
                        />
                        <span className="text-sm text-gray-700 dark:text-gray-300">Pergunta obrigatória</span>
                      </label>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end space-x-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button type="button" onClick={resetForm} disabled={submitting} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 text-gray-900 dark:text-white">
              Cancelar
            </button>
            <button type="submit" disabled={submitting} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>
              {submitting ? 'Salvando...' : (editingTemplate ? 'Atualizar' : 'Criar Template')}
            </button>
          </div>
        </form>
      </CrudModal>
    );
  }

  // Lista principal com tabs
  return (
    <CrudModal loja={loja} onClose={onClose} title="Sistema de Anamnese" icon="📝" maxWidth="4xl">
      {/* Tabs */}
      <div className="flex border-b mb-6">
        <button
          onClick={() => setActiveTab('templates')}
          className={`px-4 py-2 font-medium ${activeTab === 'templates' ? 'border-b-2' : 'text-gray-500 hover:text-gray-700'}`}
          style={activeTab === 'templates' ? { borderColor: loja.cor_primaria, color: loja.cor_primaria } : {}}
        >
          Templates ({templates.length})
        </button>
        <button
          onClick={() => setActiveTab('anamneses')}
          className={`px-4 py-2 font-medium ml-4 ${activeTab === 'anamneses' ? 'border-b-2' : 'text-gray-500 hover:text-gray-700'}`}
          style={activeTab === 'anamneses' ? { borderColor: loja.cor_primaria, color: loja.cor_primaria } : {}}
        >
          Anamneses Preenchidas ({anamneses.length})
        </button>
      </div>
      
      {loading ? (
        <div className="text-center py-8">Carregando...</div>
      ) : (
        <div>
          {activeTab === 'templates' ? (
            templates.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg mb-2">Nenhum template criado</p>
                <p className="text-sm mb-4">Crie templates personalizados para diferentes procedimentos</p>
                <button onClick={() => setShowForm(true)} className="px-6 py-3 rounded-md text-white hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
                  + Criar Template
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {templates.map((template) => (
                  <div key={template.id} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-semibold text-lg">{template.nome}</h4>
                        <p className="text-sm text-gray-600 mb-2">Procedimento: {template.procedimento_nome}</p>
                        <p className="text-sm text-gray-700 mb-2">{template.descricao}</p>
                        <div className="text-xs text-gray-500">
                          <span>❓ {JSON.parse(template.perguntas || '[]').length} perguntas</span>
                          <span className="ml-4">📅 {new Date(template.created_at).toLocaleDateString('pt-BR')}</span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button onClick={() => handleEditTemplate(template)} className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600">
                          ✏️ Editar
                        </button>
                        <button onClick={() => handleDeleteTemplate(template)} className="px-4 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600">
                          🗑️ Excluir
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )
          ) : (
            anamneses.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg mb-2">Nenhuma anamnese preenchida</p>
                <p className="text-sm mb-4">Anamneses ajudam a conhecer melhor seus pacientes</p>
              </div>
            ) : (
              <div className="space-y-4">
                {anamneses.map((anamnese) => (
                  <div key={anamnese.id} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-semibold text-lg">{anamnese.cliente_nome}</h4>
                        <p className="text-sm text-gray-600 mb-2">Template: {anamnese.template_nome}</p>
                        <div className="text-xs text-gray-500">
                          <span>📅 {new Date(anamnese.created_at).toLocaleDateString('pt-BR')}</span>
                          {anamnese.data_assinatura && (
                            <span className="ml-4">✅ Assinado</span>
                          )}
                        </div>
                      </div>
                      <button className="px-4 py-2 text-sm text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
                        Ver Respostas
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      )}

      <div className="flex justify-end space-x-4 mt-6">
        <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
          Fechar
        </button>
        {activeTab === 'templates' && (
          <button onClick={() => setShowForm(true)} className="px-6 py-2 text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
            + Novo Template
          </button>
        )}
        {activeTab === 'anamneses' && templates.length > 0 && (
          <button 
            onClick={() => setShowAnamneseForm(true)} 
            className="px-6 py-2 text-white rounded-md hover:opacity-90" 
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Nova Anamnese
          </button>
        )}
      </div>
    </CrudModal>
  );
}
