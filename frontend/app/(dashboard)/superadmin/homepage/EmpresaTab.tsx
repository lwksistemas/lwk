'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Save } from 'lucide-react';
import { EmpresaFormData } from './types';

interface EmpresaTabProps {
  empresaForm: EmpresaFormData;
  setEmpresaForm: React.Dispatch<React.SetStateAction<EmpresaFormData>>;
  onSave: () => void;
  saving: boolean;
}

export function EmpresaTab({ empresaForm, setEmpresaForm, onSave, saving }: EmpresaTabProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Dados da Empresa</CardTitle>
        <CardDescription>
          Informações exibidas no rodapé do site e no botão flutuante do WhatsApp
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label>Nome da Empresa</Label>
            <Input
              value={empresaForm.nome_empresa}
              onChange={(e) => setEmpresaForm((f) => ({ ...f, nome_empresa: e.target.value }))}
              placeholder="LWK Sistemas"
            />
          </div>
          <div>
            <Label>CNPJ</Label>
            <Input
              value={empresaForm.cnpj}
              onChange={(e) => setEmpresaForm((f) => ({ ...f, cnpj: e.target.value }))}
              placeholder="00.000.000/0001-00"
            />
          </div>
          <div className="md:col-span-2">
            <Label>Endereço Completo</Label>
            <Input
              value={empresaForm.endereco}
              onChange={(e) => setEmpresaForm((f) => ({ ...f, endereco: e.target.value }))}
              placeholder="Rua Exemplo, 123 — Centro, Cidade/UF — CEP 00000-000"
            />
          </div>
          <div>
            <Label>Telefone WhatsApp</Label>
            <Input
              value={empresaForm.telefone_whatsapp}
              onChange={(e) => setEmpresaForm((f) => ({ ...f, telefone_whatsapp: e.target.value }))}
              placeholder="5511999999999 (código país + DDD + número)"
            />
            <p className="text-xs text-gray-500 mt-1">
              Formato: 55 + DDD + número (sem espaços ou traços). Ex: 5511999999999
            </p>
          </div>
          <div>
            <Label>Email de Contato</Label>
            <Input
              type="email"
              value={empresaForm.email_contato}
              onChange={(e) => setEmpresaForm((f) => ({ ...f, email_contato: e.target.value }))}
              placeholder="contato@lwksistemas.com.br"
            />
          </div>
          <div className="md:col-span-2">
            <Label>Mensagem Padrão do WhatsApp</Label>
            <Input
              value={empresaForm.mensagem_whatsapp}
              onChange={(e) => setEmpresaForm((f) => ({ ...f, mensagem_whatsapp: e.target.value }))}
              placeholder="Olá! Gostaria de saber mais sobre o LWK Sistemas."
            />
            <p className="text-xs text-gray-500 mt-1">
              Texto pré-preenchido quando o visitante clica no botão do WhatsApp
            </p>
          </div>
        </div>

        <div className="mt-4 p-4 bg-stone-100 dark:bg-zinc-900/50 rounded-lg border border-stone-200 dark:border-zinc-700">
          <p className="text-sm text-stone-700 dark:text-stone-300">
            💡 O <strong>botão flutuante do WhatsApp</strong> só aparece no site quando o número estiver preenchido.
            O <strong>CNPJ e endereço</strong> aparecem no rodapé da homepage.
          </p>
        </div>

        <Button onClick={onSave} disabled={saving}>
          <Save className="w-4 h-4 mr-2" />
          {saving ? 'Salvando...' : 'Salvar Dados da Empresa'}
        </Button>
      </CardContent>
    </Card>
  );
}
