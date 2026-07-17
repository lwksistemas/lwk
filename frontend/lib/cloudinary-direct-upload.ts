/** Upload direto ao Cloudinary (preset unsigned) — galeria ou câmera nativa. */

const EXT_IMAGEM = /\.(jpe?g|png|gif|webp|heic|heif|bmp)$/i;

/** Compressão moderada para estética clínica (alvo ~1,5 MB). */
export const LIMITE_FOTO_CLINICA_BYTES = Math.round(1.5 * 1024 * 1024);
export const MAX_LADO_FOTO_CLINICA = 1600;
const JPEG_QUALIDADE_INICIAL = 0.82;
const JPEG_QUALIDADE_MINIMA = 0.75;
const JPEG_QUALIDADE_PASSO = 0.02;
const MIN_LADO_IMAGEM = 1200;

type FonteImagem = ImageBitmap | HTMLImageElement;

async function carregarFonteImagem(file: File): Promise<FonteImagem | null> {
  if (typeof createImageBitmap === 'function') {
    try {
      return await createImageBitmap(file);
    } catch {
      /* fallback */
    }
  }
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('imagem inválida'));
    };
    img.src = url;
  });
}

function liberarFonteImagem(fonte: FonteImagem) {
  if ('close' in fonte && typeof fonte.close === 'function') fonte.close();
}

async function canvasParaJpeg(canvas: HTMLCanvasElement, qualidade: number): Promise<Blob | null> {
  return new Promise((resolve) => {
    canvas.toBlob((b) => resolve(b), 'image/jpeg', qualidade);
  });
}

/** Reduz fotos grandes antes do upload (qualidade moderada para estética). */
export async function prepararArquivoImagemUpload(file: File): Promise<File> {
  try {
    const fonte = await carregarFonteImagem(file);
    if (!fonte) return file;

    const iw = fonte.width;
    const ih = fonte.height;
    let maxLado = MAX_LADO_FOTO_CLINICA;
    let resultado: File | null = null;

    while (maxLado >= MIN_LADO_IMAGEM) {
      const escala = Math.min(1, maxLado / Math.max(iw, ih));
      const w = Math.max(1, Math.round(iw * escala));
      const h = Math.max(1, Math.round(ih * escala));
      const canvas = document.createElement('canvas');
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext('2d');
      if (!ctx) break;
      ctx.drawImage(fonte, 0, 0, w, h);

      let qualidade = JPEG_QUALIDADE_INICIAL;
      let blob: Blob | null = null;
      while (qualidade >= JPEG_QUALIDADE_MINIMA - 1e-6) {
        blob = await canvasParaJpeg(canvas, qualidade);
        if (blob && blob.size <= LIMITE_FOTO_CLINICA_BYTES) break;
        qualidade -= JPEG_QUALIDADE_PASSO;
      }
      if (blob && blob.size <= LIMITE_FOTO_CLINICA_BYTES) {
        const nome = file.name.replace(EXT_IMAGEM, '.jpg') || 'foto.jpg';
        resultado = new File([blob], nome, { type: 'image/jpeg' });
        break;
      }
      maxLado = Math.round(maxLado * 0.9);
    }

    if (!resultado) {
      const escala = Math.min(1, MIN_LADO_IMAGEM / Math.max(iw, ih));
      const w = Math.max(1, Math.round(iw * escala));
      const h = Math.max(1, Math.round(ih * escala));
      const canvas = document.createElement('canvas');
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(fonte, 0, 0, w, h);
        const blob = await canvasParaJpeg(canvas, JPEG_QUALIDADE_MINIMA);
        if (blob) {
          const nome = file.name.replace(EXT_IMAGEM, '.jpg') || 'foto.jpg';
          resultado = new File([blob], nome, { type: 'image/jpeg' });
        }
      }
    }

    liberarFonteImagem(fonte);
    return resultado ?? file;
  } catch {
    return file;
  }
}

export async function uploadImagemCloudinary(file: File, folder: string): Promise<string> {
  const cloudName = process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME || 'dzrdbw74w';
  const uploadPreset = process.env.NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET || 'lwk_padrao';
  const arquivo = await prepararArquivoImagemUpload(file);

  const formData = new FormData();
  formData.append('file', arquivo);
  formData.append('upload_preset', uploadPreset);
  formData.append('folder', folder);
  formData.append('asset_folder', folder);

  const res = await fetch(`https://api.cloudinary.com/v1_1/${cloudName}/image/upload`, {
    method: 'POST',
    body: formData,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error((data as { error?: { message?: string } }).error?.message || 'Falha no upload');
  }
  return (data as { secure_url: string }).secure_url;
}
