'use client';

import { IconRenderer } from '@/components/shared/IconRenderer';
import Image from 'next/image';

interface HeroPreviewData {
  titulo: string;
  subtitulo: string;
  botao_texto: string;
  botao_principal_ativo?: boolean;
  imagem?: string;
}

interface FuncionalidadePreviewData {
  titulo: string;
  descricao: string;
  icone?: string;
  imagem?: string;
}

interface ModuloPreviewData {
  nome: string;
  descricao: string;
  slug?: string;
  icone?: string;
  imagem?: string;
}

interface HomepagePreviewProps {
  type: 'hero' | 'funcionalidade' | 'modulo';
  data: HeroPreviewData | FuncionalidadePreviewData | ModuloPreviewData;
}

export function HomepagePreview({ type, data }: HomepagePreviewProps) {
  if (type === 'hero') {
    const heroData = data as HeroPreviewData;
    return (
      <div className="border-2 border-blue-200 rounded-lg p-6 bg-gradient-to-br from-blue-50 to-blue-100">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
          <span className="text-xs font-medium text-blue-600 uppercase">Preview</span>
        </div>
        
        <div className="bg-white rounded-lg p-6 shadow-sm">
          {heroData.imagem && (
            <div className="mb-4 aspect-video relative rounded-lg overflow-hidden">
              <Image
                src={heroData.imagem}
                alt={heroData.titulo}
                fill
                className="object-cover"
              />
            </div>
          )}
          <h1 className="text-2xl font-bold text-gray-900 mb-3">
            {heroData.titulo || 'Título do Hero'}
          </h1>
          <p className="text-gray-600 mb-4">
            {heroData.subtitulo || 'Subtítulo do Hero'}
          </p>
          <div className="flex gap-3">
            {heroData.botao_principal_ativo !== false && (
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium">
                {heroData.botao_texto || 'Testar Gratuitamente'}
              </button>
            )}
            <button className="bg-white text-blue-600 border-2 border-blue-600 px-4 py-2 rounded-lg text-sm font-medium">
              Ver Demonstração
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (type === 'funcionalidade') {
    const funcData = data as FuncionalidadePreviewData;
    return (
      <div className="border-2 border-green-200 rounded-lg p-6 bg-gradient-to-br from-green-50 to-green-100">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse" />
          <span className="text-xs font-medium text-green-600 uppercase">Preview</span>
        </div>
        
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <div className="mb-3">
            <IconRenderer
              icone={funcData.icone}
              imagem={funcData.imagem}
              alt={funcData.titulo}
              size="md"
            />
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-2">
            {funcData.titulo || 'Título da Funcionalidade'}
          </h3>
          <p className="text-gray-600 text-sm">
            {funcData.descricao || 'Descrição da funcionalidade'}
          </p>
        </div>
      </div>
    );
  }

  if (type === 'modulo') {
    const modData = data as ModuloPreviewData;
    return (
      <div className="border-2 border-purple-200 rounded-lg p-6 bg-gradient-to-br from-purple-50 to-purple-100">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-2 h-2 bg-purple-600 rounded-full animate-pulse" />
          <span className="text-xs font-medium text-purple-600 uppercase">Preview</span>
        </div>
        
        <div className="bg-white rounded-lg p-6 shadow-sm border-2 border-transparent hover:border-blue-500 transition-all">
          <div className="mb-3">
            <IconRenderer
              icone={modData.icone}
              imagem={modData.imagem}
              alt={modData.nome}
              size="md"
            />
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-2">
            {modData.nome || 'Nome do Módulo'}
          </h3>
          <p className="text-gray-600 text-sm mb-3">
            {modData.descricao || 'Descrição do módulo'}
          </p>
          {modData.slug && (
            <span className="inline-block text-blue-600 font-medium text-sm">
              Acessar →
            </span>
          )}
        </div>
      </div>
    );
  }

  return null;
}
