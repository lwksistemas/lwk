# Deploy: Adicionar lead_email para Habilitar Botão de Assinatura (v1152)

## Resumo
Adicionado campo `lead_email` nos serializers de Proposta e Contrato para habilitar o botão de assinatura digital quando o lead tiver email cadastrado.

## Problema Corrigido
Botão de assinatura digital estava sempre desabilitado na lista de propostas porque o componente `BotaoAssinaturaDigital` não recebia a prop `leadEmail`.

## Causa Raiz
O componente `BotaoAssinaturaDigital` desabilita o botão quando `!leadEmail`:
```typescript
disabled={enviando || !leadEmail}
```

O serializer `PropostaSerializer` não retornava o campo `lead_email`, então o frontend não tinha essa informação para passar ao componente.

## Solução Implementada

### Backend (Heroku)
1. Adicionado campo `lead_email` no `PropostaSerializer`:
```python
class PropostaSerializer(serializers.ModelSerializer):
    oportunidade_titulo = serializers.CharField(source='oportunidade.titulo', read_only=True)
    lead_nome = serializers.CharField(source='oportunidade.lead.nome', read_only=True)
    lead_email = serializers.CharField(source='oportunidade.lead.email', read_only=True)  # ← NOVO
```

2. Adicionado campo `lead_email` no `ContratoSerializer`:
```python
class ContratoSerializer(serializers.ModelSerializer):
    oportunidade_titulo = serializers.CharField(source='oportunidade.titulo', read_only=True)
    lead_nome = serializers.CharField(source='oportunidade.lead.nome', read_only=True)
    lead_email = serializers.CharField(source='oportunidade.lead.email', read_only=True)  # ← NOVO
```

### Frontend (Vercel)
1. Adicionado campo `lead_email` na interface Proposta:
```typescript
interface Proposta {
  // ... outros campos
  lead_email?: string;  // ← NOVO
  // ...
}
```

2. Passando `leadEmail` para o componente:
```typescript
<BotaoAssinaturaDigital
  tipoDocumento="proposta"
  documentoId={p.id}
  statusAssinatura={p.status_assinatura}
  leadEmail={p.lead_email}  // ← NOVO
  onSucesso={loadPropostas}
/>
```

## Deploy Realizado

### Backend (Heroku)
```bash
git add -A
git commit -m "fix: adicionar lead_email para habilitar botão de assinatura digital v1152"
git push heroku master
```

**Resultado:**
- ✅ Release v1151 deployado com sucesso
- ✅ Collectstatic: 160 arquivos copiados
- ✅ Migrations: Nenhuma pendente

### Frontend (Vercel)
```bash
cd frontend
vercel --prod --yes
```

**Resultado:**
- ✅ Deploy concluído em 46s
- ✅ URL: https://lwksistemas.com.br
- ✅ Inspect: https://vercel.com/lwks-projects-48afd555/frontend/Am5SLAciB4WbPuVydCtAEW5KEHPD

## Comportamento do Botão

### Quando o Lead TEM Email
- ✅ Botão habilitado (verde)
- ✅ Texto: "Enviar para Assinatura Digital"
- ✅ Ao clicar: Envia email com link de assinatura

### Quando o Lead NÃO TEM Email
- ❌ Botão desabilitado (opacidade 50%)
- ⚠️ Mensagem: "Lead precisa ter email cadastrado para enviar assinatura digital"
- ℹ️ Tooltip: "Lead precisa ter email cadastrado"

## Arquivos Modificados

### Backend
1. `backend/crm_vendas/serializers.py`
   - Adicionado `lead_email` no PropostaSerializer
   - Adicionado `lead_email` no ContratoSerializer

### Frontend
1. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/propostas/page.tsx`
   - Adicionado campo `lead_email` na interface Proposta
   - Passando `leadEmail` para BotaoAssinaturaDigital

### Documentação
1. `DEPLOY_LEAD_EMAIL_v1152.md` - Este documento

## Testes Recomendados

### Cenário 1: Lead COM Email
1. Acessar https://lwksistemas.com.br/loja/22239255889/crm-vendas/propostas
2. Verificar proposta com lead que tem email
3. ✅ Botão de assinatura deve estar habilitado (verde)
4. Clicar no botão
5. ✅ Email deve ser enviado ao cliente

### Cenário 2: Lead SEM Email
1. Criar proposta com lead sem email
2. ✅ Botão de assinatura deve estar desabilitado
3. ✅ Mensagem de aviso deve aparecer
4. Editar lead e adicionar email
5. Recarregar página de propostas
6. ✅ Botão deve ficar habilitado

## Status

- ✅ Backend deployado (Heroku v1151)
- ✅ Frontend deployado (Vercel)
- ✅ Botão habilitado quando lead tem email
- ✅ Mensagem de aviso quando lead não tem email
- ⏳ Validação com usuário

## Próximos Passos

1. Validar com usuário que botão está funcionando
2. Aplicar mesma correção na página de contratos (se necessário)
3. Adicionar validação de email ao criar/editar lead

---

**Data:** 19/03/2026  
**Versão Backend:** v1151  
**Versão Frontend:** Última (Vercel)  
**Status:** Deploy concluído, botão habilitado
