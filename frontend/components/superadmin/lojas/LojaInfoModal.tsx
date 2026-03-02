'use client';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tamanho_banco_mb: number | null;
  tamanho_banco_estimativa_mb: number;
  tamanho_banco_motivo: string | null;
  database_created: boolean;
  espaco_plano_gb: number | null;
  espaco_livre_gb: number | null;
  senha_provisoria: string;
  login_page_url: string;
  owner_username: string;
  owner_email: string;
  owner_telefone?: string;
  storage_usado_mb?: number;
  storage_limite_mb?: number;
  storage_livre_mb?: number;
  storage_livre_gb?: number;
  storage_percentual?: number;
  storage_status?: string;
  storage_status_texto?: string;
  storage_alerta_enviado?: boolean;
  storage_ultima_verificacao?: string | null;
  storage_horas_desde_verificacao?: number | null;
  plano_nome?: string;
}

interface LojaInfoModalProps {
  lojaInfo: LojaInfo | null;
  loading: boolean;
  onClose: () => void;
}

export function LojaInfoModal({ lojaInfo, loading, onClose }: LojaInfoModalProps) {
  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" 
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden" 
        onClick={e => e.stopPropagation()}
      >
        <div className="bg-purple-900 text-white px-6 py-4">
          <h2 className="text-xl font-bold">Informações da Loja</h2>
        </div>
        
        <div className="p-6">
          {loading ? (
            <div className="text-center py-8 text-gray-500">Carregando...</div>
          ) : lojaInfo ? (
            <div className="space-y-4 text-sm">
              <div>
                <span className="font-semibold text-gray-500 block mb-1">Loja</span>
                <p className="font-medium text-gray-900">{lojaInfo.nome}</p>
              </div>
              
              {/* Storage */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="font-semibold text-gray-500 block mb-1">Storage usado</span>
                  <p className="text-gray-900">
                    {lojaInfo.storage_usado_mb != null
                      ? `${lojaInfo.storage_usado_mb.toFixed(2)} MB`
                      : '0.00 MB'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {lojaInfo.storage_percentual != null
                      ? `${lojaInfo.storage_percentual.toFixed(1)}% do limite`
                      : 'Aguardando verificação'}
                  </p>
                </div>
                <div>
                  <span className="font-semibold text-gray-500 block mb-1">Storage disponível</span>
                  <p className="text-gray-900">
                    {lojaInfo.storage_livre_gb != null 
                      ? `${lojaInfo.storage_livre_gb} GB` 
                      : lojaInfo.espaco_plano_gb != null 
                      ? `${lojaInfo.espaco_plano_gb} GB (plano)` 
                      : '—'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Limite: {lojaInfo.storage_limite_mb != null 
                      ? `${(lojaInfo.storage_limite_mb / 1024).toFixed(0)} GB` 
                      : '5 GB'}
                  </p>
                </div>
              </div>
              
              {/* Status do Storage */}
              {lojaInfo.storage_status && (
                <div className={`p-3 rounded-lg ${
                  lojaInfo.storage_status === 'critical' 
                    ? 'bg-red-50 border border-red-200' 
                    : lojaInfo.storage_status === 'warning'
                    ? 'bg-yellow-50 border border-yellow-200'
                    : 'bg-green-50 border border-green-200'
                }`}>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${
                      lojaInfo.storage_status === 'critical'
                        ? 'text-red-700'
                        : lojaInfo.storage_status === 'warning'
                        ? 'text-yellow-700'
                        : 'text-green-700'
                    }`}>
                      {lojaInfo.storage_status === 'critical' && '🚫'}
                      {lojaInfo.storage_status === 'warning' && '⚠️'}
                      {lojaInfo.storage_status === 'ok' && '✅'}
                      {' '}
                      {lojaInfo.storage_status_texto}
                    </span>
                  </div>
                  {lojaInfo.storage_ultima_verificacao && (
                    <p className="text-xs text-gray-600 mt-1">
                      Última verificação: {lojaInfo.storage_horas_desde_verificacao != null 
                        ? `há ${lojaInfo.storage_horas_desde_verificacao}h` 
                        : 'recente'}
                    </p>
                  )}
                </div>
              )}
              
              {/* Senha */}
              <div>
                <span className="font-semibold text-gray-500 block mb-1">Senha de acesso</span>
                <p className="text-gray-900 font-mono bg-gray-100 px-2 py-1 rounded break-all">
                  {lojaInfo.senha_provisoria || '—'}
                </p>
              </div>
              
              {/* Login URL */}
              <div>
                <span className="font-semibold text-gray-500 block mb-1">Página de login da loja</span>
                <p className="text-gray-900 break-all">
                  {lojaInfo.login_page_url ? (
                    <a
                      href={typeof window !== 'undefined' ? `${window.location.origin}${lojaInfo.login_page_url}` : lojaInfo.login_page_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-600 hover:text-purple-800 underline"
                    >
                      {typeof window !== 'undefined' ? `${window.location.origin}${lojaInfo.login_page_url}` : lojaInfo.login_page_url}
                    </a>
                  ) : '—'}
                </p>
              </div>
              
              {/* Owner */}
              <div className="pt-2 border-t border-gray-200">
                <span className="font-semibold text-gray-500 block mb-1">Usuário / E-mail</span>
                <p className="text-gray-900">{lojaInfo.owner_username} — {lojaInfo.owner_email}</p>
                {lojaInfo.owner_telefone && (
                  <p className="text-gray-600 text-sm mt-1">Tel: {lojaInfo.owner_telefone}</p>
                )}
              </div>
            </div>
          ) : null}
        </div>
        
        <div className="px-6 py-4 bg-gray-50 border-t flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-md"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
