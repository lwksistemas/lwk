# Resumo Completo das Correções v1027

## Visão Geral
Versão v1027 implementou campos de assinatura em propostas/contratos e corrigiu problemas críticos de filtros e criação de tabelas no CRM Vendas.

## Versões Deployadas
- **Backend Heroku**: v1143 (todas as correções)
- **Frontend Vercel**: Última versão com campos de assinatura

---

## 1. Feature: Campos de Assinatura (v1136)

### Problema
Propostas e contratos não tinham campos para nomes de assinatura no PDF.

### Solução
- Adicionados campos `nome_vendedor_assinatura` e `nome_cliente_assinatura` nos modelos Proposta e Contrato
- Migration 0023 criada (executada manualmente via comando `criar_colunas_assinatura`)
- Novo endpoint `/api/crm-vendas/vendedores/me/` para buscar dados do vendedor logado
- Frontend atualizado com inputs de assinatura e preenchimento automático

### Arquivos Modificados
- `backend/crm_vendas/models.py`
- `backend/crm_vendas/serializers.py`
- `backend/crm_vendas/views.py`
- `backend/crm_vendas/migrations/0023_add_assinatura_fields.py`
- `backend/crm_vendas/management/commands/criar_colunas_assinatura.py`
- `frontend/components/crm-vendas/PropostaFormContent.tsx`
- `frontend/components/crm-vendas/modals/ModalPropostaForm.tsx`
- `frontend/components/crm-vendas/modals/ModalContratoForm.tsx`
- `frontend/app/(dashboard)/loja/[slug]/crm-vendas/propostas/page.tsx`

---

## 2. Correção: Filtro de Vendedor - Owner Vê Todos os Dados (v1137-v1139)

### Problema
Admin da loja (owner) não via leads e oportunidades criados por vendedores quando o owner tinha VendedorUsuario vinculado.

### Causa Raiz
`get_current_vendedor_id()` retornava vendedor_id para owner, aplicando filtro incorretamente.

### Solução v1137
Atualizado `VendedorFilterMixin.filter_by_vendedor()` para verificar se é owner ANTES de aplicar filtro:
```python
# Verificar se é proprietário da loja
loja_id = get_current_loja_id()
if loja_id and self.request and self.request.user:
    try:
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if loja and loja.owner_id == self.request.user.id:
            # Owner SEMPRE vê todos os dados
            return queryset
    except Exception:
        pass
```

### Solução v1138
Corrigido `dashboard_data()` para owner sempre ver todos os dados + comando `limpar_cache_dashboard`:
```python
# Verificar se é owner ANTES de aplicar filtro de vendedor
is_owner = False
try:
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if loja and loja.owner_id == request.user.id:
        is_owner = True
except Exception:
    pass

vendedor_id = None if is_owner else get_current_vendedor_id(request)
```

### Solução v1139
Corrigido `LeadViewSet.retrieve()` para owner acessar qualquer lead (necessário para criar nova proposta):
```python
# Para retrieve (GET /leads/{id}/), owner sempre tem acesso
if self.action == 'retrieve':
    from superadmin.models import Loja
    loja_id = get_current_loja_id()
    if loja_id and self.request and self.request.user:
        try:
            loja = Loja.objects.using('default').filter(id=loja_id).first()
            if loja and loja.owner_id == self.request.user.id:
                # Owner: retorna queryset sem filtro
                return qs
        except Exception:
            pass
```

### Arquivos Modificados
- `backend/crm_vendas/mixins.py`
- `backend/crm_vendas/views.py`
- `backend/crm_vendas/management/commands/limpar_cache_dashboard.py`

---

## 3. Correção: Tabelas Faltantes no Pipeline (v1141-v1142)

### Problema
Erro "relation crm_vendas_oportunidade_item does not exist" ao acessar pipeline em lojas existentes.

### Causa Raiz
Tabelas de produtos e itens não foram criadas no schema da loja quando o CRM foi ativado.

### Solução v1141
Criado comando `criar_tabelas_oportunidade_item` para criar tabelas manualmente em lojas existentes:
```bash
python manage.py criar_tabelas_oportunidade_item
```

### Solução v1142
Adicionado signal em `backend/superadmin/signals.py` para criar tabelas automaticamente ao criar nova loja CRM Vendas:
```python
elif tipo_loja_nome == 'CRM Vendas':
    # Criar tabelas do CRM automaticamente
    try:
        from crm_vendas.schema_service import configurar_schema_crm_loja
        if configurar_schema_crm_loja(instance):
            logger.info(f"✅ Schema CRM configurado para loja {instance.nome}")
            
            # Criar tabelas de produtos e itens
            from django.db import connection
            db_name = instance.database_name
            
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {db_name}, public;")
                
                # Verificar se tabela já existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = %s
                        AND table_name = 'crm_vendas_oportunidade_item'
                    );
                """, [db_name])
                
                existe = cursor.fetchone()[0]
                
                if not existe:
                    # Criar tabelas
                    _criar_tabelas_crm(cursor, db_name)
                    logger.info(f"✅ Tabelas CRM criadas para loja {instance.nome}")
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas CRM para loja {instance.nome}: {e}")
```

Função auxiliar `_criar_tabelas_crm()` cria:
- ProdutoServico
- OportunidadeItem
- Proposta
- Contrato

Com índices apropriados para performance.

### Arquivos Modificados
- `backend/crm_vendas/management/commands/criar_tabelas_oportunidade_item.py`
- `backend/superadmin/signals.py`

---

## 4. Feature: Seção de Assinaturas nos PDFs (v1143)

### Problema
Campos de assinatura salvos no banco mas não apareciam no PDF gerado.

### Solução
Adicionada seção "Assinaturas" no final dos PDFs de propostas e contratos:

```python
# Assinaturas
nome_vendedor = getattr(proposta, 'nome_vendedor_assinatura', None) or '___________________________'
nome_cliente = getattr(proposta, 'nome_cliente_assinatura', None) or '___________________________'

elements.append(Paragraph('<b>Assinaturas</b>', section_style))
elements.append(Spacer(1, 0.5*cm))

# Tabela de assinaturas (2 colunas)
assinatura_data = [
    ['___________________________', '___________________________'],
    [nome_vendedor, nome_cliente],
    ['Vendedor', 'Cliente'],
]
assinatura_table = Table(assinatura_data, colWidths=[8*cm, 8*cm])
assinatura_table.setStyle(TableStyle([
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('TOPPADDING', (0, 0), (-1, 0), 20),
    ('BOTTOMPADDING', (0, 1), (-1, 1), 5),
]))
elements.append(assinatura_table)
```

### Layout
- Tabela com 2 colunas (Vendedor | Cliente)
- Linha para assinatura (underline)
- Nomes dos signatários
- Labels "Vendedor" e "Cliente"

### Arquivos Modificados
- `backend/crm_vendas/pdf_proposta_contrato.py`

---

## Regras de Negócio Importantes

### Owner vs Vendedor
- **Owner (Administrador)**: SEMPRE vê todos os dados da loja, mesmo se tiver VendedorUsuario vinculado
- **Vendedor**: Vê apenas seus próprios dados (leads, oportunidades, atividades)

### Verificação de Owner
Implementada em todos os mixins e views críticas:
```python
from superadmin.models import Loja
loja = Loja.objects.using('default').filter(id=loja_id).first()
if loja and loja.owner_id == request.user.id:
    # Owner: acesso total
```

### Criação Automática de Tabelas
Novas lojas CRM Vendas têm todas as tabelas criadas automaticamente via signal:
- crm_vendas_produto_servico
- crm_vendas_oportunidade_item
- crm_vendas_proposta
- crm_vendas_contrato

---

## Comandos de Manutenção

### Criar Colunas de Assinatura (Lojas Existentes)
```bash
python manage.py criar_colunas_assinatura
```

### Criar Tabelas de Produtos/Itens (Lojas Existentes)
```bash
python manage.py criar_tabelas_oportunidade_item
```

### Limpar Cache do Dashboard
```bash
python manage.py limpar_cache_dashboard
```

---

## Deploy

### Backend (Heroku)
```bash
git add .
git commit -m "feat: implementar campos de assinatura e corrigir filtros (v1027)"
git push heroku master
```

### Frontend (Vercel)
```bash
cd frontend
vercel --prod --yes
```

---

## Testes Realizados

### Loja de Testes
- **Loja ID**: 22239255889
- **URL**: https://lwksistemas.com.br/loja/22239255889/crm-vendas/

### Cenários Testados
1. ✅ Admin vê todos os leads e oportunidades (mesmo com vendedor vinculado)
2. ✅ Vendedor vê apenas seus próprios dados
3. ✅ Campos de assinatura salvam corretamente
4. ✅ PDFs mostram seção de assinaturas
5. ✅ Pipeline carrega sem erros (tabelas criadas)
6. ✅ Dashboard mostra dados corretos para admin e vendedor
7. ✅ Nova proposta busca lead corretamente (owner pode acessar qualquer lead)

---

## Problemas Conhecidos e Soluções

### Migrations no Heroku
Migrations frequentemente marcam como aplicadas mas não criam tabelas/colunas. Solução:
- Criar comandos management para executar manualmente
- Verificar existência antes de criar

### Cache do Dashboard
Dashboard pode mostrar dados desatualizados. Solução:
- Comando `limpar_cache_dashboard` para forçar atualização
- Cache invalidado automaticamente em operações de escrita

---

## Próximos Passos

### Melhorias Futuras
1. Adicionar assinatura digital nos PDFs
2. Permitir upload de imagem de assinatura
3. Adicionar campo de data de assinatura
4. Histórico de versões de propostas/contratos

### Monitoramento
- Verificar logs de criação de lojas para garantir que tabelas são criadas
- Monitorar erros de "relation does not exist"
- Verificar se owners conseguem acessar todos os dados

---

## Conclusão

Versão v1027 implementou com sucesso:
- ✅ Campos de assinatura em propostas e contratos
- ✅ Correção de filtros para owner ver todos os dados
- ✅ Criação automática de tabelas em novas lojas
- ✅ Seção de assinaturas nos PDFs

Todas as correções foram testadas na loja 22239255889 e deployadas em produção.

**Status**: ✅ CONCLUÍDO
**Data**: 2026-03-18
**Versão Backend**: v1143
**Versão Frontend**: Última versão deployada
