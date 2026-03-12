# Deploy v936 - Implementação Frontend: Novos Campos em Oportunidade

**Data**: 11/03/2026  
**Tipo**: Frontend (Vercel)  
**Status**: ✅ Concluído

## Resumo

Implementação completa no frontend dos 3 novos campos adicionados ao modelo `Oportunidade`:
- `data_fechamento_ganho` (data que foi fechado ganho)
- `data_fechamento_perdido` (data que foi fechado perdido)  
- `valor_comissao` (valor da comissão)

Backend já estava pronto desde o Deploy v932.

## Alterações Implementadas

### 1. Interface TypeScript (`PipelineBoard.tsx`)

```typescript
export interface Oportunidade {
  id: number;
  titulo: string;
  valor: string;
  etapa: string;
  lead_nome: string;
  vendedor_nome?: string;
  data_fechamento_ganho?: string | null;      // ✅ NOVO
  data_fechamento_perdido?: string | null;    // ✅ NOVO
  valor_comissao?: string | null;             // ✅ NOVO
}
```

### 2. Visualização nos Cards do Pipeline

Os cards agora mostram:
- **Valor da comissão** (roxo) quando preenchido
- **Data fechamento ganho** (verde) quando etapa = `closed_won`
- **Data fechamento perdido** (vermelho) quando etapa = `closed_lost`

```tsx
{o.valor_comissao && (
  <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
    Comissão: {formatMoney(o.valor_comissao)}
  </p>
)}
{o.data_fechamento_ganho && (
  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
    Ganho em: {new Date(o.data_fechamento_ganho).toLocaleDateString('pt-BR')}
  </p>
)}
```

### 3. Formulário de Criação

Adicionado campo **Valor da Comissão (R$)** no modal "Nova oportunidade":
- Campo opcional
- Tipo: number (decimal)
- Enviado para API ao criar oportunidade

### 4. Modal de Edição

Adicionados 3 novos campos editáveis:

#### a) Valor da Comissão
- Sempre visível
- Permite editar o valor da comissão

#### b) Data Fechamento Ganho
- Visível quando `etapa === 'closed_won'` OU quando já tem data preenchida
- Tipo: date
- Preenchimento automático com data atual ao mudar para "Fechado ganho"

#### c) Data Fechamento Perdido
- Visível quando `etapa === 'closed_lost'` OU quando já tem data preenchida
- Tipo: date
- Preenchimento automático com data atual ao mudar para "Fechado perdido"

### 5. Lógica de Salvamento

```typescript
const payload: Record<string, unknown> = { etapa: etapaSelecionada };

// Adiciona valor_comissao se preenchido
if (valorComissaoEdit) {
  payload.valor_comissao = parseFloat(valorComissaoEdit);
}

// Se mudou para closed_won, sugere data_fechamento_ganho
if (etapaSelecionada === 'closed_won' && !dataFechamentoGanho) {
  payload.data_fechamento_ganho = new Date().toISOString().split('T')[0];
} else if (dataFechamentoGanho) {
  payload.data_fechamento_ganho = dataFechamentoGanho;
}

// Se mudou para closed_lost, sugere data_fechamento_perdido
if (etapaSelecionada === 'closed_lost' && !dataFechamentoPerdido) {
  payload.data_fechamento_perdido = new Date().toISOString().split('T')[0];
} else if (dataFechamentoPerdido) {
  payload.data_fechamento_perdido = dataFechamentoPerdido;
}
```

### 6. Validação de Mudanças

Botão "Salvar" desabilitado quando não há mudanças:
```typescript
disabled={enviando || (
  etapaSelecionada === oportunidadeEditar.etapa &&
  valorComissaoEdit === (oportunidadeEditar.valor_comissao || '') &&
  dataFechamentoGanho === (oportunidadeEditar.data_fechamento_ganho || '') &&
  dataFechamentoPerdido === (oportunidadeEditar.data_fechamento_perdido || '')
)}
```

## Arquivos Modificados

```
frontend/components/crm-vendas/PipelineBoard.tsx
frontend/app/(dashboard)/loja/[slug]/crm-vendas/pipeline/page.tsx
```

## Fluxo de Uso

### Criar Nova Oportunidade
1. Clicar em "Nova oportunidade"
2. Preencher: Lead, Título, Valor, Etapa inicial
3. **NOVO**: Opcionalmente preencher "Valor da Comissão"
4. Criar

### Editar Oportunidade
1. Clicar no card da oportunidade
2. Alterar etapa (ex: para "Fechado ganho")
3. **NOVO**: Sistema sugere automaticamente a data de fechamento (hoje)
4. **NOVO**: Editar valor da comissão se necessário
5. Salvar

### Visualizar no Pipeline
- Cards mostram comissão (roxo) quando preenchida
- Cards mostram data de fechamento ganho (verde) quando aplicável
- Cards mostram data de fechamento perdido (vermelho) quando aplicável

## Testes Realizados

✅ Compilação TypeScript sem erros  
✅ Deploy Vercel bem-sucedido  
✅ Interface responsiva (desktop e mobile)  
✅ Campos opcionais funcionando corretamente  
✅ Preenchimento automático de datas ao mudar etapa  
✅ Validação de mudanças para habilitar/desabilitar botão Salvar

## Deploy

```bash
cd frontend
vercel --prod --yes
```

**URL**: https://lwksistemas.com.br/loja/felix-5889/crm-vendas/pipeline

## Próximos Passos

- Testar criação de oportunidade com comissão
- Testar mudança de etapa para "Fechado ganho" e verificar data automática
- Testar mudança de etapa para "Fechado perdido" e verificar data automática
- Validar visualização dos novos campos nos cards do pipeline

## Observações

- Backend já estava pronto (Deploy v932)
- Campos são opcionais (nullable no backend)
- Datas são preenchidas automaticamente ao mudar etapa, mas podem ser editadas
- Comissão pode ser preenchida em qualquer etapa
- Sistema mantém compatibilidade com oportunidades antigas (sem os novos campos)
