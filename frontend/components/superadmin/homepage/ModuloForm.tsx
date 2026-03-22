'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ImageUpload } from '@/components/ImageUpload';
import { HomepagePreview } from '@/components/superadmin/HomepagePreview';

interface ModuloData {
  id?: number;
  nome: string;
  descricao: string;
  slug: string;
  icone: string;
  imagem?: string;
}

interface ModuloFormProps {
  initial: ModuloData;
  onSave: (data: ModuloData) => void;
  onCancel: () => void;
  saving: boolean;
}

export function ModuloForm({
  initial,
  onSave,
  onCancel,
  saving,
}: ModuloFormProps) {
  const [form, setForm] = useState(initial);

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <div className="space-y-4">
        <div>
          <Label>Nome</Label>
          <Input
            value={form.nome}
            onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
            placeholder="Ex: CRM Vendas"
          />
        </div>
        <div>
          <Label>Descrição</Label>
          <textarea
            className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={form.descricao}
            onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
            placeholder="Ex: Gestão de vendas e leads"
          />
        </div>
        <div>
          <Label>Slug (para link /loja/slug/login)</Label>
          <Input
            value={form.slug}
            onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value }))}
            placeholder="Ex: crm-vendas"
          />
        </div>
        <div>
          <Label>Ícone (emoji ou nome)</Label>
          <Input
            value={form.icone}
            onChange={(e) => setForm((f) => ({ ...f, icone: e.target.value }))}
            placeholder="Ex: 📊"
          />
        </div>
        
        <ImageUpload
          label="Imagem do Módulo"
          description="Imagem exibida no card (opcional, substitui o ícone)"
          value={form.imagem || ''}
          onChange={(url) => setForm((f) => ({ ...f, imagem: url }))}
          maxSize={2}
          aspectRatio="1:1"
        />
        
        <div className="flex gap-2">
          <Button onClick={() => onSave(form)} disabled={saving}>
            Salvar
          </Button>
          <Button variant="outline" onClick={onCancel}>
            Cancelar
          </Button>
        </div>
      </div>
      
      {/* Preview */}
      <div className="sticky top-6">
        <HomepagePreview type="modulo" data={form} />
      </div>
    </div>
  );
}
