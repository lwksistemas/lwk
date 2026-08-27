/**
 * Origens da Content-Security-Policy do Next.js.
 * A Memed (Sinapse) usa memed.com.br e também memed.rocks (Unleash / WebSocket).
 */
const MEMED_HTTPS = [
  "https://memed.com.br",
  "https://*.memed.com.br",
  "https://*.memed.rocks",
];

const MEMED_WSS = ["wss://*.memed.com.br", "wss://*.memed.rocks"];

function extraConnectSrcOrigins() {
  return [
    "https://api.lwksistemas.com.br",
    "https://beta.lwksistemas.com.br",
    "https://media.lwksistemas.com.br",
    "https://viacep.com.br",
    "https://brasilapi.com.br",
    ...MEMED_HTTPS,
    ...MEMED_WSS,
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
