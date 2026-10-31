'use client';

import type { ChangeEvent, Dispatch, SetStateAction } from 'react';
import { Upload } from 'lucide-react';
import { DescricoesPorPrestadora } from './DescricoesPorPrestadora';

export function CamposServicoBasicos({
  formData,
  setFormData,
  inputClass,
}: {
  formData: {
    codigo_servico_municipal: string;
    aliquota_iss: string;
    descricao_servico_padrao: string;
    emitir_nf_automaticamente: boolean;
  };
  setFormData: Dispatch<SetStateAction<any>>;
  inputClass: string;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Código do serviço municipal
        </label>
        <input
          type="text"
          value={formData.codigo_servico_municipal}
          onChange={(e) => setFormData((p: any) => ({ ...p, codigo_servico_municipal: e.target.value }))}
          className={inputClass}
          placeholder="Ex: 1401"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Alíquota ISS (%)
        </label>
        <input
          type="number"
          step="0.01"
          min="0"
          max="100"
          value={formData.aliquota_iss}
          onChange={(e) => setFormData((p: any) => ({ ...p, aliquota_iss: e.target.value }))}
          className={inputClass}
        />
      </div>
      <DescricoesPorPrestadora inputClass={inputClass} />
      <div className="md:col-span-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Texto de reserva
        </label>
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
          Usado só quando a empresa prestadora ainda não tem descrição.
        </p>
        <textarea
          value={formData.descricao_servico_padrao}
          onChange={(e) => setFormData((p: any) => ({ ...p, descricao_servico_padrao: e.target.value }))}
          rows={3}
          className={inputClass}
        />
      </div>
      <div className="md:col-span-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={formData.emitir_nf_automaticamente}
            onChange={(e) =>
              setFormData((p: any) => ({ ...p, emitir_nf_automaticamente: e.target.checked }))
            }
            className="w-4 h-4"
          />
          <span className="text-sm text-gray-700 dark:text-gray-300">
            Emitir nota fiscal automaticamente ao confirmar pagamento
          </span>
        </label>
      </div>
    </div>
  );
}

export function CertificadoFields({
  certificadoFile,
  temCertificadoSalvo,
  senha,
  onSenha,
  onFileChange,
  inputClass,
  labelCertificado = 'Certificado Digital A1 (.pfx) *',
}: {
  certificadoFile: File | null;
  temCertificadoSalvo: boolean;
  senha: string;
  onSenha: (v: string) => void;
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  inputClass: string;
  labelCertificado?: string;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
      <div className="md:col-span-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {labelCertificado}
        </label>
        <label className="flex items-center gap-3 px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-[#0176d3]">
          <Upload size={20} className="text-gray-400" />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {certificadoFile
              ? certificadoFile.name
              : temCertificadoSalvo
                ? 'Certificado já enviado — clique para alterar'
                : 'Clique para selecionar o arquivo .pfx'}
          </span>
          <input type="file" accept=".pfx" onChange={onFileChange} className="hidden" />
        </label>
      </div>
      <div className="md:col-span-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Senha do certificado
        </label>
        <input
          type="password"
          value={senha}
          onChange={(e) => onSenha(e.target.value)}
          placeholder="Senha do arquivo .pfx"
          className={inputClass}
        />
      </div>
    </div>
  );
}
