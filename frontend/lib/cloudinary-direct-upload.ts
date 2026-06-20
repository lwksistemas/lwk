/** Upload direto ao Cloudinary (preset unsigned) — galeria ou câmera nativa. */

const EXT_IMAGEM = /\.(jpe?g|png|gif|webp|heic|heif|bmp)$/i;
const LIMITE_CLOUDINARY_BYTES = 9 * 1024 * 1024;
const MAX_LADO_INICIAL = 1920;

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

/** Reduz fotos grandes antes do upload (limite Cloudinary ~10 MB). */
export async function prepararArquivoImagemUpload(file: File): Promise<File> {
  try {
    const fonte = await carregarFonteImagem(file);
    if (!fonte) return file;

    const iw = fonte.width;
    const ih = fonte.height;
    let maxLado = MAX_LADO_INICIAL;
    let resultado: File | null = null;

    while (maxLado >= 960) {
      const escala = Math.min(1, maxLado / Math.max(iw, ih));
      const w = Math.max(1, Math.round(iw * escala));
      const h = Math.max(1, Math.round(ih * escala));
      const canvas = document.createElement('canvas');
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext('2d');
      if (!ctx) break;
      ctx.drawImage(fonte, 0, 0, w, h);

      let qualidade = 0.88;
      let blob: Blob | null = null;
      while (qualidade >= 0.45) {
        blob = await canvasParaJpeg(canvas, qualidade);
        if (blob && blob.size <= LIMITE_CLOUDINARY_BYTES) break;
        qualidade -= 0.08;
      }
      if (blob && blob.size <= LIMITE_CLOUDINARY_BYTES) {
        const nome = file.name.replace(EXT_IMAGEM, '.jpg') || 'foto.jpg';
        resultado = new File([blob], nome, { type: 'image/jpeg' });
        break;
      }
      maxLado = Math.round(maxLado * 0.75);
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
  const data = (await res.json().catch(() => ({}))) as { secure_url?: string; error?: { message?: string } };
  if (!res.ok || !data.secure_url) {
    throw new Error(data.error?.message || 'Erro ao enviar imagem.');
  }
  return data.secure_url;
}
