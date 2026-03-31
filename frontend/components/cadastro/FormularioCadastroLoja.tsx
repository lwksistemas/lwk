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
    <form onSubmit={onSubmit} className="space-y-6 p-4 sm:space-y-8 sm:p-6 md:p-8">
      {/* Seção 1: Informações Básicas */}
      <div className="border-b border-gray-200 pb-6 dark:border-slate-700">
        <h3 className="mb-4 text-lg font-semibold text-gray-800 dark:text-slate-200">
          1. Informações Básicas
        </h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Nome da Empresa *
            </label>
            <input
              type="text"
              name="nome"
              value={formData.nome}
              onChange={handleChange}
              required
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              placeholder="Ex: Minha Empresa LTDA"
            />
          </div>
          
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:gap-2">
            <div className="min-w-0 flex-1">
              <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                CPF ou CNPJ *
              </label>
              <input
                type="text"
                name="cpf_cnpj"
                value={formData.cpf_cnpj}
                onChange={handleCpfCnpjChange}
                required
                maxLength={18}
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                placeholder="000.000.000-00"
              />
            </div>
            <button
              type="button"
              onClick={buscarCnpj}
              disabled={buscarCnpjLoading || formData.cpf_cnpj.replace(/\D/g, '').length !== 14}
              className="h-11 shrink-0 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 sm:h-auto sm:min-h-[42px] sm:self-end"
            >
              {buscarCnpjLoading ? '...' : 'Buscar'}
            </button>
          </div>

          <div className="md:col-span-2">
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Atalho (URL Amigável) – opcional
            </label>
            <input
              type="text"
              name="atalho"
              value={formData.atalho || ''}
              onChange={handleChange}
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              placeholder="minha-empresa (deixe vazio para gerar automaticamente)"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              URL: /{formData.atalho || '…'} — gerado automaticamente se vazio. 
              Ex.: "felix-representacoes" → /felix-representacoes
            </p>
          </div>
        </div>
      </div>

      {/* Seção 2: Endereço */}
      <div className="border-b border-gray-200 pb-6 dark:border-slate-700">
        <h3 className="mb-4 text-lg font-semibold text-gray-800 dark:text-slate-200">2. Endereço</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="col-span-full flex flex-col gap-3 sm:flex-row sm:items-end sm:gap-2">
            <div className="min-w-0 flex-1">
              <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                CEP
              </label>
              <input
                type="text"
                name="cep"
                value={formData.cep}
                onChange={handleChange}
                maxLength={9}
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                placeholder="00000-000"
              />
            </div>
            <button
              type="button"
              onClick={buscarCep}
              disabled={buscarCepLoading || formData.cep.replace(/\D/g, '').length !== 8}
              className="h-11 shrink-0 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 sm:h-auto sm:min-h-[42px] sm:self-end"
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
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Número</label>
            <input
              type="text"
              name="numero"
              value={formData.numero}
              onChange={handleChange}
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Bairro</label>
            <input
              type="text"
              name="bairro"
              value={formData.bairro}
              onChange={handleChange}
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cidade</label>
            <input
              type="text"
              name="cidade"
              value={formData.cidade}
              onChange={handleChange}
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
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
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base uppercase text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
            />
          </div>
        </div>
      </div>

      {/* Seção 3: Tipo de App */}
      <div className="border-b border-gray-200 pb-6 dark:border-slate-700">
        <h3 className="mb-4 text-lg font-semibold text-gray-800 dark:text-slate-200">3. Tipo de Sistema</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
      <div className="border-b border-gray-200 pb-6 dark:border-slate-700">
        <h3 className="mb-4 text-lg font-semibold text-gray-800 dark:text-slate-200">4. Escolha seu Plano</h3>
        {!formData.tipo_loja ? (
          <div className="text-center py-8 text-gray-500">
            Selecione um tipo de sistema primeiro
          </div>
        ) : planos.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            Nenhum plano disponível
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
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
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
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
        <h3 className="mb-4 text-lg font-semibold text-gray-800 dark:text-slate-200">
          5. Dados do Administrador
        </h3>
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
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
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
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
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
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
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
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-base text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
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
      <div className="space-y-4">
        {/* Aviso sobre senha */}
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
          <div className="flex items-start gap-3">
            <span className="text-2xl">ℹ️</span>
            <div className="flex-1">
              <p className="text-sm font-semibold text-blue-900 mb-1">
                Como funciona o acesso ao sistema?
              </p>
              <p className="text-xs text-blue-800">
                Após finalizar o cadastro, você receberá um boleto de pagamento. A senha de acesso será <strong>gerada automaticamente</strong> e enviada para o email cadastrado assim que o pagamento for confirmado (1-3 dias úteis para boleto).
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
          <button
            type="submit"
            disabled={loading}
            className="min-h-[48px] w-full rounded-lg bg-blue-600 px-6 py-3 text-base font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto sm:min-w-[200px] sm:px-8 sm:text-lg"
          >
            {loading ? 'Criando cadastro...' : 'Finalizar Cadastro'}
          </button>
        </div>
      </div>
    </form>
  );
}
