'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ArrowLeft, Database, Download, Upload, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import BackupButton from '@/components/loja/BackupButton';
import apiClient from '@/lib/api-client';

interface LojaInfo {
  id: number;
  nome: string;
}

export default function BackupPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const [loja, setLoja] = useState<LojaInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const carregarLoja = async () => {
      if (!slug) {
        setLoading(false);
        return;
      }
      try {
        // Buscar loja pela API usando o slug da URL (evita sessionStorage desatualizado)
        const { data } = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
        if (data?.id) {
          setLoja({
            id: data.id,
            nome: data.nome || slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())
          });
          sessionStorage.setItem('current_loja_id', String(data.id));
        } else {
          console.error('Loja não encontrada para slug:', slug);
        }
      } catch (error) {
        console.error('Erro ao carregar loja:', error);
      } finally {
        setLoading(false);
      }
    };
    carregarLoja();
  }, [slug]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-gray-500 dark:text-gray-400">Carregando...</div>
      </div>
    );
  }

  if (!loja) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-sm text-red-600 dark:text-red-400">Erro ao carregar informações da loja.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href={`/loja/${slug}/crm-vendas/configuracoes`}
          className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-[#0176d3] dark:hover:text-[#0176d3] transition-colors"
        >
          <ArrowLeft size={16} />
          Voltar às configurações
        </Link>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Database size={28} className="text-[#0176d3]" />
          Backup de Dados
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Exporte e importe os dados da sua loja com segurança
        </p>
      </div>

      {/* Aviso Importante */}
      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
        <div className="flex gap-3">
          <AlertCircle size={20} className="text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-amber-800 dark:text-amber-300 mb-1">
              Importante
            </h3>
            <ul className="text-sm text-amber-700 dark:text-amber-400 space-y-1">
              <li>• O backup inclui todos os dados do CRM (leads, oportunidades, atividades, etc.)</li>
              <li>• Ao importar um backup, os dados atuais serão substituídos</li>
              <li>• Recomendamos fazer backups regulares dos seus dados</li>
              <li>• O arquivo de backup é um arquivo .zip compactado</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Cards de Ação */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Exportar Backup */}
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
          <div className="flex items-start gap-4 mb-4">
            <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
              <Download size={24} />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                Exportar Backup
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Baixe uma cópia de segurança de todos os seus dados
              </p>
            </div>
          </div>
          <ul className="space-y-2 mb-4 text-sm text-gray-600 dark:text-gray-400">
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
              Leads e oportunidades
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
              Atividades e calendário
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
              Contas e contatos
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
              Configurações personalizadas
            </li>
          </ul>
          <BackupButton 
            lojaId={loja.id} 
            lojaNome={loja.nome}
            className="w-full !bg-green-600 hover:!bg-green-700"
            exportOnly={true}
          />
        </div>

        {/* Importar Backup */}
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
          <div className="flex items-start gap-4 mb-4">
            <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
              <Upload size={24} />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                Importar Backup
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Restaure dados de um backup anterior
              </p>
            </div>
          </div>
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-4">
            <p className="text-xs text-red-700 dark:text-red-400">
              <strong>Atenção:</strong> A importação irá substituir todos os dados atuais. 
              Recomendamos exportar um backup antes de importar.
            </p>
          </div>
          <ul className="space-y-2 mb-4 text-sm text-gray-600 dark:text-gray-400">
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
              Arquivo .zip de backup
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
              Máximo 50MB
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
              Processo pode levar alguns minutos
            </li>
          </ul>
          <BackupButton 
            lojaId={loja.id} 
            lojaNome={loja.nome}
            className="w-full !bg-blue-600 hover:!bg-blue-700"
            importOnly={true}
          />
        </div>

        {/* Configurar Backup Automático */}
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
          <div className="flex items-start gap-4 mb-4">
            <div className="p-3 rounded-lg bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                Backup Automático
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Configure backups automáticos por email
              </p>
            </div>
          </div>
          <ul className="space-y-2 mb-4 text-sm text-gray-600 dark:text-gray-400">
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
              Backup diário, semanal ou mensal
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
              Receba por email automaticamente
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
              Configure horário de envio
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
              Backup manual sob demanda
            </li>
          </ul>
          <BackupButton 
            lojaId={loja.id} 
            lojaNome={loja.nome}
            className="w-full !bg-purple-600 hover:!bg-purple-700"
            configOnly={true}
          />
        </div>
      </div>

      {/* Dicas */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-2">
          💡 Dicas de Backup
        </h3>
        <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
          <li>• Faça backups regulares (recomendamos semanalmente)</li>
          <li>• Guarde os arquivos de backup em local seguro (nuvem, HD externo)</li>
          <li>• Teste a restauração periodicamente para garantir que o backup está funcionando</li>
          <li>• Mantenha múltiplas versões de backup (não sobrescreva o backup anterior)</li>
        </ul>
      </div>
    </div>
  );
}
