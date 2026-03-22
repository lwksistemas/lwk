'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ImageUpload } from '@/components/ImageUpload';
import { HomepagePreview } from '@/components/superadmin/HomepagePreview';

interface FuncionalidadeData {
  id?: number;
  titulo: string;
  descricao: string;
  icone: string;
  imagem?: string;
}

interface FuncionalidadeFormProps {
  initial: FuncionalidadeData;
  onSave: (data: FuncionalidadeData) => void;
  onCancel: () => void;
  saving: boolean;
}

export function FuncionalidadeForm({
  initial,
  onSave,
  onCancel,
  saving,
}: FuncionalidadeFormProps) {
  const [form, setForm] = useState(initial);

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <div className="space-y-4">
        <div>
          <Label>Título</Label>
          <Input
            value={form.titulo}
            onChange={(e) => setForm((f) => ({ ...f, titulo: e.target.value }))}
            placeholder="Ex: CRM de Clientes"
          />
        </div>
        <div>
          <Label>Descrição</Label>
          <textarea
            className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={form.descricao}
            onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
            placeholder="Ex: Gestão completa de clientes"
          />
        </div>
        <div>
          <Label>Ícone (emoji ou nome: Users, BarChart, etc.)</Label>
          <Input
            value={form.icone}
            onChange={(e) => setForm((f) => ({ ...f, icone: e.target.value }))}
            placeholder="Ex: 👥 ou Users"
          />
        </div>
        
        <ImageUpload
          label="Imagem da Funcionalidade"
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
        <HomepagePreview type="funcionalidade" data={form} />
      </div>
    </div>
  );
}
