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
  const MAX_ATTEMPTS = 18; // 18 tentativas (aumentado de 12)
  const ATTEMPT_INTERVAL = 5000; // 5 segundos entre tentativas
  const ATTEMPT_INTERVAL_503 = 8000; // 8 segundos quando receber 503 (servidor acordando)
  const TOTAL_TIMEOUT = 120000; // 120 segundos total (aumentado de 70s)

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
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s por tentativa (aumentado de 10s)

        const response = await fetch('/api/backend-health?server=render', {
          method: 'GET',
          signal: controller.signal,
          cache: 'no-store',
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          const data = await response.json();
          
          // Verificar se o servidor está realmente pronto
          if (data.ok && data.status === 200 && data.configured !== false) {
            updateProgress({
              status: 'ready',
              message: 'Servidor acordado e pronto!',
              progress: 100,
            });
            return true;
          }
          
          // Se recebeu 503, o servidor está acordando mas ainda não está pronto
          if (data.status === 503) {
            updateProgress({
              status: 'waking',
              message: `Servidor acordando, inicializando banco de dados... (tentativa ${attempt}/${MAX_ATTEMPTS})`,
              progress: progressPercent,
            });
            
            // Aguardar mais tempo quando receber 503
            if (attempt < MAX_ATTEMPTS) {
              await new Promise(resolve => setTimeout(resolve, ATTEMPT_INTERVAL_503));
            }
            continue;
          }
        }

        // Se não acordou ainda, aguardar antes da próxima tentativa
        if (attempt < MAX_ATTEMPTS) {
          await new Promise(resolve => setTimeout(resolve, ATTEMPT_INTERVAL));
        }

      } catch (error) {
        // Timeout ou erro de rede, continuar tentando
        console.log(`Tentativa ${attempt} falhou:`, error);
        
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
      message: 'Servidor não respondeu após várias tentativas. Tente novamente em alguns minutos.',
      progress: 0,
    });
    return false;

  } catch (error) {
    console.error('Erro ao acordar servidor Render:', error);
    updateProgress({
      status: 'error',
      message: 'Erro ao tentar acordar o servidor. Tente novamente.',
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
