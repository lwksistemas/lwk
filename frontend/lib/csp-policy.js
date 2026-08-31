/**
 * Origens da Content-Security-Policy do Next.js.
 * V4 embedded precisa do Unleash (*.memed.rocks) para o iframe subir.
 */
const MEMED_HTTPS = [
  "https://memed.com.br",
  "https://*.memed.com.br",
  "https://v4-embedded.memed.com.br",
  "https://v4-embedded-qa.memed.com.br",
  "https://gateway.memed.com.br",
  "https://cdn.memed.com.br",
  "https://*.memed.rocks",
  "https://data.memed.rocks",
];

const MEMED_WSS = [
  "wss://*.memed.com.br",
  "wss://*.memed.rocks",
];

const MEMED_TELEMETRIA = [
  "https://api.rudderstack.com",
  "https://*.rudderstack.com",
  "https://cdn.rudderlabs.com",
  "https://*.rudderlabs.com",
  "https://ipv4.icanhazip.com",
  "https://api.ipify.org",
  "https://d2r1yp2w7bby2u.cloudfront.net",
  "https://*.cloudfront.net",
];

function extraConnectSrcOrigins() {
  return [
    "https://api.lwksistemas.com.br",
    "https://beta.lwksistemas.com.br",
    "https://media.lwksistemas.com.br",
    "https://viacep.com.br",
    "https://brasilapi.com.br",
    ...MEMED_HTTPS,
    ...MEMED_WSS,
    ...MEMED_TELEMETRIA,
    "https://meet.jit.si",
    "wss://meet.jit.si",
    "https://*.jitsi.net",
    "wss://*.jitsi.net",
    "https://8x8.vc",
    "wss://8x8.vc",
  ];
}

function extraImgSrcOrigins() {
  const origins = new Set([
    "https://media.lwksistemas.com.br",
    "https://beta.lwksistemas.com.br",
    "https://i.pravatar.cc",
  ]);
  const mediaUrl = process.env.NEXT_PUBLIC_MEDIA_URL || "";
  if (mediaUrl) {
    try {
      origins.add(new URL(mediaUrl).origin);
    } catch {
      /* ignore */
    }
  }
  return Array.from(origins).join(" ");
}

module.exports = {
  MEMED_HTTPS,
  MEMED_WSS,
  extraConnectSrcOrigins,
  extraImgSrcOrigins,
};
