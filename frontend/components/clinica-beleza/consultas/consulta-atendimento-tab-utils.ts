/** Protocolo fica visível durante o atendimento, mesmo com o editor de notas aberto. */
export function mostrarSeletorProtocolo(
  protocolosCount: number,
  consultaFinalizada: boolean,
): boolean {
  return protocolosCount > 0 && !consultaFinalizada;
}

/** Notas digitáveis enquanto a consulta não foi finalizada — sem clique extra em Editar. */
export function mostrarEditorNotasAtendimento(consultaFinalizada: boolean): boolean {
  return !consultaFinalizada;
}
