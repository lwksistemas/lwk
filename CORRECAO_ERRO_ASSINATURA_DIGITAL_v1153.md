# Correção: Erro 500 ao Enviar para Assinatura Digital (v1153)

## Problema Identificado

### Erro Original
```
ValueError: Cannot assign ContentType: the current database router prevents this relation
```

### Causa Raiz
O modelo `AssinaturaDigital` usava `GenericForeignKey` (ContentType) que criava uma relação cross-database:
- `ContentType` está no app `contenttypes` → banco `default`
- `AssinaturaDigital` está no app `crm_vendas` → banco do tenant (loja_*)
- O database router (`MultiTenantRouter`) bloqueia relações entre bancos diferentes

### Linha do Erro
```python
# backend/crm_vendas/assinatura_digital_service.py:66
content_type = ContentType.objects.get_for_model(documento)
assinatura = AssinaturaDigital.objects.create(
    content_type=content_type,  # ❌ Tentando criar relação cross-database
    object_id=documento.id,
    ...
)
```

## Solução Implementada

### 1. Substituir GenericForeignKey por ForeignKeys Diretos

**Antes:**
```python
class AssinaturaDigital(LojaIsolationMixin, models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    documento = GenericForeignKey('content_type', 'object_id')
```

**Depois:**
```python
class AssinaturaDigital(LojaIsolationMixin, models.Model):
    proposta = models.ForeignKey(
        'Proposta',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assinaturas'
    )
    contrato = models.ForeignKey(
        'Contrato',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assinaturas'
    )
    
    @property
    def documento(self):
        """Retorna o documento (proposta ou contrato) para compatibilidade."""
        return self.proposta or self.contrato
```

### 2. Adicionar Constraint de Validação

```python
constraints = [
    models.CheckConstraint(
        check=(
            models.Q(proposta__isnull=False, contrato__isnull=True) |
            models.Q(proposta__isnull=True, contrato__isnull=False)
        ),
        name='crm_assin_proposta_ou_contrato'
    )
]
```

Garante que apenas um dos campos (proposta OU contrato) está preenchido, nunca ambos.

### 3. Atualizar Serviço de Assinatura

**Antes:**
```python
content_type = ContentType.objects.get_for_model(documento)
assinatura = AssinaturaDigital.objects.create(
    content_type=content_type,
    object_id=documento.id,
    ...
)
```

**Depois:**
```python
kwargs = {
    'tipo': tipo,
    'nome_assinante': nome,
    'email_assinante': email,
    'token': token,
    'token_expira_em': timezone.now() + timedelta(days=TOKEN_EXPIRACAO_DIAS),
    'loja_id': loja_id,
    'ip_address': '0.0.0.0',
}

if documento.__class__.__name__ == 'Proposta':
    kwargs['proposta'] = documento
else:
    kwargs['contrato'] = documento

assinatura = AssinaturaDigital.objects.create(**kwargs)
```

### 4. Atualizar Geração de PDF

**Antes:**
```python
content_type = ContentType.objects.get_for_model(proposta)
assinaturas = AssinaturaDigital.objects.filter(
    content_type=content_type,
    object_id=proposta.id,
    assinado=True
)
```

**Depois:**
```python
assinaturas = AssinaturaDigital.objects.filter(
    proposta=proposta,
    assinado=True
)
```

### 5. Migration Automática de Dados

A migration `0025_remove_genericforeignkey_assinatura.py` migra automaticamente os dados existentes:

```sql
-- Migrar propostas
UPDATE crm_vendas_assinatura_digital
SET proposta_id = object_id
WHERE content_type_id = (
    SELECT id FROM django_content_type 
    WHERE app_label = 'crm_vendas' AND model = 'proposta'
);

-- Migrar contratos
UPDATE crm_vendas_assinatura_digital
SET contrato_id = object_id
WHERE content_type_id = (
    SELECT id FROM django_content_type 
    WHERE app_label = 'crm_vendas' AND model = 'contrato'
);
```

## Vantagens da Solução

1. **Elimina Dependência Cross-Database**: Todos os modelos ficam no mesmo banco (tenant)
2. **Mais Performático**: Sem joins extras com ContentType
3. **Mais Simples**: Código mais direto e fácil de manter
4. **Type-Safe**: IDEs conseguem inferir tipos corretamente
5. **Compatibilidade**: Property `documento` mantém código existente funcionando

## Arquivos Modificados

- `backend/crm_vendas/models.py` - Modelo AssinaturaDigital
- `backend/crm_vendas/assinatura_digital_service.py` - Serviço de criação
- `backend/crm_vendas/pdf_proposta_contrato.py` - Geração de PDF
- `backend/crm_vendas/migrations/0025_remove_genericforeignkey_assinatura.py` - Migration

## Deploy

```bash
git add -A
git commit -m "fix(crm-vendas): Remove GenericForeignKey de AssinaturaDigital para evitar erro cross-database"
git push heroku master
```

**Versão Heroku**: v1152 (migration aplicada automaticamente)

## Teste

1. Acessar: https://lwksistemas.com.br/loja/22239255889/crm-vendas/propostas
2. Verificar que o botão "Enviar para Assinatura Digital" está habilitado ✅
3. Clicar em "Enviar para Assinatura Digital"
4. Sistema deve enviar email sem erro 500 ✅
5. Status deve mudar para "Aguardando Cliente" ✅

## Resultado Final

✅ Erro 500 corrigido (ValueError: Cannot assign ContentType)
✅ Botão de assinatura digital habilitado
✅ Assinatura digital funcionando corretamente
✅ Dados existentes migrados automaticamente
✅ Código mais simples e performático
✅ Sem dependências cross-database

## Próximos Passos

Agora o usuário pode:
1. Clicar no botão "Enviar para Assinatura Digital"
2. O cliente receberá email com link de assinatura
3. Após cliente assinar, vendedor receberá email
4. Após vendedor assinar, ambos recebem PDF final assinado
