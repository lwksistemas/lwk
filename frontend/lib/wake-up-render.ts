/**
 * Função para acordar o servidor Render (plano Free)
 * 
 * O servidor Render no plano Free "dorme" após 15 minutos de inatividade.
 * Esta função faz requisições para acordar o servidor antes de usá-lo.
 */

export interface WakeUpProgress {
  status: 'checking' | 'waking' | 'ready' | 'error';
  message: string;
  progress: number; // 0-100
}

export type WakeUpCallback = (progress: WakeUpProgress) => void;

/**
 * Acorda o servidor Render fazendo requisições até ele responder
 * 
 * @param onProgress Callback para atualizar o progresso
 * @returns Promise<boolean> true se acordou com sucesso
 */
export async function wakeUpRenderServer(
  onProgress?: WakeUpCallback
): Promise<boolean> {
  const RENDER_URL = 'https://lwksistemas-backup.onrender.com';
  const MAX_ATTEMPTS = 12; // 12 tentativas
  const ATTEMPT_INTERVAL = 5000; // 5 segundos entre tentativas
  const TOTAL_TIMEOUT = 70000; // 70 segundos total

  const updateProgress = (progress: WakeUpProgress) => {
    if (onProgress) {
      onProgress(progress);
    }
  };

  try {
    updateProgress({
      status: 'checking',
      message: 'Verificando status do servidor...',
      progress: 0,
    });

    // Tentar acordar o servidor
    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
      try {
        const progressPercent = Math.min((attempt / MAX_ATTEMPTS) * 100, 95);
        
        updateProgress({
          status: 'waking',
          message: `Acordando servidor... (tentativa ${attempt}/${MAX_ATTEMPTS})`,
          progress: progressPercent,
        });

        // Fazer requisição via API route para evitar CORS
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s por tentativa

        const response = await fetch('/api/backend-health?server=render', {
          method: 'GET',
          signal: controller.signal,
          cache: 'no-store',
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          const data = await response.json();
          
          if (data.ok && data.configured !== false) {
            updateProgress({
              status: 'ready',
              message: 'Servidor acordado e pronto!',
              progress: 100,
            });
            return true;
          }
        }

        // Se não acordou ainda, aguardar antes da próxima tentativa
        if (attempt < MAX_ATTEMPTS) {
          await new Promise(resolve => setTimeout(resolve, ATTEMPT_INTERVAL));
        }

      } catch (error) {
        // Timeout ou erro de rede, continuar tentando
        if (attempt === MAX_ATTEMPTS) {
          throw error;
        }
        // Aguardar antes da próxima tentativa
        await new Promise(resolve => setTimeout(resolve, ATTEMPT_INTERVAL));
      }
    }

    // Se chegou aqui, não conseguiu acordar
    updateProgress({
      status: 'error',
      message: 'Servidor não respondeu após várias tentativas',
      progress: 0,
    });
    return false;

  } catch (error) {
    console.error('Erro ao acordar servidor Render:', error);
    updateProgress({
      status: 'error',
      message: 'Erro ao tentar acordar o servidor',
      progress: 0,
    });
    return false;
  }
}

/**
 * Verifica se o servidor está acordado (responde rápido)
 */
export async function isRenderServerAwake(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s

    const response = await fetch('/api/backend-health?server=render', {
      method: 'GET',
      signal: controller.signal,
      cache: 'no-store',
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      return data.ok && data.configured !== false;
    }

    return false;
  } catch {
    return false;
  }
}
