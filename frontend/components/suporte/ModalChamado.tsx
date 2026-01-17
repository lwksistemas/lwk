'use client'

import { useState } from 'react'
import { apiClient } from '@/lib/api-client'

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
  
  const [formData, setFormData] = useState({
    tipo: 'duvida',
    titulo: '',
    descricao: '',
    prioridade: 'media'
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErro('')

    try {
      // Adicionar informações da loja se disponíveis
      const dadosChamado = {
        ...formData,
        ...(lojaSlug && { loja_slug: lojaSlug }),
        ...(lojaNome && { loja_nome: lojaNome })
      }
      
      await apiClient.post('/suporte/criar-chamado/', dadosChamado)
      
      setSucesso(true)
      
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
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                🆘 Abrir Chamado de Suporte
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Descreva sua dúvida, problema ou solicitação de treinamento
              </p>
            </div>
            <button
              onClick={onFechar}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Mensagem de Sucesso */}
          {sucesso && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <p className="text-green-800 font-medium">
                  ✅ Chamado criado com sucesso! Nossa equipe entrará em contato em breve.
                </p>
              </div>
            </div>
          )}

          {/* Mensagem de Erro */}
          {erro && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800">{erro}</p>
            </div>
          )}

          {/* Formulário */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Tipo de Chamado */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Chamado *
              </label>
              <select
                value={formData.tipo}
                onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Prioridade
              </label>
              <select
                value={formData.prioridade}
                onChange={(e) => setFormData({ ...formData, prioridade: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="baixa">🟢 Baixa</option>
                <option value="media">🟡 Média</option>
                <option value="alta">🟠 Alta</option>
                <option value="urgente">🔴 Urgente</option>
              </select>
            </div>

            {/* Título */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Título *
              </label>
              <input
                type="text"
                value={formData.titulo}
                onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
                placeholder="Ex: Dúvida sobre cadastro de produtos"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
                maxLength={200}
              />
            </div>

            {/* Descrição */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Descrição *
              </label>
              <textarea
                value={formData.descricao}
                onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                placeholder="Descreva detalhadamente sua dúvida, problema ou solicitação..."
                rows={6}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Quanto mais detalhes você fornecer, mais rápido poderemos ajudar!
              </p>
            </div>

            {/* Botões */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onFechar}
                className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
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
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="font-medium text-blue-900 mb-2">ℹ️ Tempo de Resposta</h3>
            <ul className="text-sm text-blue-800 space-y-1">
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
