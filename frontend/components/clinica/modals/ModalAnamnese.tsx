import { ensureArray } from '@/lib/array-helpers';
'use client';

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
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [formData, setFormData] = useState(initialFormData);
  const [submitting, setSubmitting] = useState(false);

  const loadAnamneses = useCallback(async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/anamneses/');
      setAnamneses(ensureArray(response.data));
    } catch (error) {
      console.error('Erro ao carregar anamneses:', error);
    }
  }, []);

  const loadTemplates = useCallback(async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/anamneses-templates/');
      setTemplates(ensureArray(response.data));
    } catch (error) {
      console.error('Erro ao carregar templates:', error);
    }
  }, []);

  const loadProcedimentos = useCallback(async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/procedimentos/');
      setProcedimentos(ensureArray(response.data));
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
  }, [loadAnamneses, loadTemplates, loadProcedimentos]);

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
              <h4 className="text-lg font-semibold text-gray-700">Perguntas</h4>
              <button type="button" onClick={addPergunta} className="px-4 py-2 text-sm text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
                + Adicionar Pergunta
              </button>
            </div>

            <div className="space-y-4">
              {formData.perguntas.map((pergunta, index) => (
                <div key={index} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex justify-between items-start mb-3">
                    <span className="text-sm font-medium text-gray-600">Pergunta {index + 1}</span>
                    {formData.perguntas.length > 1 && (
                      <button type="button" onClick={() => removePergunta(index)} className="text-red-500 hover:text-red-700 text-sm">
                        🗑️ Remover
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Pergunta *</label>
                      <input
                        type="text"
                        value={pergunta.pergunta}
                        onChange={(e) => handlePerguntaChange(index, 'pergunta', e.target.value)}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                        placeholder="Ex: Possui alguma alergia conhecida?"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Resposta</label>
                      <select
                        value={pergunta.tipo}
                        onChange={(e) => handlePerguntaChange(index, 'tipo', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
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
                        <span className="text-sm text-gray-700">Pergunta obrigatória</span>
                      </label>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button type="button" onClick={resetForm} disabled={submitting} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
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
    <CrudModal loja={loja} onClose={onClose} title="Sistema de Anamnese" icon="📝" maxWidth="4xl" fullScreen>
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
          <button className="px-6 py-2 text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
            + Nova Anamnese
          </button>
        )}
      </div>
    </CrudModal>
  );
}
