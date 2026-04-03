'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Upload, X, Image as ImageIcon } from 'lucide-react';

interface ImageUploadProps {
  value?: string;
  onChange: (url: string) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  maxSize?: number; // em MB
  aspectRatio?: string; // ex: '16:9', '1:1', '4:3'
  folder?: string; // pasta no Cloudinary (ex: 'lwksistemas/22239255889')
}

declare global {
  interface Window {
    cloudinary: any;
  }
}

export function ImageUpload({
  value,
  onChange,
  label = 'Imagem',
  description,
  disabled = false,
  maxSize = 5,
  aspectRatio,
  folder = 'lwksistemas',
}: ImageUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Carregar script do Cloudinary se ainda não estiver carregado
    if (typeof window !== 'undefined' && !window.cloudinary) {
      const script = document.createElement('script');
      script.src = 'https://upload-widget.cloudinary.com/global/all.js';
      script.async = true;
      document.body.appendChild(script);
    }
  }, []);

  const handleUpload = () => {
    if (disabled) return;
    
    setError(null);
    
    if (!window.cloudinary) {
      setError('Cloudinary não está carregado. Recarregue a página.');
      return;
    }

    const widget = window.cloudinary.createUploadWidget(
      {
        cloudName: 'dzrdbw74w',
        uploadPreset: 'lwk_padrao',
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
        folder: folder, // 🔒 Pasta específica da loja para isolamento
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
              explanation: 'Certifique-se de que sua câmera está conectada e que seu navegador permite captura de câmera. Quando estiver pronto, clique em Capturar.',
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
              title_uploading_processing_with_counters: 'Fazendo Upload de {{uploading}} Arquivos, Processando {{processing}} Arquivos',
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
      },
      (error: any, result: any) => {
        if (error) {
          console.error('Erro no upload:', error);
          setError('Erro ao fazer upload da imagem');
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
            <div className={`relative ${previewFrameClass.replace('flex items-center justify-center', '').trim()}`}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={value}
                alt="Preview"
                className={previewImgClass}
                onError={(e) => {
                  console.error('Erro ao carregar imagem:', value);
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
            onClick={handleUpload}
            disabled={disabled || uploading}
            className="w-full sm:w-auto"
          >
            <Upload className="w-4 h-4 mr-2" />
            {uploading ? 'Enviando...' : value ? 'Alterar Imagem' : 'Escolher Imagem'}
          </Button>

          <p className="text-xs text-gray-500 dark:text-gray-400">
            Formatos: JPG, PNG, GIF, WebP • Máximo: {maxSize}MB
            {aspectRatio && ` • Proporção: ${aspectRatio}`}
          </p>

          {error && (
            <p className="text-xs text-red-600 dark:text-red-400">
              {error}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
