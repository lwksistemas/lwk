'use client';

import { useEffect, useState } from 'react';
import { whatsappConfigApi, type WhatsAppConfigData } from '@/lib/whatsapp-config-api';

const DEFAULT_FLAGS = {
  proposta: true,
  contrato: true,
  termo: true,
  whatsappAtivo: false,
};

export function useWhatsappEnvioFlags() {
  const [flags, setFlags] = useState(DEFAULT_FLAGS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const data: WhatsAppConfigData = await whatsappConfigApi.get();
        if (!cancel) {
          setFlags({
            proposta: data.enviar_proposta_whatsapp ?? true,
            contrato: data.enviar_contrato_whatsapp ?? true,
            termo: data.enviar_termo_consentimento_whatsapp ?? true,
            whatsappAtivo: !!data.whatsapp_ativo,
          });
        }
      } catch {
        if (!cancel) setFlags(DEFAULT_FLAGS);
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => {
      cancel = true;
    };
  }, []);

  return { ...flags, loading };
}
