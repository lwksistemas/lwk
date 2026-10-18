'use client';

import type { ChangeEvent, Dispatch, SetStateAction } from 'react';
import Link from 'next/link';
import { Loader2 } from 'lucide-react';
import { NFSE_EMISSAO_OPCOES, type EmissaoOpcao } from '@/lib/nfse-emissao-opcoes';
import { CamposServicoBasicos, CertificadoFields } from './nfse-emissao-campos';

const INPUT =
  'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white';
const CARD =
  'bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6';

type FormData = {
  provedor_nf: string;
  issnet_usuario: string;
  issnet_senha: string;
  issnet_senha_certificado: string;
  codigo_servico_municipal: string;
  descricao_servico_padrao: string;
  aliquota_iss: string;
  inscricao_municipal: string;
  codigo_cnae: string;
  optante_simples_nacional: boolean;
  regime_especial_tributacao: string;
  incentivador_cultural: boolean;
  item_lista_servico: string;
  codigo_nbs: string;
  issnet_serie_rps: string;
  issnet_ultimo_rps_conhecido: string;
  issnet_numero_lote: string;
  issnet_ambiente_homologacao: boolean;
  issnet_usar_padrao_nacional: boolean;
  codigo_tributacao_nacional: string;
  codigo_tributacao_municipal: string;
  nacional_codigo_municipio: string;
  indicador_operacao: string;
  cst_ibscbs: string;
  cclass_trib_ibscbs: string;
  p_tot_trib_sn: string;
  emitir_nf_automaticamente: boolean;
};

export function NfseEmissaoSecoes({
  configBase,
  emissaoOpcao,
  selecionarEmissao,
  isAsaas,
  isIssnet,
  isIssnetNacional,
  isNacionalAdn,
  showCertConfig,
  showServicoConfig,
  asaasConfigurada,
  temCertificado,
  senhasSalvas,
  formData,
  setFormData,
  certificadoFile,
  onFileChange,
  onTestarConexao,
  testando,
  testeMensagem,
  onVoltar,
  loading,
}: {
  configBase: string;
  emissaoOpcao: EmissaoOpcao;
  selecionarEmissao: (opcao: EmissaoOpcao) => void;
  isAsaas: boolean;
  isIssnet: boolean;
  isIssnetNacional: boolean;
  isNacionalAdn: boolean;
  showCertConfig: boolean;
  showServicoConfig: boolean;
  asaasConfigurada: boolean;
  temCertificado: boolean;
  senhasSalvas: boolean;
  formData: FormData;
  setFormData: Dispatch<SetStateAction<any>>;
  certificadoFile: File | null;
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onTestarConexao: () => void;
  testando: boolean;
  testeMensagem: { type: 'ok' | 'error'; text: string } | null;
  onVoltar: () => void;
  loading: boolean;
}) {
  const config = {
    asaas_api_key_configured: asaasConfigurada,
    issnet_certificado: temCertificado,
    issnet_senhas_salvas: senhasSalvas,
  };
  const handleFileChange = onFileChange;
  const testarConexaoIssnet = onTestarConexao;
  const issnetTestLoading = testando;
  const issnetTestMessage = testeMensagem;
  const router = { back: onVoltar };

  return (
    <>
        <div className={CARD}>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
            Como deseja emitir?
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Selecione uma das opções. Em seguida configure o emissor escolhido.
          </p>

          <div className="space-y-3">
            {NFSE_EMISSAO_OPCOES.map((op) => {
              const selected = emissaoOpcao === op.key;
              return (
                <label
                  key={op.key}
                  className={`flex items-start gap-3 p-4 rounded-lg border-2 transition-all cursor-pointer ${
                    selected
                      ? 'border-[#0176d3] bg-[#e3f3ff] dark:bg-[#0176d3]/10'
                      : 'border-gray-200 dark:border-[#0d1f3c] hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <input
                    type="radio"
                    name="emissao_opcao"
                    value={op.key}
                    checked={selected}
                    onChange={() => selecionarEmissao(op.key)}
                    className="mt-1"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-semibold text-[#0176d3] tabular-nums">
                        {op.numero}.
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">{op.titulo}</span>
                      {op.badge ? (
                        <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                          {op.badge}
                        </span>
                      ) : null}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{op.descricao}</p>
                  </div>
                </label>
              );
            })}
          </div>
        </div>

        {/* —— 1. Asaas —— */}
        {isAsaas && (
          <div className={CARD}>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Configurações — Asaas
            </h2>
            <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
              Configure a API Key da loja em{' '}
              <Link href={`${configBase}/asaas`} className="text-[#0176d3] underline font-medium">
                Configurações → Asaas (banco)
              </Link>
              {config?.asaas_api_key_configured ? (
                <span className="text-green-700 dark:text-green-300"> — chave já cadastrada.</span>
              ) : (
                <span className="text-amber-700 dark:text-amber-300"> — chave ainda não configurada.</span>
              )}
            </p>
            <CamposServicoBasicos formData={formData} setFormData={setFormData} inputClass={INPUT} />
          </div>
        )}

        {/* —— 2 e 3. ISSNet —— */}
        {isIssnet && (
          <>
            <div className={CARD}>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Configurações — ISSNet Padrão Nacional
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                Endpoint: wsnfsenacional/ribeiraopreto (DPS). Homologação: wsnfsenacional/homologacao.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Usuário ISSNet *
                  </label>
                  <input
                    type="text"
                    value={formData.issnet_usuario}
                    onChange={(e) => setFormData({ ...formData, issnet_usuario: e.target.value })}
                    className={INPUT}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Senha ISSNet
                  </label>
                  <input
                    type="password"
                    value={formData.issnet_senha}
                    onChange={(e) => setFormData({ ...formData, issnet_senha: e.target.value })}
                    placeholder="Digite para alterar"
                    className={INPUT}
                  />
                </div>
              </div>

              <CertificadoFields
                certificadoFile={certificadoFile}
                temCertificadoSalvo={Boolean(config?.issnet_certificado)}
                senha={formData.issnet_senha_certificado}
                onSenha={(v) => setFormData({ ...formData, issnet_senha_certificado: v })}
                onFileChange={handleFileChange}
                inputClass={INPUT}
              />

              <label className="flex items-center gap-2 cursor-pointer mt-4">
                <input
                  type="checkbox"
                  checked={formData.issnet_ambiente_homologacao}
                  onChange={(e) =>
                    setFormData({ ...formData, issnet_ambiente_homologacao: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Homologação / teste
                  {isIssnetNacional ? ' (webservice Nacional)' : ' (ISSNet)'}
                </span>
              </label>

              <div className="mt-4 flex flex-col sm:flex-row sm:items-center gap-3">
                <button
                  type="button"
                  onClick={() => void testarConexaoIssnet()}
                  disabled={
                    issnetTestLoading ||
                    !formData.issnet_usuario.trim() ||
                    (!certificadoFile && !config?.issnet_certificado) ||
                    (!formData.issnet_senha &&
                      !formData.issnet_senha_certificado &&
                      !config?.issnet_senhas_salvas)
                  }
                  className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-[#0176d3] text-[#0176d3] text-sm font-medium disabled:opacity-50"
                >
                  {issnetTestLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Testando…
                    </>
                  ) : (
                    'Testar conexão ISSNet'
                  )}
                </button>
                {issnetTestMessage && (
                  <span
                    className={`text-sm ${
                      issnetTestMessage.type === 'ok'
                        ? 'text-green-700 dark:text-green-300'
                        : 'text-red-700 dark:text-red-300'
                    }`}
                  >
                    {issnetTestMessage.text}
                  </span>
                )}
              </div>
            </div>

            <div className={CARD}>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Dados do prestador e da nota
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Inscrição municipal *
                  </label>
                  <input
                    type="text"
                    value={formData.inscricao_municipal}
                    onChange={(e) => setFormData({ ...formData, inscricao_municipal: e.target.value })}
                    className={INPUT}
                    placeholder="Ex.: 20130440"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Código CNAE
                  </label>
                  <input
                    type="text"
                    value={formData.codigo_cnae}
                    onChange={(e) => setFormData({ ...formData, codigo_cnae: e.target.value })}
                    className={INPUT}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Item da lista de serviços
                  </label>
                  <input
                    type="text"
                    value={formData.item_lista_servico}
                    onChange={(e) => setFormData({ ...formData, item_lista_servico: e.target.value })}
                    placeholder="Ex.: 14.01"
                    className={INPUT}
                  />
                </div>
                {isIssnetNacional && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        cTribNac (tributação nacional)
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        maxLength={6}
                        value={formData.codigo_tributacao_nacional}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            codigo_tributacao_nacional: e.target.value.replace(/\D/g, '').slice(0, 6),
                          })
                        }
                        placeholder="140100"
                        className={INPUT}
                      />
                      <p className="text-[11px] text-gray-500 mt-1">6 dígitos. Vazio → deriva do item (14.01 → 140100).</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        cTribMun (tributação municipal)
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        maxLength={6}
                        value={formData.codigo_tributacao_municipal}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            codigo_tributacao_municipal: e.target.value.replace(/\D/g, '').slice(0, 6),
                          })
                        }
                        placeholder="140118"
                        className={INPUT}
                      />
                      <p className="text-[11px] text-gray-500 mt-1">
                        Código cadastrado no ISSNet p/ este contribuinte (NÃO é o item da lista). Confirme
                        emitindo manualmente no portal e inspecionando o XML. Vazio → usa o cTribNac.
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Código NBS
                      </label>
                      <input
                        type="text"
                        value={formData.codigo_nbs}
                        onChange={(e) => setFormData({ ...formData, codigo_nbs: e.target.value })}
                        className={INPUT}
                      />
                    </div>
                  </>
                )}
                {isIssnetNacional && (
                  <div className="md:col-span-2 mt-2 pt-4 border-t border-gray-200 dark:border-[#0d1f3c]">
                    <p className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                      IBS/CBS (Reforma Tributária)
                    </p>
                    <p className="text-[11px] text-gray-500 dark:text-gray-400 mb-3">
                      Campos opcionais do bloco IBS/CBS da DPS. Deixe em branco para usar os valores
                      padrão (CST 000, cClassTrib 000001).
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Indicador da Operação
                        </label>
                        <input
                          type="text"
                          inputMode="numeric"
                          maxLength={2}
                          value={formData.indicador_operacao}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              indicador_operacao: e.target.value.replace(/\D/g, '').slice(0, 2),
                            })
                          }
                          className={INPUT}
                        />
                        <p className="text-[11px] text-gray-500 mt-1">Vazio: deriva automaticamente do cTribNac.</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Situação Tributária (CST)
                        </label>
                        <input
                          type="text"
                          inputMode="numeric"
                          maxLength={3}
                          value={formData.cst_ibscbs}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              cst_ibscbs: e.target.value.replace(/\D/g, '').slice(0, 3),
                            })
                          }
                          placeholder="000"
                          className={INPUT}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Classificação Tributária (cClassTrib)
                        </label>
                        <input
                          type="text"
                          inputMode="numeric"
                          maxLength={6}
                          value={formData.cclass_trib_ibscbs}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              cclass_trib_ibscbs: e.target.value.replace(/\D/g, '').slice(0, 6),
                            })
                          }
                          placeholder="000001"
                          className={INPUT}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          % Total de Tributos (Simples Nacional)
                        </label>
                        <input
                          type="text"
                          inputMode="decimal"
                          value={formData.p_tot_trib_sn}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              p_tot_trib_sn: e.target.value.replace(/[^0-9.,]/g, ''),
                            })
                          }
                          placeholder="2.50"
                          className={INPUT}
                        />
                        <p className="text-[11px] text-gray-500 mt-1">Vazio: usa a alíquota de ISS informada abaixo.</p>
                      </div>
                    </div>
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Regime especial de tributação
                  </label>
                  <select
                    value={formData.regime_especial_tributacao}
                    onChange={(e) =>
                      setFormData({ ...formData, regime_especial_tributacao: e.target.value })
                    }
                    className={INPUT}
                  >
                    <option value="0">Nenhum</option>
                    <option value="1">Microempresa Municipal</option>
                    <option value="2">Estimativa</option>
                    <option value="3">Sociedade de Profissionais</option>
                    <option value="4">Cooperativa</option>
                    <option value="5">MEI</option>
                    <option value="6">ME/EPP Simples Nacional</option>
                  </select>
                </div>
                <div className="flex flex-col gap-3 justify-end">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.optante_simples_nacional}
                      onChange={(e) =>
                        setFormData({ ...formData, optante_simples_nacional: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <span className="text-sm">Optante pelo Simples Nacional</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.incentivador_cultural}
                      onChange={(e) =>
                        setFormData({ ...formData, incentivador_cultural: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <span className="text-sm">Incentivador cultural</span>
                  </label>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Série {isIssnetNacional ? 'DPS / RPS' : 'RPS'}
                  </label>
                  <input
                    type="text"
                    value={formData.issnet_serie_rps}
                    onChange={(e) => setFormData({ ...formData, issnet_serie_rps: e.target.value })}
                    className={INPUT}
                    placeholder="1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Último RPS/DPS emitido
                  </label>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={formData.issnet_ultimo_rps_conhecido}
                    onChange={(e) =>
                      setFormData({ ...formData, issnet_ultimo_rps_conhecido: e.target.value })
                    }
                    className={INPUT}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Número do lote (opcional)
                  </label>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={formData.issnet_numero_lote}
                    onChange={(e) => setFormData({ ...formData, issnet_numero_lote: e.target.value })}
                    className={INPUT}
                  />
                </div>
              </div>
              <div className="mt-6 pt-4 border-t border-gray-200 dark:border-[#0d1f3c]">
                <CamposServicoBasicos formData={formData} setFormData={setFormData} inputClass={INPUT} />
              </div>
            </div>
          </>
        )}

        {/* —— 4. API Nacional ADN —— */}
        {isNacionalAdn && (
          <div className={CARD}>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Configurações — API Nacional NFS-e
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
              Emissão direta (ADN). Requer certificado A1 da loja e município habilitado para emissão sem
              intermediário.
            </p>

            <CertificadoFields
              certificadoFile={certificadoFile}
              temCertificadoSalvo={Boolean(config?.issnet_certificado)}
              senha={formData.issnet_senha_certificado}
              onSenha={(v) => setFormData({ ...formData, issnet_senha_certificado: v })}
              onFileChange={handleFileChange}
              inputClass={INPUT}
              labelCertificado="Certificado Digital A1 (.pfx) *"
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Inscrição municipal *
                </label>
                <input
                  type="text"
                  value={formData.inscricao_municipal}
                  onChange={(e) => setFormData({ ...formData, inscricao_municipal: e.target.value })}
                  className={INPUT}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Código IBGE do município *
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={7}
                  value={formData.nacional_codigo_municipio}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      nacional_codigo_municipio: e.target.value.replace(/\D/g, '').slice(0, 7),
                    })
                  }
                  placeholder="3543402"
                  className={INPUT}
                />
                <p className="text-[11px] text-gray-500 mt-1">7 dígitos (ex.: 3543402 Ribeirão Preto).</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Código NBS
                </label>
                <input
                  type="text"
                  value={formData.codigo_nbs}
                  onChange={(e) => setFormData({ ...formData, codigo_nbs: e.target.value })}
                  className={INPUT}
                />
              </div>
              <label className="flex items-center gap-2 cursor-pointer self-end pb-2">
                <input
                  type="checkbox"
                  checked={formData.optante_simples_nacional}
                  onChange={(e) =>
                    setFormData({ ...formData, optante_simples_nacional: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <span className="text-sm">Optante pelo Simples Nacional</span>
              </label>
            </div>

            <div className="mt-6 pt-4 border-t border-gray-200 dark:border-[#0d1f3c]">
              <CamposServicoBasicos formData={formData} setFormData={setFormData} inputClass={INPUT} />
            </div>
          </div>
        )}

        {(showCertConfig || showServicoConfig || isAsaas) && (
          <div className="flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 disabled:opacity-50"
            >
              {loading ? 'Salvando...' : 'Salvar configurações'}
            </button>
          </div>
        )}
    </>
  );
}
