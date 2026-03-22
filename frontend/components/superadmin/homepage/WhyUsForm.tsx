'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface WhyUsData {
  id?: number;
  titulo: string;
  descricao?: string;
  icone?: string;
}

interface WhyUsFormProps {
  initial: WhyUsData;
  onSave: (data: WhyUsData) => void;
  onCancel: () => void;
  saving: boolean;
}

export function WhyUsForm({
  initial,
  onSave,
  onCancel,
  saving,
}: WhyUsFormProps) {
  const [form, setForm] = useState(initial);

  return (
    <div className="space-y-4">
      <div>
        <Label>Título</Label>
        <Input
          value={form.titulo}
          onChange={(e) => setForm((f) => ({ ...f, titulo: e.target.value }))}
          placeholder="Ex: Aumente sua produtividade"
        />
      </div>
      <div>
        <Label>Descrição (opcional)</Label>
        <textarea
          className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={form.descricao || ''}
          onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
          placeholder="Ex: Descrição detalhada do benefício"
        />
      </div>
      <div>
        <Label>Ícone (emoji)</Label>
        <Input
          value={form.icone || '✓'}
          onChange={(e) => setForm((f) => ({ ...f, icone: e.target.value }))}
          placeholder="Ex: ✓ ou ⭐"
        />
      </div>
      
      <div className="flex gap-2">
        <Button onClick={() => onSave(form)} disabled={saving}>
          Salvar
        </Button>
        <Button variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>
    </div>
  );
}
