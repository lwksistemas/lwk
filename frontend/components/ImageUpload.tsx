'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Upload, X, Image as ImageIcon } from 'lucide-react';
import { logger } from '@/lib/logger';

interface ImageUploadProps {
  value?: string;
  onChange: (url: string) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  maxSize?: number; // em MB
  aspectRatio?: string; // ex: '16:9', '1:1', '4:3'
  folder?: string; // pasta no Cloudinary (ex: 'lwksistemas/22239255889')
  /** Botão inline, sem área de preview — para barras de ação compactas */
  compact?: boolean;
  buttonLabel?: string;
}

declare global {
  interface Window {
    cloudinary: any;
  }
}

const CLOUDINARY_WIDGET_SRC = 'https://upload-widget.cloudinary.com/global/all.js';

/** Uma única carga do script para todos os ImageUpload (evita corrida e duplicados). */
let cloudinaryScriptPromise: Promise<void> | null = null;

export function resetCloudinaryWidgetScript(): void {
  cloudinaryScriptPromise = null;
  if (typeof document !== 'undefined') {
    document.querySelectorAll('script[data-lwk-cloudinary-widget="1"]').forEach((el) => el.remove());
  }
  if (typeof window !== 'undefined') {
    delete window.cloudinary;
  }
}

function loadCloudinaryWidgetScript(): Promise<void> {
  if (typeof window === 'undefined') {
    return Promise.resolve();
  }
  if (window.cloudinary?.createUploadWidget) {
    return Promise.resolve();
  }
  if (cloudinaryScriptPromise) {
    return cloudinaryScriptPromise;
  }
  const p = new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(
      'script[data-lwk-cloudinary-widget="1"]'
    );
    if (existing) {
      if (window.cloudinary?.createUploadWidget) {
        resolve();
        return;
      }
      const t0 = Date.now();
      const poll = () => {
        if (window.cloudinary?.createUploadWidget) {
          resolve();
          return;
        }
        if (Date.now() - t0 > 30000) {
          reject(new Error('Timeout ao aguardar Cloudinary'));
          return;
        }
        setTimeout(poll, 50);
      };
      existing.addEventListener('error', () =>
        reject(new Error('Script Cloudinary falhou'))
      );
      poll();
      return;
    }
    const script = document.createElement('script');
    script.src = CLOUDINARY_WIDGET_SRC;
    script.async = true;
    script.dataset.lwkCloudinaryWidget = '1';
    script.onload = () => {
      if (window.cloudinary?.createUploadWidget) resolve();
      else reject(new Error('Cloudinary não disponível após carregar o script'));
    };
    script.onerror = () => reject(new Error('Não foi possível carregar o widget do Cloudinary'));
    document.body.appendChild(script);
  });
  cloudinaryScriptPromise = p.catch((err) => {
    cloudinaryScriptPromise = null;
    throw err;
  });
  return cloudinaryScriptPromise;
}

export function ImageUpload({
  value,
  onChange,
  label = 'Imagem',
  description,
  disabled = false,
  maxSize = 5,
  aspectRatio,
  folder = 'lwksistemas/misc',
  compact = false,
  buttonLabel,
}: ImageUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [widgetReady, setWidgetReady] = useState(
    () => typeof window !== 'undefined' && Boolean(window.cloudinary?.createUploadWidget)
  );
  const [loadAttempt, setLoadAttempt] = useState(0);

  const prepareWidget = (force = false) => {
    if (force) {
      resetCloudinaryWidgetScript();
      setWidgetReady(false);
    }
    return loadCloudinaryWidgetScript()
      .then(() => {
        setWidgetReady(true);
        setError(null);
      })
      .catch((e: unknown) => {
        logger.warn('Erro ao carregar widget Cloudinary:', e);
        setWidgetReady(false);
        setError('Não foi possível carregar o upload de imagens (Cloudinary).');
        throw e;
      });
  };

  useEffect(() => {
    let cancelled = false;
    prepareWidget()
      .catch(() => {
        /* erro já tratado em prepareWidget */
      })
      .finally(() => {
        if (cancelled) return;
      });
    return () => {
      cancelled = true;
    };
  }, [loadAttempt]);

  const cloudName = process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME || 'dzrdbw74w';
  const uploadPreset = process.env.NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET || 'lwk_padrao';

  const handleUpload = async () => {
    if (disabled) return;

    setError(null);

    try {
      await loadCloudinaryWidgetScript();
    } catch (e) {
      logger.warn('Cloudinary não está pronto:', e);
      setError('Cloudinary não está pronto. Recarregue a página ou tente em instantes.');
      return;
    }

    if (!window.cloudinary?.createUploadWidget) {
      setError('Cloudinary não está carregado. Recarregue a página.');
      return;
    }

    const uploadOptions = {
      cloudName,
      uploadPreset,
      secure: true,
      sources: ['local', 'url', 'camera'],
      multiple: false,
      maxFileSize: maxSize * 1024 * 1024,
      clientAllowedFormats: ['jpg', 'jpeg', 'png', 'gif', 'webp'],
      maxImageWidth: 2000,
      maxImageHeight: 2000,
      cropping: aspectRatio ? true : false,
      croppingAspectRatio: aspectRatio ? parseAspectRatio(aspectRatio) : undefined,
      croppingShowDimensions: true,
      showSkipCropButton: false,
      folder,
      asset_folder: folder,
      useAssetFolderAsPublicIdPrefix: true,
      resourceType: 'image',
      language: 'pt',
      text: {
        pt: {
          or: 'Ou',
          back: 'Voltar',
          advanced: 'Avançado',
          close: 'Fechar',
          no_results: 'Nenhum resultado',
          search_placeholder: 'Buscar arquivos',
          about_uw: 'Sobre o Upload Widget',
          menu: {
            files: 'Meus Arquivos',
            web: 'Endereço Web',
            camera: 'Câmera',
          },
          local: {
            browse: 'Procurar',
            dd_title_single: 'Arraste e solte uma imagem aqui',
            dd_title_multi: 'Arraste e solte imagens aqui',
            drop_title_single: 'Solte a imagem para fazer upload',
            drop_title_multi: 'Solte as imagens para fazer upload',
          },
          camera: {
            capture: 'Capturar',
            cancel: 'Cancelar',
            take_pic: 'Tirar foto e fazer upload',
            explanation:
              'Certifique-se de que sua câmera está conectada e que seu navegador permite captura de câmera. Quando estiver pronto, clique em Capturar.',
          },
          crop: {
            title: 'Recortar',
            crop_btn: 'Recortar e Fazer Upload',
            skip_btn: 'Pular',
            reset_btn: 'Resetar',
            close_btn: 'Sim',
            close_prompt: 'Fechar cancelará todos os uploads, tem certeza?',
            image_error: 'Erro ao carregar imagem',
            corner_tooltip: 'Arraste o canto para redimensionar',
            handle_tooltip: 'Arraste a alça para redimensionar',
          },
          url: {
            inner_title: 'URL pública da imagem:',
            input_placeholder: 'http://remote.site.example/images/remote-image.jpg',
          },
          queue: {
            title: 'Fila de Upload',
            title_uploading_with_counter: 'Fazendo Upload de {{num}} Arquivos',
            title_processing_with_counter: 'Processando {{num}} Arquivos',
            title_uploading_processing_with_counters:
              'Fazendo Upload de {{uploading}} Arquivos, Processando {{processing}} Arquivos',
            title_uploading: 'Fazendo Upload de Arquivos',
            mini_title: 'Enviado',
            mini_title_uploading: 'Enviando',
            mini_title_processing: 'Processando',
            show_completed: 'Mostrar concluídos',
            retry_failed: 'Tentar novamente os que falharam',
            abort_all: 'Cancelar Todos',
            upload_more: 'Fazer Upload de Mais',
            done: 'Concluído',
            mini_upload_count: '{{num}} enviado',
            mini_failed: '{{num}} falhou',
            statuses: {
              uploading: 'Enviando...',
              processing: 'Processando...',
              timeout: 'Um arquivo grande está sendo enviado. Pode levar algum tempo.',
              error: 'Erro',
              uploaded: 'Concluído',
              aborted: 'Cancelado',
            },
          },
        },
      },
    };

    const widget = window.cloudinary.createUploadWidget(
      uploadOptions,
      (error: any, result: any) => {
        if (error) {
          logger.warn('Erro no upload Cloudinary:', error, result);
          setError(
            'Erro ao enviar a imagem. Se for importação por URL, confira o link. No Cloudinary, o preset sem assinatura deve permitir este domínio (lwksistemas.com.br).'
          );
          setUploading(false);
          return;
        }

        if (result && result.event === 'success') {
          const imageUrl = result.info.secure_url;
          onChange(imageUrl);
          setUploading(false);
          setError(null);
        }

        if (result && result.event === 'close') {
          setUploading(false);
        }
      }
    );

    setUploading(true);
    widget.open();
  };

  const handleRemove = () => {
    if (disabled) return;
    onChange('');
    setError(null);
  };

  const parseAspectRatio = (ratio: string): number => {
    const [width, height] = ratio.split(':').map(Number);
    return width / height;
  };

  // Preview alinhado à proporção do banner (16:9) para não “vazar” fora do quadro
  const isWideHero = aspectRatio === '16:9';
  const previewFrameClass = isWideHero
    ? 'w-full max-w-md aspect-video rounded-lg border-2 border-gray-200 dark:border-gray-700 overflow-hidden bg-gray-50 dark:bg-gray-800 flex items-center justify-center'
    : 'w-32 h-32 rounded-lg border-2 border-gray-200 dark:border-gray-700 overflow-hidden bg-gray-50 dark:bg-gray-800 flex items-center justify-center';
  const previewImgClass = isWideHero
    ? 'max-w-full max-h-full w-full h-full object-contain object-center'
    : 'w-full h-full object-cover';

  const uploadButtonLabel =
    buttonLabel ||
    (!widgetReady ? 'A carregar…' : uploading ? 'Enviando...' : value ? 'Alterar Imagem' : 'Escolher Imagem');

  if (compact) {
    return (
      <div className="inline-flex flex-col gap-1">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => {
            handleUpload().catch((e) => {
              logger.warn('Erro ao abrir upload:', e);
              setError(String(e?.message || 'Erro ao abrir upload'));
            });
          }}
          disabled={disabled || uploading}
          className="h-9"
        >
          <Upload className="w-4 h-4 mr-2" />
          {uploadButtonLabel}
        </Button>
        {error && (
          <p className="text-xs text-red-600 dark:text-red-400 max-w-xs">{error}</p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {label && (
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      
      {description && (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {description}
        </p>
      )}

      <div className="flex flex-col sm:flex-row items-start gap-4">
        {/* Preview da imagem */}
        {value && value.trim() !== '' ? (
          <div className="relative group w-full sm:w-auto shrink-0">
            <div className={previewFrameClass}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={value}
                alt="Preview"
                className={previewImgClass}
                onError={(e) => {
                  logger.warn('Erro ao carregar preview da imagem');
                  // Se houver erro ao carregar, mostrar placeholder
                  e.currentTarget.style.display = 'none';
                }}
              />
            </div>
            
            {!disabled && (
              <button
                type="button"
                onClick={handleRemove}
                className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 shadow-lg z-10"
                title="Remover imagem"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        ) : (
          <div
            className={
              isWideHero
                ? 'w-full max-w-md aspect-video rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center bg-gray-50 dark:bg-gray-800 shrink-0'
                : 'w-32 h-32 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center bg-gray-50 dark:bg-gray-800 shrink-0'
            }
          >
            <ImageIcon className="w-8 h-8 text-gray-400" />
          </div>
        )}

        {/* Botão de upload */}
        <div className="flex-1 space-y-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              handleUpload().catch((e) => {
                logger.warn('Erro ao abrir upload:', e);
                setError(String(e?.message || 'Erro ao abrir upload'));
              });
            }}
            disabled={disabled || uploading}
            className="w-full sm:w-auto"
          >
            <Upload className="w-4 h-4 mr-2" />
            {!widgetReady
              ? 'A carregar…'
              : uploading
                ? 'Enviando...'
                : value
                  ? 'Alterar Imagem'
                  : 'Escolher Imagem'}
          </Button>

          <p className="text-xs text-gray-500 dark:text-gray-400">
            Formatos: JPG, PNG, GIF, WebP • Máximo: {maxSize}MB
            {aspectRatio && ` • Proporção: ${aspectRatio}`}
          </p>
          {!widgetReady && !error && (
            <p className="text-xs text-amber-600 dark:text-amber-400">
              A preparar o serviço de imagens…
            </p>
          )}

          {error && (
            <div className="space-y-2">
              <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
              <button
                type="button"
                onClick={() => setLoadAttempt((n) => n + 1)}
                className="text-xs font-medium text-blue-600 hover:underline dark:text-blue-400"
              >
                Tentar carregar novamente
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
