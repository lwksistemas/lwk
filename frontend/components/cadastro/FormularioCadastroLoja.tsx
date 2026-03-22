'use client';

import { formatCurrency } from '@/lib/financeiro-helpers';

interface FormularioCadastroLojaProps {
  lojaForm: any;
  onSubmit: (e: React.FormEvent) => void;
  loading: boolean;
  mostrarSenha?: boolean;
}

export function FormularioCadastroLoja({ 
  lojaForm, 
  onSubmit, 
  loading,
  mostrarSenha = false 
}: FormularioCadastroLojaProps) {
  const { 
    formData, 
    setFormData, 
    tipos, 
    planos,
    buscarCepLoading,
    buscarCnpjLoading,
    loadPlanosPorTipo,
    getSuggestedSlug,
    formatCpfCnpj,
    buscarCep,
    buscarCnpj,
    gerarSenhaProvisoria,
  } = lojaForm;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    if (name === 'cep') {
      const digits = value.replace(/\D/g, '').slice(0, 8);
      const formatted = digits.length > 5 ? `${digits.slice(0, 5)}-${digits.slice(5)}` : digits;
      setFormData((prev: any) => ({ ...prev, cep: formatted }));
      return;
    }
    
    setFormData((prev: any) => ({ ...prev, [name]: value }));
    
    if (name === 'nome') {
      setFormData((prev: any) => ({ ...prev, slug: getSuggestedSlug(value, prev.cpf_cnpj) }));
    }
    
    if (name === 'tipo_loja' && value) {
      loadPlanosPorTipo(value);
      setFormData((prev: any) => ({ ...prev, plano: '' }));
    }
  };

  const handleCpfCnpjChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCpfCnpj(e.target.value);
    setFormData((prev: any) => ({ 
      ...prev, 
      cpf_cnpj: formatted, 
      slug: getSuggestedSlug(prev.nome, formatted) 
    }));
  };

  const planoSelecionado = planos.find((p: any) => p.id === parseInt(formData.plano));
  const valorAssinatura = planoSelecionado 
    ? (formData.tipo_assinatura === 'anual' 
        ? planoSelecionado.preco_anual 
        : planoSelecionado.preco_mensal)
    : 0;

  return (
    <form onSubmit={onSubmit} className="p-8 space-y-8">
      {/* Seção 1: Informações Básicas */}
      <div className="border-b border-gray-200 pb-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-700">1. Informações Básicas</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome da Empresa *
            </label>
            <input
              type="text"
              name="nome"
              value={formData.nome}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ex: Minha Empresa LTDA"
            />
          </div>
          
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                CPF ou CNPJ *
              </label>
              <input
                type="text"
                name="cpf_cnpj"
                value={formData.cpf_cnpj}
                onChange={handleCpfCnpjChange}
                required
                maxLength={18}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="000.000.000-00"
              />
            </div>
            <button
              type="button"
              onClick={buscarCnpj}
              disabled={buscarCnpjLoading || formData.cpf_cnpj.replace(/\D/g, '').length !== 14}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {buscarCnpjLoading ? '...' : 'Buscar'}
            </button>
          </div>
        </div>
      </div>

      {/* Seção 2: Endereço */}
      <div className="border-b border-gray-200 pb-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-700">2. Endereço</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                CEP
              </label>
              <input
                type="text"
                name="cep"
                value={formData.cep}
                onChange={handleChange}
                maxLength={9}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="00000-000"
              />
            </div>
            <button
              type="button"
              onClick={buscarCep}
              disabled={buscarCepLoading || formData.cep.replace(/\D/g, '').length !== 8}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 whitespace-nowrap"
            >
              {buscarCepLoading ? '...' : 'Buscar'}
            </button>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Logradouro</label>
            <input
              type="text"
              name="logradouro"
              value={formData.logradouro}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Número</label>
            <input
              type="text"
              name="numero"
              value={formData.numero}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Bairro</label>
            <input
              type="text"
              name="bairro"
              value={formData.bairro}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cidade</label>
            <input
              type="text"
              name="cidade"
              value={formData.cidade}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">UF</label>
            <input
              type="text"
              name="uf"
              value={formData.uf}
              onChange={handleChange}
              maxLength={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 uppercase"
            />
          </div>
        </div>
      </div>

      {/* Seção 3: Tipo de App */}
      <div className="border-b border-gray-200 pb-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-700">3. Tipo de Sistema</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {tipos.map((tipo: any) => (
            <label
              key={tipo.id}
              className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                formData.tipo_loja === tipo.id.toString()
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              <input
                type="radio"
                name="tipo_loja"
                value={tipo.id}
                checked={formData.tipo_loja === tipo.id.toString()}
                onChange={handleChange}
                className="sr-only"
                required
              />
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-900">{tipo.nome}</span>
                <div
                  className="w-6 h-6 rounded-full"
                  style={{ backgroundColor: tipo.cor_primaria }}
                />
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Seção 4: Plano */}
      <div className="border-b border-gray-200 pb-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-700">4. Escolha seu Plano</h3>
        {!formData.tipo_loja ? (
          <div className="text-center py-8 text-gray-500">
            Selecione um tipo de sistema primeiro
          </div>
        ) : planos.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            Nenhum plano disponível
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {planos.map((plano: any) => (
              <label
                key={plano.id}
                className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                  formData.plano === plano.id.toString()
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                }`}
              >
                <input
                  type="radio"
                  name="plano"
                  value={plano.id}
                  checked={formData.plano === plano.id.toString()}
                  onChange={handleChange}
                  className="sr-only"
                  required
                />
                <div className="text-center">
                  <h4 className="font-bold text-lg mb-2">{plano.nome}</h4>
                  <p className="text-2xl font-bold text-blue-600 mb-2">
                    {formatCurrency(plano.preco_mensal)}
                  </p>
                  <p className="text-sm text-gray-600">por mês</p>
                  {plano.preco_anual && (
                    <p className="text-xs text-gray-500 mt-1">
                      ou {formatCurrency(plano.preco_anual)}/ano
                    </p>
                  )}
                </div>
              </label>
            ))}
          </div>
        )}
        
        {formData.plano && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Assinatura *
              </label>
              <select
                name="tipo_assinatura"
                value={formData.tipo_assinatura}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="mensal">Mensal</option>
                <option value="anual">Anual</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Dia de Vencimento *
              </label>
              <select
                name="dia_vencimento"
                value={formData.dia_vencimento}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                {Array.from({ length: 28 }, (_, i) => i + 1).map(dia => (
                  <option key={dia} value={dia}>Dia {dia}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {valorAssinatura > 0 && (
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm font-medium text-blue-900">
              Valor da assinatura: <span className="text-xl">{formatCurrency(valorAssinatura)}</span>
              {formData.tipo_assinatura === 'anual' && ' (pagamento anual)'}
            </p>
            <p className="text-xs text-blue-700 mt-1">
              Vencimento todo dia {formData.dia_vencimento} do mês
            </p>
          </div>
        )}
      </div>

      {/* Seção 5: Dados do Administrador */}
      <div className="pb-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-700">5. Dados do Administrador</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome Completo *
            </label>
            <input
              type="text"
              name="owner_full_name"
              value={formData.owner_full_name}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ex: João Silva"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome de Usuário *
            </label>
            <input
              type="text"
              name="owner_username"
              value={formData.owner_username}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ex: joao.silva"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              E-mail *
            </label>
            <input
              type="email"
              name="owner_email"
              value={formData.owner_email}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="email@empresa.com"
            />
            <p className="text-xs text-gray-500 mt-1">
              A senha será enviada para este email após confirmação do pagamento
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Telefone
            </label>
            <input
              type="tel"
              name="owner_telefone"
              value={formData.owner_telefone}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="(00) 00000-0000"
            />
          </div>

          {mostrarSenha && formData.owner_password && (
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Senha Provisória *
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={formData.owner_password}
                  readOnly
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 font-mono"
                />
                <button
                  type="button"
                  onClick={gerarSenhaProvisoria}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  🔄 Gerar Nova
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Botão de Submit */}
      <div className="flex justify-end gap-4">
        <button
          type="submit"
          disabled={loading}
          className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold text-lg"
        >
          {loading ? 'Criando cadastro...' : 'Finalizar Cadastro'}
        </button>
      </div>
    </form>
  );
}
