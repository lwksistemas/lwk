# Relatório de Análises - LWK Sistemas

**Data:** 09/03/2026

---

## 1. Sistema em Produção ✅

| Verificação | Status |
|-------------|--------|
| API Root (Heroku) | ✅ Online |
| API Superadmin (auth) | ✅ HTTP 401 (esperado) |
| Página inicial (Vercel) | ✅ HTTP 200 |
| Login Superadmin | ✅ HTTP 200 |
| Login Suporte | ✅ HTTP 200 |
| Página limpar cache | ✅ HTTP 200 |

**Observação:** Schema OpenAPI retorna HTTP 500 (opcional, não crítico).

---

## 2. Frontend (Next.js)

### Build de Produção ✅
- **Status:** Sucesso
- **Páginas geradas:** 27/27
- **First Load JS:** ~360 kB (shared)

### TypeScript ✅
- **Status:** Sem erros (`npx tsc --noEmit`)

### ESLint ✅
Corrigidos em 09/03/2026: useCallback, deps e eslint-disable com justificativa onde intencional.

---

## 3. Vulnerabilidades npm ⚠️

**Total:** 5 altas restantes após `npm audit fix` (09/03/2026)

| Pacote | Severidade | Problema |
|--------|------------|----------|
| ajv | moderada | ReDoS com `$data` |
| minimatch | alta | ReDoS (múltiplas variantes) |
| rollup | alta | Path Traversal |
| serialize-javascript | alta | RCE via RegExp.flags |

**Cadeia de dependência:** Maioria em `@ducanh2912/next-pwa` → workbox-build → rollup/serialize-javascript.

**Ações sugeridas:**
```bash
npm audit fix          # Corrige sem breaking changes
npm audit fix --force  # Pode quebrar (downgrade next-pwa)
```

---

## 4. Backend (Django)

### Ambiente local ⚠️
- **Django check:** Falhou (módulos ausentes no ambiente local)
- **Causa:** `drf_spectacular` ou `pkg_resources` não encontrados
- **Nota:** Em produção (Heroku) o deploy funciona; o ambiente local pode precisar de `pip install -r requirements.txt` no venv.

### Dependências Python (requirements.txt)
- Django 4.2.11
- DRF 3.14.0
- drf-spectacular 0.27.2
- psycopg2-binary 2.9.9
- Outras: redis, gunicorn, google-api, etc.

**Recomendação:** Executar `safety check` periodicamente:
```bash
pip install safety
safety check -r backend/requirements.txt
```

---

## 5. Documentação de Análises Existentes

O projeto possui documentação detalhada em `docs/`:

| Documento | Conteúdo |
|-----------|----------|
| `ANALISE_ESCOPO_SEGURANCA_DESEMPENHO.md` | Escopo de segurança, desempenho e limpeza |
| `ANALISE_SEGURANCA_ORFAOS_PRODUCAO.md` | Órfãos e segurança em produção |
| `ANALISE_BACKUP_BOAS_PRATICAS.md` | Backup e boas práticas |
| `ANALISE_CLINICA_BELEZA_OTIMIZACOES.md` | Otimizações Clínica da Beleza |
| `ANALISE_MONITORAMENTO_ASAAS_MERCADOPAGO_100_LOJAS.md` | Monitoramento de pagamentos |
| `SEGURANCA_ENTRE_LOJAS.md` | Isolamento entre lojas |
| `CAPACIDADE_100_LOJAS.md` | Capacidade e escalabilidade |

---

## 6. Comandos de Verificação Disponíveis

### Backend
```bash
python manage.py check
python manage.py verificar_dados_orfaos
python manage.py verificar_status_assinaturas
python manage.py verificar_storage_lojas
python manage.py verificar_usuario <username>
```

### Frontend
```bash
npm run lint
npm run build
npx tsc --noEmit
```

### Sistema
```bash
./scripts/verificar-sistema.sh
```

---

## 7. Resumo e Prioridades

| Prioridade | Item | Ação |
|------------|------|------|
| Alta | Vulnerabilidades npm restantes | `npm audit fix --force` (pode quebrar PWA) |
| Baixa | Ambiente local backend | Completar `pip install` no venv |
| Info | Produção | Sistema operacional ✅ |
| ✅ | ESLint | Corrigido 09/03/2026 |
