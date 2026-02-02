import { ensureArray } from '@/lib/array-helpers';
'use client';

import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { CrudModal } from '../shared/CrudModal';
import { FormField } from '../shared/FormField';
import type { LojaInfo } from '../shared/CrudModal';

interface Protocolo {
  id: number;
  nome: string;
  procedimento: number;
  procedimento_nome?: string;
  descricao: string;
  tempo_estimado: number;
  materiais_necessarios?: string;
  preparacao: string;
  execucao: string;
  pos_procedimento: string;
  contraindicacoes?: string;
  cuidados_especiais?: string;
  created_at?: string;
}

interface Procedimento {
  id: number;
  nome: string;
}

interface ModalProtocolosProps {
  loja: LojaInfo;
  onClose: () => void;
}

const initialFormData = {
  nome: '',
  procedimento: '',
  descricao: '',
  tempo_estimado: '',
  materiais_necessarios: '',
  preparacao: '',
  execucao: '',
  pos_procedimento: '',
  contraindicacoes: '',
  cuidados_especiais: ''
};

export function ModalProtocolos({ loja, onClose }: ModalProtocolosProps) {
  const [protocolos, setProtocolos] = useState<Protocolo[]>([]);
  const [procedimentos, setProcedimentos] = useState<Procedimento[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProtocolo, setEditingProtocolo] = useState<Protocolo | null>(null);
  const [formData, setFormData] = useState(initialFormData);
  const [submitting, setSubmitting] = useState(false);

  const loadProtocolos = useCallback(async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/protocolos/');
      setProtocolos(ensureArray(response.data));
    } catch (error) {
      console.error('Erro ao carregar protocolos:', error);
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
    loadProtocolos();
    loadProcedimentos();
  }, [loadProtocolos, loadProcedimentos]);

  const handleEdit = (protocolo: Protocolo) => {
    setEditingProtocolo(protocolo);
    setFormData({
      nome: protocolo.nome || '',
      procedimento: protocolo.procedimento?.toString() || '',
      descricao: protocolo.descricao || '',
      tempo_estimado: protocolo.tempo_estimado?.toString() || '',
      materiais_necessarios: protocolo.materiais_necessarios || '',
      preparacao: protocolo.preparacao || '',
      execucao: protocolo.execucao || '',
      pos_procedimento: protocolo.pos_procedimento || '',
      contraindicacoes: protocolo.contraindicacoes || '',
      cuidados_especiais: protocolo.cuidados_especiais || ''
    });
    setShowForm(true);
  };

  const handleDelete = async (protocolo: Protocolo) => {
    if (!confirm(`Tem certeza que deseja excluir o protocolo ${protocolo.nome}?`)) return;
    
    try {
      await clinicaApiClient.delete(`/clinica/protocolos/${protocolo.id}/`);
      alert('✅ Protocolo excluído com sucesso!');
      loadProtocolos();
    } catch (error) {
      console.error('Erro ao excluir protocolo:', error);
      alert('❌ Erro ao excluir protocolo');
    }
  };

  const resetForm = () => {
    setFormData(initialFormData);
    setEditingProtocolo(null);
    setShowForm(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      const cleanedData = Object.fromEntries(
        Object.entries(formData).map(([key, value]) => [key, value === '' ? null : value])
      );

      if (editingProtocolo) {
        await clinicaApiClient.put(`/clinica/protocolos/${editingProtocolo.id}/`, cleanedData);
        alert('✅ Protocolo atualizado com sucesso!');
      } else {
        await clinicaApiClient.post('/clinica/protocolos/', cleanedData);
        alert('✅ Protocolo criado com sucesso!');
      }
      loadProtocolos();
      resetForm();
    } catch (error) {
      console.error('Erro ao salvar protocolo:', error);
      alert('❌ Erro ao salvar protocolo');
    } finally {
      setSubmitting(false);
    }
  };

  const procedimentosOptions = procedimentos.map(p => ({ value: p.id, label: p.nome }));

  if (showForm) {
    return (
      <CrudModal loja={loja} onClose={resetForm} title={editingProtocolo ? 'Editar Protocolo' : 'Novo Protocolo de Procedimento'} icon="📋">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Nome do Protocolo" name="nome" value={formData.nome} onChange={handleChange} required placeholder="Ex: Protocolo Limpeza de Pele Profunda" colSpan={2} />
            <FormField label="Procedimento" name="procedimento" type="select" value={formData.procedimento} onChange={handleChange} required options={procedimentosOptions} />
            <FormField label="Tempo Estimado (minutos)" name="tempo_estimado" type="number" value={formData.tempo_estimado} onChange={handleChange} required min={1} placeholder="60" />
            <FormField label="Descrição" name="descricao" type="textarea" value={formData.descricao} onChange={handleChange} required rows={3} placeholder="Descreva o objetivo e benefícios do protocolo..." colSpan={2} />
            <FormField label="Materiais Necessários" name="materiais_necessarios" type="textarea" value={formData.materiais_necessarios} onChange={handleChange} rows={3} placeholder="Liste os materiais e produtos necessários..." colSpan={2} />
            <FormField label="Preparação" name="preparacao" type="textarea" value={formData.preparacao} onChange={handleChange} required rows={3} placeholder="Descreva a preparação do cliente e ambiente..." colSpan={2} />
            <FormField label="Execução" name="execucao" type="textarea" value={formData.execucao} onChange={handleChange} required rows={5} placeholder="1. Primeiro passo...&#10;2. Segundo passo...&#10;3. Terceiro passo..." colSpan={2} />
            <FormField label="Pós-Procedimento" name="pos_procedimento" type="textarea" value={formData.pos_procedimento} onChange={handleChange} required rows={3} placeholder="Cuidados após o procedimento..." colSpan={2} />
            <FormField label="Contraindicações" name="contraindicacoes" type="textarea" value={formData.contraindicacoes} onChange={handleChange} rows={2} placeholder="Situações em que o procedimento não deve ser realizado..." colSpan={2} />
            <FormField label="Cuidados Especiais" name="cuidados_especiais" type="textarea" value={formData.cuidados_especiais} onChange={handleChange} rows={2} placeholder="Cuidados especiais durante o procedimento..." colSpan={2} />
          </div>

          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button type="button" onClick={resetForm} disabled={submitting} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
              Cancelar
            </button>
            <button type="submit" disabled={submitting} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>
              {submitting ? 'Salvando...' : (editingProtocolo ? 'Atualizar' : 'Criar Protocolo')}
            </button>
          </div>
        </form>
      </CrudModal>
    );
  }

  return (
    <CrudModal loja={loja} onClose={onClose} title="Gerenciar Protocolos de Procedimentos" icon="📋" maxWidth="4xl" fullScreen>
      {loading ? (
        <div className="text-center py-8">Carregando protocolos...</div>
      ) : protocolos.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">Nenhum protocolo cadastrado</p>
          <p className="text-sm mb-4">Protocolos padronizam seus procedimentos e garantem qualidade</p>
          <button onClick={() => setShowForm(true)} className="px-6 py-3 rounded-md text-white hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
            + Criar Primeiro Protocolo
          </button>
        </div>
      ) : (
        <div className="space-y-4 mb-6">
          {protocolos.map((protocolo) => (
            <div key={protocolo.id} className="border rounded-lg p-4 hover:bg-gray-50">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="font-semibold text-lg">{protocolo.nome}</h4>
                  <p className="text-sm text-gray-600 mb-2">Procedimento: {protocolo.procedimento_nome}</p>
                  <p className="text-sm text-gray-700 mb-2">{protocolo.descricao}</p>
                  <div className="text-xs text-gray-500">
                    <span className="mr-4">⏱️ {protocolo.tempo_estimado} min</span>
                    {protocolo.created_at && (
                      <span>📅 Criado em {new Date(protocolo.created_at).toLocaleDateString('pt-BR')}</span>
                    )}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button onClick={() => handleEdit(protocolo)} className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600">
                    ✏️ Editar
                  </button>
                  <button onClick={() => handleDelete(protocolo)} className="px-4 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600">
                    🗑️ Excluir
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-end space-x-4">
        <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
          Fechar
        </button>
        <button onClick={() => setShowForm(true)} className="px-6 py-2 text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
          + Novo Protocolo
        </button>
      </div>
    </CrudModal>
  );
}
