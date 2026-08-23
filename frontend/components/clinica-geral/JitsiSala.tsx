'use client';

type JitsiSalaProps = {
  sala: string;
  displayName: string;
  altura?: number;
};

export function salaJitsiDeUrl(url: string): string {
  return (url || '').replace(/\/+$/, '').split('/').pop() || '';
}

export function urlEmbedJitsi(sala: string, displayName: string): string {
  const nome = encodeURIComponent(displayName || 'Participante');
  const hash = [
    `userInfo.displayName="${nome}"`,
    'config.prejoinPageEnabled=true',
    'config.disableDeepLinking=true',
  ].join('&');
  return `https://meet.jit.si/${encodeURIComponent(sala)}#${hash}`;
}

export function JitsiSala({ sala, displayName, altura = 320 }: JitsiSalaProps) {
  if (!sala) {
    return <p className="text-sm text-slate-500">Sala ainda não disponível.</p>;
  }
  const src = urlEmbedJitsi(sala, displayName);
  return (
    <div className="space-y-2">
      <iframe
        title="Teleconsulta"
        src={src}
        allow="camera; microphone; fullscreen; display-capture; autoplay; clipboard-write"
        allowFullScreen
        className="w-full rounded-md border-0 bg-slate-900"
        style={{ height: altura, minHeight: altura }}
      />
      <a href={src} target="_blank" rel="noreferrer" className="block text-center text-xs underline" style={{ color: '#0D9B9B' }}>
        Se o vídeo não aparecer, abrir em nova aba
      </a>
    </div>
  );
}
