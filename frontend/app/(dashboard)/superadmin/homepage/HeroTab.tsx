'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Save } from 'lucide-react';
import { HomepagePreview } from '@/components/superadmin/HomepagePreview';
import { HeroData } from './types';

interface HeroTabProps {
  heroForm: HeroData;
  setHeroForm: React.Dispatch<React.SetStateAction<HeroData>>;
  onSave: () => void;
  saving: boolean;
}

export function HeroTab({ heroForm, setHeroForm, onSave, saving }: HeroTabProps) {
  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Textos do banner</CardTitle>
          <CardDescription>
            Título, subtítulo e botão exibidos sobre o fundo (as imagens de fundo ficam na aba Imagens)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Título</Label>
            <Input
              value={heroForm.titulo}
              onChange={(e) => setHeroForm((f) => ({ ...f, titulo: e.target.value }))}
              placeholder="Ex: LWK SISTEMAS"
            />
          </div>
          <div>
            <Label>Subtítulo</Label>
            <textarea
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={heroForm.subtitulo}
              onChange={(e) => setHeroForm((f) => ({ ...f, subtitulo: e.target.value }))}
              placeholder="Ex: Gestão de Lojas"
            />
          </div>
          <div>
            <Label>Texto do botão</Label>
            <Input
              value={heroForm.botao_texto}
              onChange={(e) => setHeroForm((f) => ({ ...f, botao_texto: e.target.value }))}
              placeholder="Ex: Testar grátis"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="botao_principal_ativo"
              checked={heroForm.botao_principal_ativo !== false}
              onChange={(e) => setHeroForm((f) => ({ ...f, botao_principal_ativo: e.target.checked }))}
              className="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="botao_principal_ativo" className="cursor-pointer font-normal">
              Exibir botão &quot;Testar grátis&quot; na homepage
            </Label>
          </div>
          <Button onClick={onSave} disabled={saving}>
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Salvando...' : 'Salvar Hero'}
          </Button>
        </CardContent>
      </Card>

      <div className="sticky top-6">
        <HomepagePreview type="hero" data={heroForm} />
      </div>
    </div>
  );
}
