'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import { errorLogger } from '@/lib/error-logger'

interface ModalChamadoProps {
  aberto: boolean
  onFechar: () => void
  lojaSlug?: string
  lojaNome?: string
}

export default function ModalChamado({ aberto, onFechar, lojaSlug, lojaNome }: ModalChamadoProps) {
  const [loading, setLoading] = useState(false)
  const [sucesso, setSucesso] = useState(false)
  const [erro, setErro] = useState('')
  const [incluirLogs, setIncluirLogs] = useState(true)
  const [errorStats, setErrorStats] = useState({ total: 0, frontend: 0, api: 0, navegador: 0 })
  
  const [formData, setFormData] = useState({
    tipo: 'duvida',
    titulo: '',
    descricao: '',
    prioridade: 'media'
  })

  // Atualizar estatísticas de erros quando o modal abrir
  useEffect(() => {
    if (aberto) {
      const stats = errorLogger.getStats()
      setErrorStats(stats)
      // Auto-incluir logs se houver erros
      setIncluirLogs(stats.total > 0)
    }
  }, [aberto])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErro('')

    try {
      // Preparar dados do chamado
      let descricaoCompleta = formData.descricao

      // Adicionar logs de erro se solicitado
      if (incluirLogs && errorStats.total > 0) {
        const logsFormatados = errorLogger.getFormattedErrors()
        descricaoCompleta += '\n\n' + '='.repeat(60)
        descricaoCompleta += '\n📋 LOGS DE DIAGNÓSTICO AUTOMÁTICO\n'
        descricaoCompleta += '='.repeat(60)
        descricaoCompleta += logsFormatados
      }

      // Adicionar informações da loja se disponíveis
      const dadosChamado = {
        ...formData,
        descricao: descricaoCompleta,
        ...(lojaSlug && { loja_slug: lojaSlug }),
        ...(lojaNome && { loja_nome: lojaNome })
      }
      
      await apiClient.post('/suporte/criar-chamado/', dadosChamado)
      
      setSucesso(true)
      
      // Limpar logs após envio bem-sucedido
      if (incluirLogs) {
        errorLogger.clearErrors()
      }
      
      // Fechar modal após 2 segundos
      setTimeout(() => {
        onFechar()
        setSucesso(false)
        setFormData({
          tipo: 'duvida',
          titulo: '',
          descricao: '',
          prioridade: 'media'
        })
        setIncluirLogs(true)
      }, 2000)
      
    } catch (error: any) {
      setErro(error.response?.data?.error || 'Erro ao criar chamado')
    } finally {
      setLoading(false)
    }
  }

  if (!aberto) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onFechar}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div className="flex-1">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                🆘 Abrir Chamado de Suporte
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Descreva sua dúvida, problema ou solicitação
              </p>
            </div>
            <button
              onClick={onFechar}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 ml-4 flex-shrink-0"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Mensagem de Sucesso */}
          {sucesso && (
            <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-green-600 dark:text-green-400 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-green-800 dark:text-green-200 font-medium">
                  Chamado criado com sucesso! Nossa equipe entrará em contato em breve.
                </p>
              </div>
            </div>
          )}

          {/* Mensagem de Erro */}
          {erro && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-800 dark:text-red-200">{erro}</p>
            </div>
          )}

          {/* Formulário */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Tipo de Chamado */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Tipo de Chamado *
              </label>
              <select
                value={formData.tipo}
                onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                required
              >
                <option value="duvida">❓ Dúvida</option>
                <option value="treinamento">📚 Treinamento</option>
                <option value="problema">🐛 Problema Técnico</option>
                <option value="sugestao">💡 Sugestão</option>
                <option value="outro">📝 Outro</option>
              </select>
            </div>

            {/* Prioridade */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Prioridade
              </label>
              <select
                value={formData.prioridade}
                onChange={(e) => setFormData({ ...formData, prioridade: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                <option value="baixa">🟢 Baixa</option>
                <option value="media">🟡 Média</option>
                <option value="alta">🟠 Alta</option>
                <option value="urgente">🔴 Urgente</option>
              </select>
            </div>

            {/* Título */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Título *
              </label>
              <input
                type="text"
                value={formData.titulo}
                onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
                placeholder="Ex: Dúvida sobre cadastro de produtos"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                required
                maxLength={200}
              />
            </div>

            {/* Descrição */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Descrição *
              </label>
              <textarea
                value={formData.descricao}
                onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                placeholder="Descreva detalhadamente sua dúvida, problema ou solicitação..."
                rows={5}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
                required
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Quanto mais detalhes você fornecer, mais rápido poderemos ajudar!
              </p>
            </div>

            {/* Incluir Logs de Diagnóstico */}
            {errorStats.total > 0 && (
              <div className="p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                <div className="flex items-start gap-2">
                  <input
                    type="checkbox"
                    id="incluirLogs"
                    checked={incluirLogs}
                    onChange={(e) => setIncluirLogs(e.target.checked)}
                    className="mt-0.5 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <label htmlFor="incluirLogs" className="text-sm font-medium text-amber-900 dark:text-amber-200 cursor-pointer">
                      📊 Incluir logs de diagnóstico automático
                    </label>
                    <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                      Detectamos {errorStats.total} erro(s) recente(s):
                      {errorStats.frontend > 0 && <span className="ml-1">🔴 {errorStats.frontend} frontend</span>}
                      {errorStats.api > 0 && <span className="ml-1">🟢 {errorStats.api} API</span>}
                      {errorStats.navegador > 0 && <span className="ml-1">🟡 {errorStats.navegador} navegador</span>}
                    </p>
                    <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                      ✅ Recomendado: Isso ajuda nossa equipe a resolver seu problema mais rápido
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Botões */}
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={onFechar}
                className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm font-medium"
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Enviando...
                  </span>
                ) : (
                  '📨 Enviar Chamado'
                )}
              </button>
            </div>
          </form>

          {/* Informações Adicionais */}
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <h3 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-2">ℹ️ Tempo de Resposta</h3>
            <ul className="text-xs text-blue-800 dark:text-blue-300 space-y-1">
              <li>• <strong>Urgente:</strong> Até 2 horas</li>
              <li>• <strong>Alta:</strong> Até 4 horas</li>
              <li>• <strong>Média:</strong> Até 24 horas</li>
              <li>• <strong>Baixa:</strong> Até 48 horas</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
