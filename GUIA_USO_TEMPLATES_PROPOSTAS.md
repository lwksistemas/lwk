# Guia de Uso - Sistema de Templates de Propostas

**Versão**: v1025  
**Data**: 18/03/2026  

---

## 📋 VISÃO GERAL

O sistema de templates permite criar múltiplas propostas padrão diferentes e escolher qual usar ao criar uma nova proposta comercial.

---

## 🎯 FUNCIONALIDADES

### 1. Gerenciar Templates
**URL**: `/loja/[slug]/crm-vendas/proposta-templates`

#### Criar Novo Template
1. Clique em **"Novo Template"**
2. Preencha:
   - **Nome**: Ex: "Proposta Premium", "Proposta Básica"
   - **Conteúdo**: Texto da proposta
   - **Marcar como padrão**: ✓ (opcional)
   - **Ativo**: ✓ (recomendado)
3. Clique em **"Salvar"**

#### Editar Template
1. Clique no ícone de **lápis** no card do template
2. Modifique os campos desejados
3. Clique em **"Salvar"**

#### Excluir Template
1. Clique no ícone de **lixeira** no card do template
2. Confirme a exclusão

#### Marcar como Padrão
1. Clique no ícone de **estrela** no card do template
2. O template será marcado como padrão (⭐)
3. Apenas um template pode ser padrão por vez

---

### 2. Usar Templates em Propostas
**URL**: `/loja/[slug]/crm-vendas/propostas`

#### Ao Criar Nova Proposta
1. Clique em **"Nova Proposta"**
2. O template padrão (⭐) será carregado automaticamente no campo "Conteúdo"
3. Para usar outro template:
   - Localize o campo **"Usar template"**
   - Selecione o template desejado no dropdown
   - O conteúdo será preenchido automaticamente

#### Ao Editar Proposta
1. Clique no ícone de **lápis** na proposta
2. Use o campo **"Usar template"** para trocar o conteúdo
3. Ou edite manualmente o campo "Conteúdo"

---

## 🔄 FLUXO DE TRABALHO RECOMENDADO

### Configuração Inicial
1. Acesse `/loja/[slug]/crm-vendas/proposta-templates`
2. Crie seus templates principais:
   - **Proposta Básica**: Para clientes pequenos
   - **Proposta Premium**: Para clientes grandes
   - **Proposta Personalizada**: Para casos especiais
3. Marque o mais usado como **padrão** (⭐)

### Uso Diário
1. Ao criar proposta, o template padrão já estará carregado
2. Se precisar de outro template, selecione no dropdown
3. Personalize o conteúdo conforme necessário
4. Salve a proposta

---

## 💡 DICAS

### Template Padrão
- Apenas um template pode ser padrão por vez
- Ao marcar um novo como padrão, o anterior perde a marcação
- Template padrão é carregado automaticamente em novas propostas

### Organização
- Use nomes descritivos: "Proposta Premium", não "Template 1"
- Mantenha templates inativos se não usar mais (não exclua)
- Revise periodicamente os templates para manter atualizados

### Conteúdo
- Inclua variáveis que você sempre edita: [NOME_CLIENTE], [VALOR]
- Mantenha formatação consistente entre templates
- Use quebras de linha para melhor legibilidade

---

## 🎨 INTERFACE

### Página de Templates
```
┌─────────────────────────────────────────────┐
│ Templates de Propostas    [Novo Template]   │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐  ┌──────────────┐        │
│  │ Proposta     │  │ Proposta     │        │
│  │ Básica ⭐    │  │ Premium      │        │
│  │              │  │              │        │
│  │ Conteúdo...  │  │ Conteúdo...  │        │
│  │              │  │              │        │
│  │ [Ativo]      │  │ [Ativo]      │        │
│  │ ⭐ ✏️ 🗑️      │  │ ⭐ ✏️ 🗑️      │        │
│  └──────────────┘  └──────────────┘        │
│                                             │
└─────────────────────────────────────────────┘
```

### Seletor em Propostas
```
┌─────────────────────────────────────────────┐
│ Usar template                               │
│ ┌─────────────────────────────────────────┐ │
│ │ Selecione um template (opcional)      ▼ │ │
│ └─────────────────────────────────────────┘ │
│   • Proposta Básica (PADRÃO)                │
│   • Proposta Premium                        │
│   • Proposta Personalizada                  │
└─────────────────────────────────────────────┘
```

---

## 🔧 CAMPOS DO TEMPLATE

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| Nome | ✅ Sim | Identificação do template |
| Conteúdo | ❌ Não | Texto da proposta |
| Marcar como padrão | ❌ Não | Define como template padrão |
| Ativo | ❌ Não | Habilita/desabilita o template |

---

## 🚨 OBSERVAÇÕES IMPORTANTES

1. **Template Padrão**: Sempre carregado em novas propostas
2. **Templates Inativos**: Não aparecem no seletor de propostas
3. **Exclusão**: Não afeta propostas já criadas
4. **Edição**: Não afeta propostas já criadas (apenas novas)

---

## 📞 SUPORTE

Se tiver dúvidas ou problemas:
1. Verifique se o template está **Ativo**
2. Confirme se há um template marcado como **padrão**
3. Recarregue a página se o seletor não aparecer
4. Entre em contato com o suporte técnico

---

**Última atualização**: 18/03/2026  
**Versão do sistema**: v1025
