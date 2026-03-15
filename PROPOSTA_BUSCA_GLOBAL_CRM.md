# Proposta: Busca Global no CRM Vendas

## Objetivo

Implementar busca funcional na barra superior fixa do CRM, permitindo localizar rapidamente **Leads**, **Oportunidades** e **Contas** por nome, empresa, e-mail ou telefone.

---

## 1. Fluxo de Uso

1. Usuário digita na barra (mín. 2 caracteres)
2. Após ~300ms de debounce, dispara a busca
3. Dropdown exibe resultados agrupados por tipo (Leads, Oportunidades, Contas)
4. Clique em um resultado → navega para a página correspondente (detalhe ou listagem filtrada)

---

## 2. Backend

### 2.1 Novo endpoint

```
GET /crm-vendas/busca/?q=termo&limit=5
```

**Parâmetros:**
- `q` (obrigatório): termo de busca (mín. 2 caracteres)
- `limit` (opcional): máx. resultados por tipo (padrão: 5)

**Resposta:**
```json
{
  "leads": [
    { "id": 1, "nome": "João Silva", "empresa": "Empresa X", "status": "novo" }
  ],
  "oportunidades": [
    { "id": 2, "titulo": "Venda Empresa X", "valor": "15000.00", "etapa": "negotiation" }
  ],
  "contas": [
    { "id": 3, "nome": "Empresa X", "segmento": "Varejo" }
  ]
}
```

### 2.2 Lógica de busca

- **Leads**: `nome`, `empresa`, `email`, `telefone` (icontains)
- **Oportunidades**: `titulo`, `lead__nome`, `lead__empresa`, `conta__nome` (icontains)
- **Contas**: `nome`, `email`, `telefone` (icontains)

Respeitar isolamento por loja e filtro por vendedor (quando aplicável), usando a mesma lógica de `get_current_vendedor_id`.

### 2.3 Arquivos a criar/alterar

- `backend/crm_vendas/views.py` – nova view `crm_busca`
- `backend/crm_vendas/urls.py` – rota `path('busca/', crm_busca)`

---

## 3. Frontend

### 3.1 Componente de busca

Criar `SearchBarCrm` (ou integrar no `HeaderCrm`):

- Input controlado com estado `query`
- Debounce de 300ms antes de chamar a API
- Dropdown posicionado abaixo do input com resultados
- Fechar dropdown ao clicar fora ou ao selecionar um item
- Loading e estado vazio (“Nenhum resultado”)

### 3.2 Navegação ao clicar

| Tipo         | Ação ao clicar                                      |
|--------------|-----------------------------------------------------|
| Lead         | `/loja/{slug}/crm-vendas/leads` (abrir modal ver lead ou ir para leads com filtro) |
| Oportunidade | `/loja/{slug}/crm-vendas/pipeline` (foco na oportunidade) |
| Conta        | `/loja/{slug}/crm-vendas/customers` (detalhe da conta) |

**Opção mais simples:** redirecionar para a listagem com `?q=termo` e aplicar filtro no backend da listagem.

**Opção mais rica:** link direto para o item (ex.: `/leads/{id}` se existir rota de detalhe).

### 3.3 Mobile

- Barra de busca oculta em telas pequenas (`hidden sm:block`)
- Botão de busca que abre um modal/popover com o input (opcional, fase 2)

---

## 4. Estimativa de Esforço

| Etapa              | Tempo estimado |
|--------------------|----------------|
| Backend (API)      | 1–2 h          |
| Frontend (Header)  | 2–3 h          |
| Testes e ajustes   | 1 h            |
| **Total**          | **4–6 h**      |

---

## 5. Considerações

- **Performance:** limitar resultados (ex.: 5 por tipo) e usar `select_related`/`prefetch_related` para evitar N+1.
- **Segurança:** manter isolamento por loja e filtro por vendedor.
- **UX:** debounce para reduzir requisições; feedback visual (loading, empty state).
- **Acessibilidade:** suporte a teclado (Tab, Enter, Escape) e `aria-*` adequados.

---

## 6. Próximos Passos

1. Aprovar proposta
2. Implementar backend
3. Implementar frontend
4. Testar em produção
5. (Opcional) Adicionar atalho de teclado (ex.: Ctrl+K) para focar na busca
