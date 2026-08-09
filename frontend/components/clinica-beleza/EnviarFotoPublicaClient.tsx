'use client';

import { useEnviarFotoPublica } from './enviar-foto-publica/useEnviarFotoPublica';
import { FotoPublicaErro, FotoPublicaLoading, FotoPublicaSucesso } from './enviar-foto-publica/FotoPublicaStates';
import { FotoPublicaForm } from './enviar-foto-publica/FotoPublicaForm';

export function EnviarFotoPublicaClient({ token: tokenProp }: { token?: string | null }) {
  const {
    loading,
    config,
    erro,
    enviando,
    preparando,
    progressoEnvio,
    fotosEnviadas,
    pendentes,
    cameraInputRef,
    galeriaInputRef,
    maxFotos,
    maxNesteEnvio,
    onCameraChange,
    onGaleriaChange,
    confirmarEnvio,
    removerPendente,
  } = useEnviarFotoPublica(tokenProp);

  if (loading) {
    return <FotoPublicaLoading />;
  }

  if (fotosEnviadas > 0) {
    return <FotoPublicaSucesso fotosEnviadas={fotosEnviadas} />;
  }

  if (erro && !config) {
    return <FotoPublicaErro erro={erro} />;
  }

  if (!config) {
    return <FotoPublicaErro erro="Erro ao carregar configuração." />;
  }

  return (
    <FotoPublicaForm
      config={config}
      pendentes={pendentes}
      erro={erro}
      enviando={enviando}
      preparando={preparando}
      progressoEnvio={progressoEnvio}
      maxFotos={maxFotos}
      maxNesteEnvio={maxNesteEnvio}
      cameraInputRef={cameraInputRef}
      galeriaInputRef={galeriaInputRef}
      onCameraChange={onCameraChange}
      onGaleriaChange={onGaleriaChange}
      onConfirmarEnvio={confirmarEnvio}
      onRemoverPendente={removerPendente}
    />
  );
}
