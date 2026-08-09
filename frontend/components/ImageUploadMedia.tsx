'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Upload, X, Image as ImageIcon, Loader2 } from 'lucide-react';
import apiClient from '@/lib/api-client';

interface ImageUploadMediaProps {
  value?: string;
  onChange?: (url: string) => void;
  /** Se informada, o componente não faz upload sozinho; entrega o arquivo bruto. */
  onFileSelect?: (file: File) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  maxSize?: number; // em MB
  folder?: string; // subpasta: fotos, docs, avatars, recibos, contratos
  /** Botão inline, sem área de preview */
  compact?: boolean;
  buttonLabel?: string;
  /** Aceitar apenas imagens ou também PDFs */
  accept?: string;
}

const MEDIA_SERVER_URL = process.env.NEXT_PUBLIC_MEDIA_URL || 'https://media.lwksistemas.com.br';

export function ImageUploadMedia({
  value,
  onChange,
  onFileSelect,
  label = 'Imagem',
  description,
  disabled = false,
  maxSize = 10,
  folder = 'fotos',
  compact = false,
  buttonLabel,
  accept = 'image/*',
}: ImageUploadMediaProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validar tamanho
    if (file.size > maxSize * 1024 * 1024) {
      setError(`Arquivo muito grande. Máximo: ${maxSize}MB`);
      return;
    }

    setError(null);

    // Modo delegado: o caller faz o upload (ex.: consulta fotos)
    if (onFileSelect) {
      onFileSelect(file);
      if (inputRef.current) inputRef.current.value = '';
      return;
    }

    if (!onChange) {
      setError('Nenhum handler de upload configurado.');
      return;
    }

    setUploading(true);

    try {
      // Upload via API backend (que faz proxy para o servidor de mídia)
      const formData = new FormData();
      formData.append('file', file);
      formData.append('folder', folder);

      const response = await apiClient.post<{
        success: boolean;
        url: string;
        filename: string;
        error?: string;
      }>('/media/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.data?.url) {
        onChange?.(response.data.url);
        setError(null);
      } else {
        setError(response.data?.error || 'Erro ao enviar arquivo');
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { error?: string; detail?: string } } };
      const apiMsg = axiosErr?.response?.data?.error || axiosErr?.response?.data?.detail;
      setError(apiMsg || 'Erro ao enviar arquivo. Tente novamente.');
    } finally {
      setUploading(false);
      // Limpar input para permitir reselecionar o mesmo arquivo
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  const handleRemove = () => {
    if (disabled) return;
    onChange?.('');
    setError(null);
  };

  const handleClick = () => {
    if (disabled || uploading) return;
    inputRef.current?.click();
  };

  // Modo compacto: só botão
  if (compact) {
    return (
      <div className="inline-flex items-center gap-2">
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleClick}
          disabled={disabled || uploading}
        >
          {uploading ? (
            <Loader2 size={16} className="animate-spin mr-1" />
          ) : (
            <Upload size={16} className="mr-1" />
          )}
          {buttonLabel || 'Enviar'}
        </Button>
        {value && (
          <Button type="button" variant="ghost" size="sm" onClick={handleRemove}>
            <X size={16} />
          </Button>
        )}
        {error && <span className="text-xs text-red-500">{error}</span>}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      {description && (
        <p className="text-xs text-gray-500 dark:text-gray-400">{description}</p>
      )}

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleFileSelect}
        className="hidden"
        disabled={disabled}
      />

      {value ? (
        <div className="relative w-32 h-32 rounded-lg border-2 border-gray-200 dark:border-gray-700 overflow-hidden bg-gray-50 dark:bg-gray-800">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={value}
            alt={label}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '';
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
          {!disabled && (
            <button
              type="button"
              onClick={handleRemove}
              className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
            >
              <X size={12} />
            </button>
          )}
        </div>
      ) : (
        <div
          onClick={handleClick}
          className={`w-32 h-32 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 flex flex-col items-center justify-center cursor-pointer hover:border-blue-400 transition-colors ${
            disabled ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {uploading ? (
            <Loader2 size={24} className="text-gray-400 animate-spin" />
          ) : (
            <>
              <ImageIcon size={24} className="text-gray-400 mb-1" />
              <span className="text-xs text-gray-500">
                {buttonLabel || 'Clique para enviar'}
              </span>
            </>
          )}
        </div>
      )}

      {error && (
        <p className="text-xs text-red-500 mt-1">{error}</p>
      )}
    </div>
  );
}
