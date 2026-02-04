'use client';

import { useState, useEffect } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { ModalBase } from './ModalBase';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

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
