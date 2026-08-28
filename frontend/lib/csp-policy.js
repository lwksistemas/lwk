/**
 * Origens da Content-Security-Policy do Next.js.
 * Sinapse 3.25+ (ago/2026) usa v4-embedded.memed.com.br e Unleash em
 * unleash-proxy.data.memed.rocks — o host aninhado precisa de entrada própria.
 * Telemetria da Memed (RudderStack / IP) também precisa de connect-src.
 */
const MEMED_HTTPS = [
  "https://memed.com.br",
  "https://*.memed.com.br",
  "https://v4-embedded.memed.com.br",
  "https://*.memed.rocks",
  "https://*.data.memed.rocks",
];

const MEMED_WSS = [
  "wss://*.memed.com.br",
  "wss://*.memed.rocks",
  "wss://*.data.memed.rocks",
];

const MEMED_TELEMETRIA = [
  "https://api.rudderstack.com",
  "https://*.rudderstack.com",
  "https://cdn.rudderlabs.com",
  "https://*.rudderlabs.com",
  "https://ipv4.icanhazip.com",
  "https://api.ipify.org",
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

module.exports = {
  MEMED_HTTPS,
  MEMED_WSS,
  extraConnectSrcOrigins,
};
