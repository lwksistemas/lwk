# INTEGRAÇÃO: Botão de Assinatura Digital nos Formulários

## Como Adicionar o Botão nos Formulários Existentes

### 1. Proposta - ModalPropostaForm.tsx

Adicione a prop no componente ModalPropostaForm:

```tsx
// frontend/components/crm-vendas/modals/ModalPropostaForm.tsx

interface ModalPropostaFormProps {
  // ... props existentes ...
  propostaId?: number; // ADICIONAR
  statusAssinatura?: string; // ADICIONAR
}

export default function ModalPropostaForm({
  // ... props existentes ...
  propostaId, // ADICIONAR
  statusAssinatura, // ADICIONAR
}: ModalPropostaFormProps) {
  return (
    <div className="...">
      {/* ... conteúdo existente ... */}
      <div className="p-4">
        <PropostaFormContent
          // ... props existentes ...
          propostaId={propostaId} // ADICIONAR
          statusAssinatura={statusAssinatura} // ADICIONAR
        />
      </div>
    </div>
  );
}
```

### 2. PropostaFormContent.tsx

Adicione o botão de assinatura após os botões Salvar/Cancelar:

```tsx
// frontend/components/crm-vendas/PropostaFormContent.tsx

import BotaoAssinaturaDigital from './BotaoAssinaturaDigital';

export interface PropostaFormContentProps {
  // ... props existentes ...
  propostaId?: number; // ADICIONAR
  statusAssinatura?: string; // ADICIONAR
}

export default function PropostaFormContent({
  // ... props existentes ...
  propostaId, // ADICIONAR
  statusAssinatura, // ADICIONAR
}: PropostaFormContentProps) {
  return (
    <form onSubmit={onSubmit} className={formClass}>
      {/* ... campos existentes ... */}
      
      {/* Botões existentes */}
      <div className="flex gap-2 pt-2 md:col-span-2">
        {showCancel && onCancel && (
          <button type="button" onClick={() => !enviando && onCancel()} className="...">
            Cancelar
          </button>
        )}
        <button type="submit" disabled={enviando} className="...">
          {enviando ? 'Salvando...' : 'Salvar'}
        </button>
      </div>
      
      {/* ADICIONAR: Botão de Assinatura Digital */}
      {isEdit && propostaId && (
        <div className="md:col-span-2 pt-4 border-t border-gray-200 dark:border-gray-700">
          <BotaoAssinaturaDigital
            documentoId={propostaId}
            tipoDocumento="proposta"
            statusAssinatura={statusAssinatura}
            leadEmail={leadInfo?.email}
            onSucesso={() => {
              // Recarregar dados ou fechar modal
              if (onCancel) {
                onCancel();
              }
            }}
          />
        </div>
      )}
    </form>
  );
}
```

### 3. Página de Propostas - Passar Props

Na página que usa o ModalPropostaForm, passe os dados da proposta:

```tsx
// Exemplo: frontend/app/(dashboard)/loja/[slug]/crm-vendas/propostas/page.tsx

const [propostaSelecionada, setPropostaSelecionada] = useState<Proposta | null>(null);

// Ao abrir modal de edição:
<ModalPropostaForm
  title="Editar Proposta"
  form={form}
  // ... outras props ...
  isEdit={true}
  propostaId={propostaSelecionada?.id} // ADICIONAR
  statusAssinatura={propostaSelecionada?.status_assinatura} // ADICIONAR
  onClose={() => {
    setModalAberto(false);
    setPropostaSelecionada(null);
  }}
/>
```

### 4. Contrato - ModalContratoForm.tsx

Mesma lógica para contratos:

```tsx
// frontend/components/crm-vendas/modals/ModalContratoForm.tsx

interface ModalContratoFormProps {
  // ... props existentes ...
  contratoId?: number; // ADICIONAR
  statusAssinatura?: string; // ADICIONAR
}

// No componente:
<ContratoFormContent
  // ... props existentes ...
  contratoId={contratoId}
  statusAssinatura={statusAssinatura}
/>
```

### 5. ContratoFormContent.tsx

```tsx
// frontend/components/crm-vendas/ContratoFormContent.tsx

import BotaoAssinaturaDigital from './BotaoAssinaturaDigital';

export interface ContratoFormContentProps {
  // ... props existentes ...
  contratoId?: number; // ADICIONAR
  statusAssinatura?: string; // ADICIONAR
}

export default function ContratoFormContent({
  // ... props existentes ...
  contratoId,
  statusAssinatura,
}: ContratoFormContentProps) {
  return (
    <form onSubmit={onSubmit} className={formClass}>
      {/* ... campos existentes ... */}
      
      {/* Botões existentes */}
      <div className="flex gap-2 pt-2 md:col-span-2">
        {/* ... botões Salvar/Cancelar ... */}
      </div>
      
      {/* ADICIONAR: Botão de Assinatura Digital */}
      {isEdit && contratoId && (
        <div className="md:col-span-2 pt-4 border-t border-gray-200 dark:border-gray-700">
          <BotaoAssinaturaDigital
            documentoId={contratoId}
            tipoDocumento="contrato"
            statusAssinatura={statusAssinatura}
            leadEmail={leadInfo?.email}
            onSucesso={() => {
              if (onCancel) {
                onCancel();
              }
            }}
          />
        </div>
      )}
    </form>
  );
}
```

## Badge de Status na Listagem

Para mostrar o status de assinatura nas listagens de propostas/contratos:

```tsx
// Componente de Badge
function BadgeStatusAssinatura({ status }: { status?: string }) {
  if (!status || status === 'rascunho') return null;
  
  const config = {
    aguardando_cliente: {
      bg: 'bg-yellow-100 dark:bg-yellow-900/20',
      text: 'text-yellow-700 dark:text-yellow-300',
      label: 'Aguardando Cliente',
    },
    aguardando_vendedor: {
      bg: 'bg-blue-100 dark:bg-blue-900/20',
      text: 'text-blue-700 dark:text-blue-300',
      label: 'Aguardando Vendedor',
    },
    concluido: {
      bg: 'bg-green-100 dark:bg-green-900/20',
      text: 'text-green-700 dark:text-green-300',
      label: 'Assinado',
    },
    cancelado: {
      bg: 'bg-gray-100 dark:bg-gray-900/20',
      text: 'text-gray-700 dark:text-gray-300',
      label: 'Cancelado',
    },
  };
  
  const { bg, text, label } = config[status as keyof typeof config] || config.rascunho;
  
  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${bg} ${text}`}>
      {label}
    </span>
  );
}

// Uso na listagem:
<div className="flex items-center gap-2">
  <span>{proposta.titulo}</span>
  <BadgeStatusAssinatura status={proposta.status_assinatura} />
</div>
```

## Atualizar Interface de Proposta/Contrato

Adicione o campo `status_assinatura` nas interfaces TypeScript:

```tsx
// frontend/types/crm.ts (ou onde estiverem as interfaces)

export interface Proposta {
  id: number;
  oportunidade: number;
  oportunidade_titulo: string;
  lead_nome: string;
  titulo: string;
  conteudo: string;
  valor_total: string;
  status: string;
  status_assinatura: string; // ADICIONAR
  data_envio: string | null;
  data_resposta: string | null;
  observacoes: string;
  nome_vendedor_assinatura: string;
  nome_cliente_assinatura: string;
  created_at: string;
  updated_at: string;
}

export interface Contrato {
  id: number;
  oportunidade: number;
  oportunidade_titulo: string;
  lead_nome: string;
  numero: string;
  titulo: string;
  conteudo: string;
  valor_total: string;
  status: string;
  status_assinatura: string; // ADICIONAR
  data_envio: string | null;
  data_assinatura: string | null;
  observacoes: string;
  nome_vendedor_assinatura: string;
  nome_cliente_assinatura: string;
  created_at: string;
  updated_at: string;
}
```

## Exemplo Completo de Uso

```tsx
// Página de Propostas
'use client';

import { useState, useEffect } from 'react';
import ModalPropostaForm from '@/components/crm-vendas/modals/ModalPropostaForm';
import BadgeStatusAssinatura from '@/components/crm-vendas/BadgeStatusAssinatura';

export default function PropostasPage() {
  const [propostas, setPropostas] = useState<Proposta[]>([]);
  const [modalAberto, setModalAberto] = useState(false);
  const [propostaSelecionada, setPropostaSelecionada] = useState<Proposta | null>(null);
  
  const carregarPropostas = async () => {
    const res = await fetch('/api/crm-vendas/propostas/');
    const data = await res.json();
    setPropostas(data.results || data);
  };
  
  const editarProposta = (proposta: Proposta) => {
    setPropostaSelecionada(proposta);
    setModalAberto(true);
  };
  
  return (
    <div>
      {/* Listagem */}
      <div className="space-y-2">
        {propostas.map((proposta) => (
          <div key={proposta.id} className="p-4 bg-white rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold">{proposta.titulo}</h3>
                <p className="text-sm text-gray-600">{proposta.lead_nome}</p>
              </div>
              <div className="flex items-center gap-2">
                <BadgeStatusAssinatura status={proposta.status_assinatura} />
                <button onClick={() => editarProposta(proposta)}>
                  Editar
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Modal */}
      {modalAberto && (
        <ModalPropostaForm
          title={propostaSelecionada ? 'Editar Proposta' : 'Nova Proposta'}
          isEdit={!!propostaSelecionada}
          propostaId={propostaSelecionada?.id}
          statusAssinatura={propostaSelecionada?.status_assinatura}
          // ... outras props ...
          onClose={() => {
            setModalAberto(false);
            setPropostaSelecionada(null);
            carregarPropostas(); // Recarregar lista
          }}
        />
      )}
    </div>
  );
}
```

## Observações Importantes

1. **Validação de Email**: O botão só fica habilitado se o lead tiver email cadastrado
2. **Status Visual**: Badge mostra o status atual da assinatura
3. **Feedback**: Mensagens de sucesso/erro são exibidas automaticamente
4. **Recarregamento**: Após enviar para assinatura, recarregue os dados para atualizar o status
5. **Modo Edição**: Botão só aparece em modo de edição (isEdit=true)

## Testes Recomendados

- [ ] Criar proposta sem email do lead → Botão desabilitado
- [ ] Adicionar email ao lead → Botão habilitado
- [ ] Enviar para assinatura → Verificar feedback de sucesso
- [ ] Reabrir proposta → Verificar badge de status
- [ ] Tentar enviar novamente → Botão não aparece (mostra status)
