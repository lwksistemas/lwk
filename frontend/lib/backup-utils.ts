/**
 * Utilitários para o recurso de backup das lojas.
 * Centraliza extração de mensagem de erro (resposta blob/JSON/403) e constantes.
 */

/** Tamanho máximo do arquivo de importação (500 MB), alinhado ao backend */
export const BACKUP_MAX_UPLOAD_BYTES = 500 * 1024 * 1024;

const BACKUP_403_MESSAGE = 'Sem permissão para exportar backup desta loja.';
const IMPORT_403_MESSAGE = 'Sem permissão para importar backup nesta loja.';

/**
 * Extrai mensagem de erro da resposta da API de backup.
 * Trata responseType: 'blob' (resposta de erro vem como Blob com JSON dentro).
 */
export async function getBackupErrorMessage(
  error: any,
  fallback: string,
  options?: { isImport?: boolean }
): Promise<string> {
  if (error?.response?.status === 403) {
    return options?.isImport ? IMPORT_403_MESSAGE : BACKUP_403_MESSAGE;
  }
  const data = error?.response?.data;
  if (data == null) return fallback;
  if (typeof data === 'string') return data;
  if (data.error) return data.error;
  if (data instanceof Blob) {
    try {
      const text = await data.text();
      const parsed = text ? JSON.parse(text) : {};
      return parsed.error || fallback;
    } catch {
      return fallback;
    }
  }
  return fallback;
}
