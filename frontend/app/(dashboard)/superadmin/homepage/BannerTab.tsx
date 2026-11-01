'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Save } from 'lucide-react';
import type { HeroData } from './types';

interface BannerTabProps {
  heroForm: HeroData;
  setHeroForm: React.Dispatch<React.SetStateAction<HeroData>>;
  onSave: () => void;
  saving: boolean;
}

export function BannerTab({ heroForm, setHeroForm, onSave, saving }: BannerTabProps) {
  const set = (campo: keyof HeroData, valor: string | boolean | number) => {
    setHeroForm((atual) => ({ ...atual, [campo]: valor }));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Banner da página inicial</CardTitle>
        <CardDescription>
          Etiqueta, título, texto e os dois botões do topo. As telas do notebook ficam em Imagens
          (o título de cada imagem vira a etiqueta, como “CRM Vendas”). Os quatro cartões de baixo
          são as Funcionalidades.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <Label>Etiqueta</Label>
            <Input value={heroForm.selo || ''} onChange={(e) => set('selo', e.target.value)} placeholder="Software House" />
          </div>
          <div className="md:col-span-2">
            <Label>Título</Label>
            <Input
              value={heroForm.titulo}
              onChange={(e) => set('titulo', e.target.value)}
              placeholder="Soluções de software para o seu negócio."
            />
          </div>
          <div className="md:col-span-2">
            <Label>Texto</Label>
            <textarea
              value={heroForm.subtitulo}
              onChange={(e) => set('subtitulo', e.target.value)}
              rows={4}
              className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm"
              placeholder="Desenvolvemos sistemas e soluções personalizadas..."
            />
          </div>
          <div>
            <Label>Botão principal</Label>
            <Input
              value={heroForm.botao_texto}
              onChange={(e) => set('botao_texto', e.target.value)}
              placeholder="Conheça nossas soluções"
            />
          </div>
          <div>
            <Label>Link do botão principal</Label>
            <Input
              value={heroForm.botao_url || ''}
              onChange={(e) => set('botao_url', e.target.value)}
              placeholder="#solucoes"
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={heroForm.botao_principal_ativo !== false}
              onChange={(e) => set('botao_principal_ativo', e.target.checked)}
            />
            Mostrar botão principal
          </label>
          <div />
          <div>
            <Label>Segundo botão</Label>
            <Input
              value={heroForm.botao_secundario_texto || ''}
              onChange={(e) => set('botao_secundario_texto', e.target.value)}
              placeholder="Solicite uma demonstração"
            />
          </div>
          <div>
            <Label>Link do segundo botão</Label>
            <Input
              value={heroForm.botao_secundario_url || ''}
              onChange={(e) => set('botao_secundario_url', e.target.value)}
              placeholder="/demonstracao"
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={heroForm.botao_secundario_ativo !== false}
              onChange={(e) => set('botao_secundario_ativo', e.target.checked)}
            />
            Mostrar segundo botão
          </label>
          <div>
            <Label>Troca das telas do notebook (segundos)</Label>
            <Input
              type="number"
              min={3}
              max={30}
              value={heroForm.intervalo_carrossel ?? 5}
              onChange={(e) => set('intervalo_carrossel', Number(e.target.value))}
            />
          </div>
        </div>
        <Button onClick={onSave} disabled={saving || !heroForm.titulo.trim()}>
          <Save className="mr-2 h-4 w-4" />
          Salvar banner
        </Button>
      </CardContent>
    </Card>
  );
}
