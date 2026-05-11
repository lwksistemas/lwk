'use client'

import { useState, useEffect } from 'react'
import { FileText, Plus, X, AlertCircle, Store } from 'lucide-react'
import apiClient from '@/lib/api-client'

interface ModalEmitirNFSeManualProps {
  onClose: () => void
  onSuccess: () => void
}

interface LojaOption {
  id: number
  nome: string
  slug: string
  cpf_cnpj: string
  email: string
  razao_social: string
}

const INITIAL_FORM = {
  loja_id: null as number | null,
  tomador_cpf_cnpj: '',
  tomador_nome: '',
  tomador_email: '',
  tomador_logradouro: '',
  tomador_numero: '',
  tomador_complemento: '',
  tomador_bairro: '',
  tomador_cidade: '',
  tomador_uf: '',
  tomador_cep: '',
  servico_descricao: '',
  valor_servicos: '',
  enviar_email: true,
  codigo_cnae: '',
  codigo_servico: '',
}

const inputClass = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"

export function ModalEmitirNFSeManual({ onClose, onSuccess }: ModalEmitirNFSeManualProps) {
  const [step, setStep] = useState<'escolha' | 'loja' | 'manual'>('escolha')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [lojas, setLojas] = useState<LojaOption[]>([])
  const [loadingLojas, setLoadingLojas] = useState(false)
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [selectedLojaId, setSelectedLojaId] = useState('')

  useEffect(() => {
    if (step === 'loja') {
      carregarLojas()
    }
  }, [step])

  const carregarLojas = async () => {
    try {
      setLoadingLojas(true)
      const { data } = await apiClient.get('/superadmin/nfse-emitidas/lojas/')
      setLojas(data.lojas || [])
    } catch (err) {
      console.error('Erro ao carregar lojas:', err)
    } finally {
      setLoadingLojas(false)
    }
  }

  const handleLojaChange = (lojaId: string) => {
    setSelectedLojaId(lojaId)
    const loja = lojas.find((l) => String(l.id) === lojaId)
    if (loja) {
      setFormData({
        ...formData,
        loja_id: loja.id,
        tomador_cpf_cnpj: loja.cpf_cnpj,
        tomador_nome: loja.razao_social || loja.nome,
        tomador_email: loja.email,
      })
    }
  }

  const handleFieldChange = (field: string, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = step === 'loja' && formData.loja_id
        ? {
            loja_id: formData.loja_id,
            servico_descricao: formData.servico_descricao,
            valor_servicos: formData.valor_servicos,
            enviar_email: formData.enviar_email,
            codigo_cnae: formData.codigo_cnae || undefined,
            codigo_servico: formData.codigo_servico || undefined,
          }
        : {
            tomador_cpf_cnpj: formData.tomador_cpf_cnpj,
            tomador_nome: formData.tomador_nome,
            tomador_email: formData.tomador_email,
            tomador_logradouro: formData.tomador_logradouro,
            tomador_numero: formData.tomador_numero,
            tomador_complemento: formData.tomador_complemento,
            tomador_bairro: formData.tomador_bairro,
            tomador_cidade: formData.tomador_cidade,
            tomador_uf: formData.tomador_uf,
            tomador_cep: formData.tomador_cep,
            servico_descricao: formData.servico_descricao,
            valor_servicos: formData.valor_servicos,
            enviar_email: formData.enviar_email,
            codigo_cnae: formData.codigo_cnae || undefined,
            codigo_servico: formData.codigo_servico || undefined,
          }

      const { data } = await apiClient.post('/superadmin/nfse-emitidas/emitir-manual/', payload)
      if (data.success) {
        onSuccess()
      } else {
        setError(data.error || 'Erro ao emitir NFS-e')
      }
    } catch (err: any) {
      console.error('Erro ao emitir NFS-e:', err)
      setError(err.response?.data?.error || 'Erro ao emitir NFS-e')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-[#16325c] rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Emitir NFS-e Manual</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
              <X size={24} />
            </button>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
              <AlertCircle size={20} className="text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
              <span className="text-sm text-red-800 dark:text-red-200">{error}</span>
            </div>
          )}

          {/* Step: Escolha */}
          {step === 'escolha' && (
            <div className="space-y-4">
              <p className="text-gray-600 dark:text-gray-400 mb-6">Como deseja preencher os dados do cliente?</p>
              <button
                onClick={() => setStep('loja')}
                className="w-full p-6 border-2 border-gray-200 dark:border-gray-600 rounded-lg hover:border-[#0176d3] hover:bg-[#e3f3ff] dark:hover:bg-[#0176d3]/10 transition-all text-left"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-[#0176d3]/10 rounded-lg">
                    <Store size={24} className="text-[#0176d3]" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Selecionar Loja</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Escolha uma loja cadastrada no sistema. Os dados do tomador serão preenchidos automaticamente.
                    </p>
                  </div>
                </div>
              </button>
              <button
                onClick={() => setStep('manual')}
                className="w-full p-6 border-2 border-gray-200 dark:border-gray-600 rounded-lg hover:border-[#0176d3] hover:bg-[#e3f3ff] dark:hover:bg-[#0176d3]/10 transition-all text-left"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-[#0176d3]/10 rounded-lg">
                    <Plus size={24} className="text-[#0176d3]" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Preencher Manualmente</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Digite os dados do tomador manualmente (CPF/CNPJ, nome, endereço).
                    </p>
                  </div>
                </div>
              </button>
              <div className="flex justify-end pt-4">
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}

          {/* Step: Selecionar Loja */}
          {step === 'loja' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Loja *
                </label>
                {loadingLojas ? (
                  <div className="text-center py-4">
                    <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-[#0176d3]" />
                  </div>
                ) : (
                  <select
                    value={selectedLojaId}
                    onChange={(e) => handleLojaChange(e.target.value)}
                    required
                    className={inputClass}
                  >
                    <option value="">Selecione uma loja...</option>
                    {lojas.map((loja) => (
                      <option key={loja.id} value={loja.id}>
                        {loja.nome} {loja.cpf_cnpj ? `- ${loja.cpf_cnpj}` : ''}
                      </option>
                    ))}
                  </select>
                )}
                {selectedLojaId && formData.tomador_cpf_cnpj && (
                  <div className="mt-3 p-3 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg text-sm">
                    <p><strong>Tomador:</strong> {formData.tomador_nome}</p>
                    <p><strong>CPF/CNPJ:</strong> {formData.tomador_cpf_cnpj}</p>
                    {formData.tomador_email && <p><strong>Email:</strong> {formData.tomador_email}</p>}
                  </div>
                )}
              </div>

              {/* Dados do Serviço */}
              <ServicoFields formData={formData} onChange={handleFieldChange} />

              {/* Botões */}
              <FormButtons loading={loading} onBack={() => setStep('escolha')} onClose={onClose} />
            </form>
          )}

          {/* Step: Manual */}
          {step === 'manual' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Dados do Tomador */}
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Dados do Cliente</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">CPF/CNPJ *</label>
                    <input
                      type="text"
                      value={formData.tomador_cpf_cnpj}
                      onChange={(e) => handleFieldChange('tomador_cpf_cnpj', e.target.value)}
                      required
                      className={inputClass}
                      placeholder="000.000.000-00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Nome/Razão Social *</label>
                    <input
                      type="text"
                      value={formData.tomador_nome}
                      onChange={(e) => handleFieldChange('tomador_nome', e.target.value)}
                      required
                      className={inputClass}
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Email</label>
                    <input
                      type="email"
                      value={formData.tomador_email}
                      onChange={(e) => handleFieldChange('tomador_email', e.target.value)}
                      className={inputClass}
                    />
                  </div>
                </div>
              </div>

              {/* Endereço */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Endereço</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">CEP</label>
                    <input
                      type="text"
                      value={formData.tomador_cep}
                      onChange={(e) => handleFieldChange('tomador_cep', e.target.value)}
                      className={inputClass}
                      placeholder="00000-000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Logradouro</label>
                    <input
                      type="text"
                      value={formData.tomador_logradouro}
                      onChange={(e) => handleFieldChange('tomador_logradouro', e.target.value)}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Número</label>
                    <input
                      type="text"
                      value={formData.tomador_numero}
                      onChange={(e) => handleFieldChange('tomador_numero', e.target.value)}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Complemento</label>
                    <input
                      type="text"
                      value={formData.tomador_complemento}
                      onChange={(e) => handleFieldChange('tomador_complemento', e.target.value)}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Bairro</label>
                    <input
                      type="text"
                      value={formData.tomador_bairro}
                      onChange={(e) => handleFieldChange('tomador_bairro', e.target.value)}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Cidade</label>
                    <input
                      type="text"
                      value={formData.tomador_cidade}
                      onChange={(e) => handleFieldChange('tomador_cidade', e.target.value)}
                      className={inputClass}
                      placeholder="Ribeirão Preto"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">UF</label>
                    <input
                      type="text"
                      maxLength={2}
                      value={formData.tomador_uf}
                      onChange={(e) => handleFieldChange('tomador_uf', e.target.value.toUpperCase())}
                      className={inputClass}
                      placeholder="SP"
                    />
                  </div>
                </div>
              </div>

              {/* Dados do Serviço */}
              <ServicoFields formData={formData} onChange={handleFieldChange} />

              {/* Botões */}
              <FormButtons loading={loading} onBack={() => setStep('escolha')} onClose={onClose} />
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

/* ── Sub-components ── */

// Atividades comuns para seleção rápida (LWK Sistemas)
const ATIVIDADES_COMUNS = [
  { label: 'Usar configuração padrão', cnae: '', servico: '' },
  { label: '14.01 - Licenciamento/Manutenção de Software (CNAE 6201501)', cnae: '6201501', servico: '1401' },
  { label: '17.06 - Promoção de Vendas e Negócios (CNAE 7319002)', cnae: '7319002', servico: '170602' },
  { label: '14.01 - Manutenção de Computadores (CNAE 9511800)', cnae: '9511800', servico: '140118' },
];

function ServicoFields({ formData, onChange }: { formData: typeof INITIAL_FORM; onChange: (f: string, v: string | boolean) => void }) {
  const handleAtividadeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const idx = parseInt(e.target.value);
    if (idx >= 0 && idx < ATIVIDADES_COMUNS.length) {
      const atividade = ATIVIDADES_COMUNS[idx];
      onChange('codigo_cnae', atividade.cnae);
      onChange('codigo_servico', atividade.servico);
    }
  };

  const selectedIdx = ATIVIDADES_COMUNS.findIndex(
    (a) => a.cnae === ((formData as any).codigo_cnae || '') && a.servico === ((formData as any).codigo_servico || '')
  );

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Dados do Serviço</h3>
      <div className="space-y-4">
        {/* Seletor de Atividade/CNAE */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Atividade / CNAE
          </label>
          <select
            value={selectedIdx >= 0 ? selectedIdx : 0}
            onChange={handleAtividadeChange}
            className={inputClass}
          >
            {ATIVIDADES_COMUNS.map((a, i) => (
              <option key={i} value={i}>{a.label}</option>
            ))}
          </select>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Selecione a atividade compatível com o serviço prestado
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Descrição do Serviço *
          </label>
          <textarea
            value={formData.servico_descricao}
            onChange={(e) => onChange('servico_descricao', e.target.value)}
            required
            rows={3}
            className={inputClass}
            placeholder="Ex: Licenciamento de uso de software SaaS - Plano Mensal"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Valor dos Serviços (R$) *
          </label>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={formData.valor_servicos}
            onChange={(e) => onChange('valor_servicos', e.target.value)}
            required
            className={inputClass}
            placeholder="0.00"
          />
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={formData.enviar_email}
            onChange={(e) => onChange('enviar_email', e.target.checked)}
            className="w-4 h-4"
          />
          <span className="text-sm text-gray-700 dark:text-gray-300">
            Enviar NFS-e por email para o cliente
          </span>
        </label>
      </div>
    </div>
  )
}

function FormButtons({ loading, onBack, onClose }: { loading: boolean; onBack: () => void; onClose: () => void }) {
  return (
    <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
      <button
        type="button"
        onClick={onBack}
        className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
      >
        Voltar
      </button>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Emitindo...' : 'Emitir NFS-e'}
        </button>
      </div>
    </div>
  )
}
