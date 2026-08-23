'use client';

import { useEffect, useRef } from 'react';

type JitsiSalaProps = {
  sala: string;
  displayName: string;
  altura?: number;
};

type JitsiApi = { dispose: () => void };

export function salaJitsiDeUrl(url: string): string {
  return (url || '').replace(/\/+$/, '').split('/').pop() || '';
}

export function JitsiSala({ sala, displayName, altura = 320 }: JitsiSalaProps) {
  const host = useRef<HTMLDivElement>(null);
  const api = useRef<JitsiApi | null>(null);

  useEffect(() => {
    if (!sala || !host.current) return;
    let cancelado = false;

    const montar = () => {
      if (cancelado || !host.current || !window.JitsiMeetExternalAPI) return;
      api.current?.dispose();
      host.current.innerHTML = '';
      api.current = new window.JitsiMeetExternalAPI('meet.jit.si', {
        roomName: sala,
        parentNode: host.current,
        width: '100%',
        height: altura,
        userInfo: { displayName },
        configOverwrite: {
          prejoinPageEnabled: true,
          startWithAudioMuted: false,
          startWithVideoMuted: false,
        },
        interfaceConfigOverwrite: {
          SHOW_JITSI_WATERMARK: false,
          SHOW_BRAND_WATERMARK: false,
        },
      });
    };

    if (window.JitsiMeetExternalAPI) {
      montar();
    } else {
      const existente = document.querySelector<HTMLScriptElement>('script[data-jitsi="1"]');
      if (existente) {
        existente.addEventListener('load', montar);
      } else {
        const script = document.createElement('script');
        script.src = 'https://meet.jit.si/external_api.js';
        script.async = true;
        script.dataset.jitsi = '1';
        script.onload = montar;
        document.body.appendChild(script);
      }
    }

    return () => {
      cancelado = true;
      api.current?.dispose();
      api.current = null;
    };
  }, [sala, displayName, altura]);

  return <div ref={host} className="overflow-hidden rounded-md bg-slate-900" style={{ minHeight: altura }} />;
}

declare global {
  interface Window {
    JitsiMeetExternalAPI?: new (
      domain: string,
      options: {
        roomName: string;
        parentNode: HTMLElement;
        width: string | number;
        height: string | number;
        userInfo?: { displayName?: string };
        configOverwrite?: Record<string, unknown>;
        interfaceConfigOverwrite?: Record<string, unknown>;
      },
    ) => JitsiApi;
  }
}
