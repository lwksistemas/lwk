# Relatório de refatoração e limpeza — LWK Sistemas

**Período:** sessões de refatoração contínua (maio/2026)  
**Projeto:** `/home/luiz/Documentos/lwksistemas`  
**Princípio:** reorganizar e centralizar código duplicado **sem alterar comportamento** (mesmas APIs, mesmas regras de negócio, mesmos fluxos de UI).

---

## 1. Resumo executivo

Foi realizada uma limpeza estrutural em três frentes:

| Área | Resultado |
|------|-----------|
| **NFS-e** (loja CRM + superadmin) | Helpers, componentes e páginas enxutas; cancelamento, download e status unificados |
| **Clínica da Beleza** | Offline, entidades bilíngues, erros de API e constantes centralizados |
| **Backend CRM** | Mixins e filtros de queryset reutilizáveis; menos cópia em ViewSets |

**Garantia:** nenhuma funcionalidade foi removida de propósito; a lógica foi **movida**, não reescrita com regras diferentes.

---

## 2. Novos arquivos (fonte única de verdade)

### Frontend — `lib/`

| Arquivo | Função |
|---------|--------|
| `nfse-helpers.ts` | Cancelamento ISSNet, provedor, sync, download PDF/XML, status, busca |
| `nfse-constants.ts` | Filtros de status na UI superadmin |
| `nfse-emissao-form.ts` | Formulário e carga de contas/leads para emissão NFS-e |
| `clinica-beleza-offline.ts` | Offline, duplicata local, id temporário, rede |
| `clinica-beleza-form-errors.ts` | Erros API pacientes, profissionais, procedimentos |
| `clinica-beleza-entities.ts` | Campos PT/EN (`name`/`nome`, etc.) |
| `clinica-beleza-constants.ts` | Pagamento, agenda, formas de pagamento |

### Frontend — `components/nfse/`

| Componente | Uso |
|------------|-----|
| `NfseStatusBadge` | Superadmin (shadcn Badge) |
| `NfseStatusPill` | Loja CRM (pill Tailwind) |
| `NfseProvedorBadge` | Provedor nacional / ISSNet / Asaas |

### Frontend — NFS-e loja (`crm-vendas/nfse/`)

| Arquivo | Função |
|---------|--------|
| `types.ts` | Tipo `NFSe` e handlers da tabela |
| `components/NfseLojaHeader.tsx` | Cabeçalho |
| `components/NfseLojaFilters.tsx` | Busca e filtro status |
| `components/NfseLojaSyncMessage.tsx` | Mensagens sync |
| `components/NfseLojaLoading.tsx` | Loading |
| `components/NfseLojaEmptyState.tsx` | Estado vazio |
| `components/NfseLojaTable.tsx` | Tabela + linha + ações |
| `components/ModalEmitirNFSe*.tsx` | Steps do modal de emissão |

### Frontend — NFS-e superadmin (`superadmin/nfse/`)

| Arquivo | Função |
|---------|--------|
| `types.ts` | `NFSeEmitida` |
| `components/NfseSuperadminHeader.tsx` | Cabeçalho + atualizar |
| `components/NfseSuperadminFilters.tsx` | Filtros por status |
| `components/NfseSuperadminMessage.tsx` | Alertas |
| `components/NfseSuperadminTable.tsx` | Tabela completa |

### Backend — `crm_vendas/`

| Alteração | Função |
|-----------|--------|
| `views_common.py` | Cache HTTP, filtros queryset, `LojaScopedCatalogMixin`, `CRMNoCacheListMixin` |
| `mixins.py` | `VendedorAutoAssignCreateMixin` |
| `assinatura_digital_service.py` | Alias de `normalizar_token_url` (core) |

### Documentação

| Arquivo | Função |
|---------|--------|
| `docs/REFATORACAO-LIMPEZA-SISTEMA.md` | Este relatório |

---

## 3. Duplicações eliminadas (por tema)

### 3.1 NFS-e

- **Motivos de cancelamento** — 3 cópias (loja, superadmin, backend alinhado) → `nfse-helpers.ts` (`solicitarCancelamentoNFSe`, `NFSE_CANCELAMENTO_OPCOES`)
- **Detecção ISSNet/Asaas** — `nfUsaIssnet`, `nfseSyncEndpoint`
- **Download PDF/XML** — blobs e `createObjectURL` repetidos → `openPdfFromApiBlobResponse`, `downloadNfseXmlBlob`, `downloadBlobFile`
- **Regras de botões** — `nfsePodeBaixar`, `nfsePodeCancelar`, `nfsePodeSincronizar`, `nfsePodeExcluirLoja`, `nfsePodeExcluirSuperadmin`
- **Status visual** — `NfseStatusBadge`, `NfseStatusPill`, `nfseStatusTailwindClass`
- **Provedor** — `nfseProvedorLabel`, `NfseProvedorBadge`
- **`unwrapDrfList`** — 3 cópias → `ensureArray` (`array-helpers.ts`)
- **Páginas monolíticas** — listagem extraída em componentes (loja ~440→~220 linhas; superadmin ~306→~165 linhas na page)

### 3.2 Clínica da Beleza

- **Offline** — 6 blocos “já existe na lista local” → `clinica-beleza-offline.ts`
- **Helpers de campo** — `pName`, `prName`, `getName`, etc. → `clinica-beleza-entities.ts`
- **Erros API** — pacientes + profissionais (POST/PUT duplicado) + procedimentos → `clinica-beleza-form-errors.ts`
- **Constantes** — financeiro + modal agenda → `clinica-beleza-constants.ts`

### 3.3 CRM Vendas (frontend)

- **Download PDF/DOCX** propostas e contratos → `downloadCrmDocumento` em `crm-utils.ts`
- **Listas DRF** — já usavam `normalizeListResponse` (mantido e estendido)

### 3.4 CRM Vendas (backend)

- **Headers anti-cache** em `list()` — 5+ cópias → `aplicar_cache_control_sem_store` / `CRMNoCacheListMixin`
- **`perform_create` com vendedor** — Conta e Lead idênticos → `VendedorAutoAssignCreateMixin`
- **Filtros `?status=`, `?origem=`, etc.** → `filtrar_queryset_por_query_params`
- **Catálogo por loja** — Categoria e ProdutoServico → `LojaScopedCatalogMixin`
- **Documentos** — `DocumentoQuerysetMixin` usa filtro centralizado
- **Token assinatura URL** — loop `unquote` duplicado → alias para `core.assinatura_service.normalizar_token_url`

---

## 4. Páginas e módulos tocados

### Frontend

- `app/.../crm-vendas/nfse/page.tsx` + `components/*`
- `app/.../superadmin/nfse/page.tsx` + `components/*`
- `app/.../clinica-beleza/pacientes|profissionais|procedimentos/page.tsx`
- `app/.../clinica-beleza/financeiro/page.tsx`
- `components/clinica-beleza/ModalConflitoAgenda.tsx`
- `app/.../crm-vendas/propostas/page.tsx`
- `app/.../crm-vendas/contratos/page.tsx`

### Backend

- `crm_vendas/views_common.py`
- `crm_vendas/mixins.py`
- `crm_vendas/views_cadastros.py`
- `crm_vendas/views_pipelines.py`
- `crm_vendas/views.py` (Categoria, Produto, OportunidadeItem)
- `crm_vendas/mixins_documento.py`
- `crm_vendas/assinatura_digital_service.py`
- `crm_vendas/vendedor_admin_service.py` (reexport cache)

---

## 5. Comportamento preservado (checklist de regressão)

### NFS-e — Loja

- [ ] Listar com filtro de status e busca local
- [ ] Emitir NFS-e (cliente cadastrado e manual)
- [ ] Baixar PDF (URL JSON + blob) e sync ISSNet após PDF quando aplicável
- [ ] Baixar XML, reenviar email, cancelar (prompts + aviso ISSNet), sincronizar, excluir

### NFS-e — Superadmin

- [ ] Filtros Todas / Emitidas / Canceladas / Erros
- [ ] PDF, XML (`tem_xml`), reenviar, cancelar, excluir (erro/pendente)
- [ ] Emissão manual pelo modal

### Clínica da Beleza

- [ ] Salvar paciente/profissional/procedimento online e offline
- [ ] Bloqueio de duplicata offline
- [ ] Mensagens de erro de validação (incl. email duplicado em profissional)
- [ ] Financeiro: rótulos de forma de pagamento e status
- [ ] Modal conflito agenda: rótulos de status

### CRM

- [ ] Criar/listar categoria e produto com `?ativo=`
- [ ] Criar conta/lead com vendedor logado
- [ ] Propostas/contratos: download PDF e Word
- [ ] Assinatura digital: links com token na URL ainda resolvem

---

## 6. Benefícios para manutenção

1. **Correção em um lugar** — Ex.: mudar texto do aviso ISSNet no cancelamento → só `nfse-helpers.ts`.
2. **Páginas legíveis** — Estado + handlers na page; UI em componentes.
3. **Backend consistente** — Novos ViewSets podem usar mixins em vez de copiar 15 linhas.
4. **Onboarding** — Novos devs encontram `lib/nfse-*` e `lib/clinica-beleza-*` antes de abrir páginas gigantes.
5. **Menos risco de divergência** — Loja e superadmin usam as mesmas regras `nfsePode*`.

---

## 7. Escopo não alterado (de propósito)

- Regras de negócio novas ou mudança de fluxo
- Testes automatizados adicionados (não solicitados)
- Refatoração completa de `propostas/page.tsx` e `contratos/page.tsx` (ainda grandes, mas já usam libs compartilhadas)
- Views monolíticas antigas fora de `crm_vendas` (ex.: outros apps Django)
- Migração de `downloadBlobAsFile` (crm-utils) para `nfse-helpers.downloadBlobFile` — ambos coexistem com mesma função

---

## 8. Próximos passos sugeridos (opcional)

1. Hook `useCrmDocumentoListagem` para propostas/contratos (load + modais)
2. Tipo base `CrmDocumento` compartilhado entre Proposta e Contrato
3. Extrair `AtividadeViewSet.perform_create` (notificações + Google sync) para service
4. Unificar `downloadBlobAsFile` / `downloadBlobFile` em um único helper global
5. Testes E2E nos fluxos críticos NFS-e e offline clínica

---

## 9. Conclusão

A refatoração focou em **DRY (Don't Repeat Yourself)** e **separação UI vs lógica**, mantendo **paridade funcional** com o sistema anterior. O código está mais modular, documentado por arquivo de responsabilidade clara, e preparado para evoluções sem multiplicar cópias nas páginas.

Para dúvidas sobre onde alterar cada domínio, use a tabela da seção 2 como índice.
