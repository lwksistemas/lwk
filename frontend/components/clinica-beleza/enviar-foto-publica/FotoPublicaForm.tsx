'use client';

import { Camera, CheckCircle, Images, Upload, X } from 'lucide-react';
import { AlertCircle, Stethoscope } from 'lucide-react';
import type { ArquivoPendente, FotoUploadConfig } from './useEnviarFotoPublica';

interface FotoPublicaFormProps {
  config: FotoUploadConfig;
  pendentes: ArquivoPendente[];
  erro: string;
  enviando: boolean;
  preparando: boolean;
  progressoEnvio: string;
  maxFotos: number;
  maxNesteEnvio: number;
  cameraInputRef: React.RefObject<HTMLInputElement | null>;
  galeriaInputRef: React.RefObject<HTMLInputElement | null>;
  onCameraChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onGaleriaChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onConfirmarEnvio: () => void;
  onRemoverPendente: (id: string) => void;
}

export function FotoPublicaForm({
  config,
  pendentes,
  erro,
  enviando,
  preparando,
  progressoEnvio,
  maxFotos,
  maxNesteEnvio,
  cameraInputRef,
  galeriaInputRef,
  onCameraChange,
  onGaleriaChange,
  onConfirmarEnvio,
  onRemoverPendente,
}: FotoPublicaFormProps) {
  const temPendentes = pendentes.length > 0;

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white p-4 pb-8">
      <div className="max-w-md mx-auto">
        <div className="text-center pt-8 pb-6">
          <div className="inline-flex p-3 rounded-full bg-purple-100 mb-3">
            <Stethoscope className="w-8 h-8 text-purple-700" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Foto do paciente</h1>
          <p className="text-gray-600 mt-1">{config.clinica_nome}</p>
          <p className="text-sm font-medium text-gray-800 mt-3">
            Paciente: {config.paciente_nome}
          </p>
          {config.profissional_nome && (
            <p className="text-xs text-gray-500 mt-1">Profissional: {config.profissional_nome}</p>
          )}
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6 space-y-4">
          <p className="text-sm text-gray-600 text-center">
            {preparando
              ? 'Otimizando foto para envio…'
              : temPendentes
                ? 'Confira as fotos selecionadas e toque em Enviar.'
                : 'Use a câmera do celular ou o botão Galeria para escolher fotos já salvas.'}
          </p>

          {temPendentes && (
            <div className="grid grid-cols-3 gap-2">
              {pendentes.map((item) => (
                <div
                  key={item.id}
                  className="relative aspect-square rounded-lg overflow-hidden border border-gray-200 bg-gray-100"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={item.preview} alt="Prévia" className="w-full h-full object-cover" />
                  {!enviando && (
                    <button
                      type="button"
                      onClick={() => onRemoverPendente(item.id)}
                      className="absolute top-1 right-1 p-1 rounded-full bg-black/60 text-white"
                      aria-label="Remover foto"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {temPendentes && (
            <p className="text-xs text-center text-gray-500">
              {pendentes.length} foto{pendentes.length !== 1 ? 's' : ''} selecionada
              {pendentes.length !== 1 ? 's' : ''}
              {pendentes.length < maxNesteEnvio && ' — você pode adicionar mais'}
            </p>
          )}

          {erro && (
            <p className="text-sm text-red-600 text-center flex items-center justify-center gap-1">
              <AlertCircle size={16} />
              {erro}
            </p>
          )}

          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="user"
            className="hidden"
            onChange={onCameraChange}
          />
          <input
            ref={galeriaInputRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={onGaleriaChange}
          />

          {maxNesteEnvio <= 0 && !temPendentes ? (
            <p className="text-sm text-center text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-3 py-3">
              Limite de {maxFotos} fotos por consulta já atingido.
            </p>
          ) : temPendentes ? (
            <div className="space-y-3">
              <button
                type="button"
                disabled={enviando}
                onClick={() => void onConfirmarEnvio()}
                className="w-full flex items-center justify-center gap-2 py-4 rounded-xl bg-green-600 text-white font-semibold text-lg disabled:opacity-50"
              >
                {enviando ? (
                  <>
                    <Upload className="animate-pulse" size={22} />
                    {progressoEnvio || 'Enviando…'}
                  </>
                ) : (
                  <>
                    <CheckCircle size={22} />
                    Enviar {pendentes.length} foto{pendentes.length !== 1 ? 's' : ''}
                  </>
                )}
              </button>
              {!enviando && pendentes.length < maxNesteEnvio && (
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => cameraInputRef.current?.click()}
                    className="flex items-center justify-center gap-2 py-3 rounded-xl border border-gray-300 text-gray-700 font-medium text-sm"
                  >
                    <Camera size={18} />
                    Câmera
                  </button>
                  <button
                    type="button"
                    onClick={() => galeriaInputRef.current?.click()}
                    className="flex items-center justify-center gap-2 py-3 rounded-xl border border-gray-300 text-gray-700 font-medium text-sm"
                  >
                    <Images size={18} />
                    Galeria
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              <button
                type="button"
                disabled={enviando || preparando}
                onClick={() => cameraInputRef.current?.click()}
                className="w-full flex items-center justify-center gap-2 py-4 rounded-xl bg-purple-700 text-white font-semibold text-lg disabled:opacity-50"
              >
                <Camera size={22} />
                Tirar foto (câmera)
              </button>
              <button
                type="button"
                disabled={enviando || preparando}
                onClick={() => galeriaInputRef.current?.click()}
                className="w-full flex items-center justify-center gap-2 py-4 rounded-xl border-2 border-purple-300 bg-purple-50 text-purple-900 font-semibold text-lg disabled:opacity-50"
              >
                <Images size={22} />
                Galeria — escolher fotos salvas
              </button>
              <p className="text-xs text-center text-gray-500 px-2">
                Até {maxNesteEnvio} foto(s) restantes nesta consulta (máx. {maxFotos}).
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
