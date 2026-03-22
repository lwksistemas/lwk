'use client';

import { useState } from 'react';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { useLojaForm } from '@/hooks/useLojaForm';
import { FormularioCadastroLoja } from '@/components/cadastro/FormularioCadastroLoja';
import { SucessoCadastro } from '@/components/cadastro/SucessoCadastro';

export default function CadastroPublicoPage() {
  const [loading, setLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [createdLoja, setCreatedLoja] = useState<any>(null);
  
  // Hook customizado sem campo de senha (gerada automaticamente no backend)
  const lojaForm = useLojaForm(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        ...lojaForm.formData,
        provedor_boleto_preferido: lojaForm.formData.provedor_boleto_preferido || 'asaas',
      };
      
      const response = await apiClient.post('/superadmin/lojas/', payload);
      const loja = response.data;
      setCreatedLoja(loja);
      setShowSuccess(true);
    } catch (error: any) {
      console.error('Erro ao criar loja:', error);
      
      let mensagemErro = '❌ Erro ao criar cadastro:\n\n';
      
      if (error.response?.data) {
        if (typeof error.response.data === 'object') {
          Object.entries(error.response.data).forEach(([campo, erros]: [string, any]) => {
            if (Array.isArray(erros)) {
              mensagemErro += `• ${campo}: ${erros.join(', ')}\n`;
            } else {
              mensagemErro += `• ${campo}: ${erros}\n`;
            }
          });
        } else {
          mensagemErro += error.response.data;
        }
      } else {
        mensagemErro += 'Erro desconhecido ao criar cadastro';
      }
      
      alert(mensagemErro);
    } finally {
      setLoading(false);
    }
  };

  if (showSuccess && createdLoja) {
    return <SucessoCadastro loja={createdLoja} email={lojaForm.formData.owner_email} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-6">
            <Link href="/" className="text-white/80 hover:text-white text-sm mb-2 inline-block">
              ← Voltar para home
            </Link>
            <h1 className="text-3xl font-bold mb-2">Cadastro de Nova Empresa</h1>
            <p className="text-blue-100">Preencha os dados abaixo para começar a usar o sistema</p>
          </div>

          {/* Formulário */}
          <FormularioCadastroLoja
            lojaForm={lojaForm}
            onSubmit={handleSubmit}
            loading={loading}
            mostrarSenha={false}
          />
        </div>
      </div>
    </div>
  );
}
