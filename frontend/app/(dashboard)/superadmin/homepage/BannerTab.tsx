'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Save } from 'lucide-react';
import { FONTES_HOME, TAMANHOS_HOME } from '@/lib/fontes-opcoes';
import { BOTOES_HOME, LEGENDA_BOTOES } from '@/lib/botoes-home';
import type { HeroData } from './types';

interface BannerTabProps {
  heroForm: HeroData;
  setHeroForm: React.Dispatch<React.SetStateAction<HeroData>>;
  onSave: () => void;
  saving: boolean;
}

export function BannerTab({ heroForm, setHeroForm, onSave, saving }: BannerTabProps) {
  const set = (campo: keyof HeroData, valor: HeroData[keyof HeroData]) => {
    setHeroForm((atual) => ({ ...atual, [campo]: valor }));
  };

  return (
    <>
    <Card>
      <CardHeader>
        <CardTitle>Banner da página inicial</CardTitle>
        <CardDescription>
          Etiqueta, título, texto, tipo e tamanho da letra, e os dois botões do topo. Inter e Normal são a letra da foto atual. As telas do notebook ficam em Imagens
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
              placeholder="Soluções de software"
            />
          </div>
          <div className="md:col-span-2">
            <Label>Segunda linha do título (azul)</Label>
            <Input
              value={heroForm.titulo_destaque || ''}
              onChange={(e) => set('titulo_destaque', e.target.value)}
              placeholder="para sua empresa."
            />
          </div>
          <div>
            <Label>Tipo da letra</Label>
            <select
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-sm"
              value={heroForm.fonte_familia || 'inter'}
              onChange={(e) => set('fonte_familia', e.target.value)}
            >
              {FONTES_HOME.map((fonte) => (
                <option key={fonte.id} value={fonte.id}>{fonte.rotulo}</option>
              ))}
            </select>
          </div>
          <div>
            <Label>Tamanho da letra</Label>
            <select
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-sm"
              value={heroForm.fonte_tamanho || 'normal'}
              onChange={(e) => set('fonte_tamanho', e.target.value)}
            >
              {TAMANHOS_HOME.map((tamanho) => (
                <option key={tamanho.id} value={tamanho.id}>{tamanho.rotulo}</option>
              ))}
            </select>
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
    <Card>
      <CardHeader>
        <CardTitle>Nomes dos botões</CardTitle>
        <CardDescription>
          Menu, cartões, planos e o formulário. Os dois botões do banner ficam nos campos acima.
          O texto vazio volta ao nome padrão.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {LEGENDA_BOTOES.map((item) => (
            <div key={item.id}>
              <Label>{item.onde}</Label>
              <Input
                value={heroForm.rotulos_botoes?.[item.id] ?? BOTOES_HOME[item.id]}
                onChange={(e) => set('rotulos_botoes', {
                  ...BOTOES_HOME,
                  ...(heroForm.rotulos_botoes || {}),
                  [item.id]: e.target.value,
                })}
              />
            </div>
          ))}
        </div>
        <Button onClick={onSave} disabled={saving || !heroForm.titulo.trim()}>
          <Save className="mr-2 h-4 w-4" />
          Salvar botões
        </Button>
      </CardContent>
    </Card>
    </>
  );
}
