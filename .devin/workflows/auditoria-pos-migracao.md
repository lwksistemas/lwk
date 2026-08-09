---
description: Executar auditoria pós-migração de Cloudinary e prontidão DPS/RTC
---

# Auditoria pós-migração — Clínica da Beleza

Este runbook deve ser executado após deploy das correções de migrações 0066/0067, migração do Cloudinary para o servidor de mídia próprio e habilitação do NFS-e Padrão Nacional.

## Pré-requisitos

- Acesso ao servidor com o ambiente Python/Django configurado.
- Variável `MEDIA_SERVER_URL` apontando para o novo servidor de imagens (ex.: `https://media.lwksistemas.com.br`).
- Banco PostgreSQL com schemas tenants.

## Passo 1 — Verificar migrações 0066/0067 em todos os tenants

```bash
python manage.py check_clinica_migrations
```

Se houver schemas pendentes:

```bash
python manage.py check_clinica_migrations --fix
python manage.py check_clinica_migrations
```

### O que é verificado

- `0066_paciente_foto_rename_db_columns`: colunas `url` e `public_id` na tabela `clinica_beleza_paciente_fotos`.
- `0067_nfse_config_padrao_nacional_fields`: campos de configuração DPS/RTC na tabela `clinica_beleza_clinicabelezanfseconfig`.

## Passo 2 — Auditar URLs legadas do Cloudinary

```bash
python manage.py audit_cloudinary_urls --csv /tmp/cloudinary_restantes.csv
```

Se o CSV tiver registros:

1. Notificar a clínica/tenant.
2. Requisitar re-upload das fotos pelo painel ou link QR.
3. Após backfill, re-executar o comando até o CSV ficar vazio.

## Passo 3 — Auditar prontidão DPS/RTC

```bash
python manage.py audit_dps_nacional --problemas
```

Para exportar:

```bash
python manage.py audit_dps_nacional --csv /tmp/dps_pendentes.csv --json /tmp/dps_pendentes.json
```

### Critérios de prontidão

- Configuração `padrao_nacional` ou `issnet_usar_padrao_nacional` habilitada.
- Provedor NFS-e compatível com nacional (`nacional` / `issnet`).
- Inscrição municipal (IM) preenchida.
- Códigos de tributação nacional e municipal preenchidos.
- Código do município nacional preenchido.
- Certificado A1 ativo configurado.
- CPF/CNPJ da loja preenchido.

## Passo 4 — Validar upload de fotos pelo painel

1. Acesse uma consulta em andamento (`IN_PROGRESS` ou `RECEBER`).
2. Clique em **Adicionar foto** e selecione uma imagem.
3. Confirme que a URL salva começa com `https://media.lwksistemas.com.br/files/{cnpj}/fotos/`.
4. Tente enviar uma URL externa via API — deve retornar `400` com mensagem de URL inválida.

## Passo 5 — Validar upload público via QR

1. Gere o QR code no painel.
2. Acesse o link público e envie uma foto pelo celular.
3. Confirme que a foto aparece no painel e a URL é do media server.

## Rollback / ajustes

- Para reverter a validação anti-Cloudinary, edite `backend/clinica_beleza/foto_paciente_service/validation.py`.
- Para alterar o endpoint do servidor de mídia, ajuste a variável de ambiente `MEDIA_SERVER_URL`.
