import { NFSE_CARD_CLASS, NFSE_INPUT_CLASS, type NFSeFormData } from "@/components/clinica-beleza/nfse/nfse-form-types";

interface Props {
  formData: NFSeFormData;
  onFieldChange: <K extends keyof NFSeFormData>(key: K, value: NFSeFormData[K]) => void;
}

export function NFSeGeralSection({ formData, onFieldChange }: Props) {
  const isIssnet = formData.provedor_nf === "issnet";

  return (
    <div className={NFSE_CARD_CLASS}>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Configurações Gerais</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Código do Serviço Municipal
          </label>
          <input
            type="text"
            value={formData.codigo_servico_municipal}
            onChange={(e) => onFieldChange("codigo_servico_municipal", e.target.value)}
            placeholder="Ex: 0601"
            className={NFSE_INPUT_CLASS}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Alíquota ISS (%)</label>
          <input
            type="text"
            value={formData.aliquota_iss}
            onChange={(e) => onFieldChange("aliquota_iss", e.target.value)}
            placeholder="2.00"
            className={NFSE_INPUT_CLASS}
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Descrição Padrão do Serviço
          </label>
          <textarea
            value={formData.descricao_servico_padrao}
            onChange={(e) => onFieldChange("descricao_servico_padrao", e.target.value)}
            rows={2}
            className={NFSE_INPUT_CLASS}
          />
        </div>

        {isIssnet && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Inscrição Municipal
              </label>
              <input
                type="text"
                value={formData.inscricao_municipal}
                onChange={(e) => onFieldChange("inscricao_municipal", e.target.value)}
                placeholder="Ex.: 20130440"
                className={NFSE_INPUT_CLASS}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Código CNAE (opcional)
              </label>
              <input
                type="text"
                value={formData.codigo_cnae}
                onChange={(e) => onFieldChange("codigo_cnae", e.target.value)}
                className={NFSE_INPUT_CLASS}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Item Lista Serviço (opcional)
              </label>
              <input
                type="text"
                value={formData.item_lista_servico}
                onChange={(e) => onFieldChange("item_lista_servico", e.target.value)}
                placeholder="Ex.: 06.01"
                className={NFSE_INPUT_CLASS}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Série do RPS</label>
              <input
                type="text"
                value={formData.issnet_serie_rps}
                onChange={(e) => onFieldChange("issnet_serie_rps", e.target.value)}
                placeholder="Ex.: E ou NFSE"
                className={NFSE_INPUT_CLASS}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Último RPS emitido
              </label>
              <input
                type="number"
                value={formData.issnet_ultimo_rps_conhecido}
                onChange={(e) => onFieldChange("issnet_ultimo_rps_conhecido", e.target.value)}
                className={NFSE_INPUT_CLASS}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Regime Especial Tributação
              </label>
              <select
                value={formData.regime_especial_tributacao}
                onChange={(e) => onFieldChange("regime_especial_tributacao", e.target.value)}
                className={NFSE_INPUT_CLASS}
              >
                <option value="0">Nenhum</option>
                <option value="1">Microempresa Municipal</option>
                <option value="2">Estimativa</option>
                <option value="3">Sociedade de Profissionais</option>
                <option value="4">Cooperativa</option>
                <option value="5">MEI - Simples Nacional</option>
                <option value="6">ME/EPP - Simples Nacional</option>
              </select>
            </div>
          </>
        )}

        <div className="md:col-span-2 space-y-3 pt-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.optante_simples_nacional}
              onChange={(e) => onFieldChange("optante_simples_nacional", e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Optante pelo Simples Nacional</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.incentivador_cultural}
              onChange={(e) => onFieldChange("incentivador_cultural", e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Incentivador Cultural</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.emitir_nf_automaticamente}
              onChange={(e) => onFieldChange("emitir_nf_automaticamente", e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              Emitir NF automaticamente ao confirmar pagamento
            </span>
          </label>
        </div>
      </div>
    </div>
  );
}
