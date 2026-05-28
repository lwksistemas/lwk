/** Filtros de status na UI de listagem NFS-e (superadmin). */
export const NFSE_FILTRO_STATUS_OPCOES: { value: string; label: string }[] = [
  { value: '', label: 'Todas' },
  { value: 'emitida', label: '✅ Emitidas' },
  { value: 'cancelada', label: '❌ Canceladas' },
  { value: 'erro', label: '⚠️ Erros' },
];
