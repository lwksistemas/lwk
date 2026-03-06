'use client';

import { useState } from 'react';
import apiClient from '@/lib/api-client';
import { useToast, ToastContainer } from '@/components/ToastNotificacao';
import { getBackupErrorMessage, BACKUP_MAX_UPLOAD_BYTES } from '@/lib/backup-utils';
import BackupConfigModal from '@/components/loja/BackupConfigModal';

interface BackupButtonProps {
  lojaId: number;
  lojaNome: string;
  className?: string;
}

export default function BackupButton({ lojaId, lojaNome, className = '' }: BackupButtonProps) {
  const [loading, setLoading] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [showModalConfig, setShowModalConfig] = useState(false);
  const { toasts, addToast, removeToast } = useToast();

  const handleExportarBackup = async () => {
    try {
      setLoading(true);
      setShowMenu(false);
      
      addToast({
        tipo: 'info',
        titulo: 'Backup',
        mensagem: 'Iniciando exportação do backup...'
      });
      
      const response = await apiClient.post(
        `/superadmin/lojas/${lojaId}/exportar_backup/`,
        { incluir_imagens: false },
        { responseType: 'blob' }
      );
      
      // Criar URL do blob e fazer download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Obter nome do arquivo do header ou usar padrão
      const contentDisposition = response.headers['content-disposition'];
      let filename = `backup_${lojaNome.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.zip`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      const totalRegistros = response.headers['x-total-registros'] != null
        ? parseInt(response.headers['x-total-registros'], 10)
        : null;
      const tamanhoMb = response.headers['x-tamanho-mb'];
      let mensagem = 'Backup exportado com sucesso!';
      if (totalRegistros !== null || tamanhoMb) {
        const partes: string[] = [];
        if (totalRegistros !== null) partes.push(`${totalRegistros.toLocaleString('pt-BR')} registro(s)`);
        if (tamanhoMb) partes.push(`${tamanhoMb} MB`);
        if (partes.length) mensagem += ` (${partes.join(', ')})`;
        if (totalRegistros === 0) {
          mensagem += '. Nenhum dado no banco da loja; se isso for inesperado, entre em contato com o suporte.';
        }
      }

      addToast({
        tipo: 'sucesso',
        titulo: 'Backup',
        mensagem
      });
    } catch (error: any) {
      console.error('Erro ao exportar backup:', error);
      const msg = await getBackupErrorMessage(error, 'Erro ao exportar backup');
      addToast({ tipo: 'erro', titulo: 'Erro', mensagem: msg });
    } finally {
      setLoading(false);
    }
  };

  const handleImportarBackup = () => {
    setShowMenu(false);
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.zip';
    
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (!file) return;
      
      if (!file.name.endsWith('.zip')) {
        addToast({
          tipo: 'erro',
          titulo: 'Erro',
          mensagem: 'Por favor, selecione um arquivo ZIP'
        });
        return;
      }
      
      if (file.size > BACKUP_MAX_UPLOAD_BYTES) {
        addToast({
          tipo: 'erro',
          titulo: 'Erro',
          mensagem: `Arquivo muito grande. Máximo: ${BACKUP_MAX_UPLOAD_BYTES / (1024 * 1024)}MB`
        });
        return;
      }
      
      if (!confirm('⚠️ ATENÇÃO: A importação irá substituir TODOS os dados atuais da loja. Deseja continuar?')) {
        return;
      }
      
      try {
        setLoading(true);
        addToast({
          tipo: 'info',
          titulo: 'Backup',
          mensagem: 'Importando backup... Isso pode levar alguns minutos.'
        });
        
        const formData = new FormData();
        formData.append('arquivo', file);
        
        const response = await apiClient.post(
          `/superadmin/lojas/${lojaId}/importar_backup/`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );
        
        if (response.data.success) {
          addToast({
            tipo: 'sucesso',
            titulo: 'Backup',
            mensagem: `Backup importado! ${response.data.total_registros_importados} registros restaurados.`
          });
          
          // Recarregar página após 2 segundos
          setTimeout(() => {
            window.location.reload();
          }, 2000);
        } else {
          addToast({
            tipo: 'erro',
            titulo: 'Erro',
            mensagem: response.data.error || 'Erro ao importar backup'
          });
        }
      } catch (error: any) {
        console.error('Erro ao importar backup:', error);
        const msg = await getBackupErrorMessage(error, 'Erro ao importar backup', { isImport: true });
        addToast({ tipo: 'erro', titulo: 'Erro', mensagem: msg });
      } finally {
        setLoading(false);
      }
    };
    
    input.click();
  };

  const handleConfigurarBackup = () => {
    setShowMenu(false);
    setShowModalConfig(true);
  };

  return (
    <>
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      <div className="relative">
        <button
          onClick={() => setShowMenu(!showMenu)}
          disabled={loading}
          className={`flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
          title="Gerenciar backups"
        >
          <span>💾</span>
          <span className="hidden sm:inline">Backup</span>
          {loading && (
            <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          )}
        </button>

        {showMenu && !loading && (
          <>
            {/* Overlay para fechar o menu */}
            <div
              className="fixed inset-0 z-10"
              onClick={() => setShowMenu(false)}
            />
            
            {/* Menu dropdown */}
            <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-20">
              <div className="py-1">
                <button
                  onClick={handleExportarBackup}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                >
                  <span>📤</span>
                  <span>Exportar Backup</span>
                </button>
                
                <button
                  onClick={handleImportarBackup}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                >
                  <span>📥</span>
                  <span>Importar Backup</span>
                </button>
                
                <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                
                <button
                  onClick={handleConfigurarBackup}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                >
                  <span>⚙️</span>
                  <span>Backup por email (automático ou manual)</span>
                </button>
              </div>
            </div>
          </>
        )}

        <BackupConfigModal
          open={showModalConfig}
          onClose={() => setShowModalConfig(false)}
          lojaId={lojaId}
          addToast={addToast}
        />
      </div>
    </>
  );
}
