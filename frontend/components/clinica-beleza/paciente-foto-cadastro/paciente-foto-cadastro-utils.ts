export function mensagemErroCamera(err: unknown): string {
  if (err instanceof DOMException) {
    if (err.name === "NotAllowedError") {
      return "Permita o acesso à câmera no navegador (ícone de cadeado/câmera na barra de endereço).";
    }
    if (err.name === "NotFoundError") {
      return "Nenhuma webcam encontrada. Conecte uma câmera ou use Importar foto.";
    }
    if (err.name === "NotReadableError") {
      return "A câmera está em uso por outro aplicativo. Feche o outro app e tente novamente.";
    }
  }
  return "Não foi possível acessar a câmera. Verifique se há webcam conectada e permita o acesso no navegador.";
}

export async function obterStreamCamera(): Promise<MediaStream> {
  const tentativas: MediaStreamConstraints[] = [
    {
      video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 1280 } },
      audio: false,
    },
    { video: { width: { ideal: 1280 }, height: { ideal: 1280 } }, audio: false },
    { video: true, audio: false },
  ];
  let ultimoErro: unknown;
  for (const constraints of tentativas) {
    try {
      return await navigator.mediaDevices.getUserMedia(constraints);
    } catch (err) {
      ultimoErro = err;
      if (err instanceof DOMException && err.name === "NotAllowedError") {
        throw err;
      }
    }
  }
  throw ultimoErro ?? new Error("camera_unavailable");
}

export function isArquivoImagemValido(file: File): boolean {
  return file.type.startsWith("image/") || /\.(jpe?g|png|gif|webp|heic|heif|bmp)$/i.test(file.name);
}

export async function capturarFotoDoVideo(video: HTMLVideoElement): Promise<Blob | null> {
  if (!video.videoWidth) return null;
  const canvas = document.createElement("canvas");
  const size = Math.min(video.videoWidth, video.videoHeight);
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  const offsetX = (video.videoWidth - size) / 2;
  const offsetY = (video.videoHeight - size) / 2;
  ctx.drawImage(video, offsetX, offsetY, size, size, 0, 0, size, size);
  return new Promise((resolve) => {
    canvas.toBlob((b) => resolve(b), "image/jpeg", 0.92);
  });
}
