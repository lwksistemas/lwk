# Memed — Acesso de validação (homologação)

Dados de teste para preencher no formulário de validação da Memed e instruções
de uso. O acesso fica na loja **CLÍNICA VIDA** (atalho `beleza`) em ambiente de
**homologação** (`MEMED_ENVIRONMENT=integration`).

## Credenciais para o formulário da Memed

| Campo | Valor |
|-------|-------|
| URL de login | `https://lwksistemas.com.br/loja/beleza/login` |
| CPF/CNPJ da loja | `347.870.818-45` (ou sem máscara: `34787081845`) |
| Usuário | `memed.teste` |
| Senha | `MemedTeste@2026` |

## Como testar (passo a passo)

1. Acesse `https://lwksistemas.com.br/loja/beleza/login`.
2. Informe **CPF/CNPJ** `347.870.818-45`, **usuário** `memed.teste` e **senha** `MemedTeste@2026`.
3. Vá em **Clínica da Beleza → Consultas**.
4. Abra a consulta do paciente **"Paciente Teste Memed"** (status *Em atendimento*).
5. Clique no botão **Receituário** (ou **Exames**) para abrir o editor da Memed.

## Dados de teste já provisionados (loja `beleza`)

- **Profissional:** Dr. Memed Teste (vinculado ao usuário, perfil administrador)
- **Paciente:** Paciente Teste Memed
- **Consulta:** status *Em atendimento* (IN_PROGRESS), pronta para prescrever

Recriar/normalizar os dados de teste (idempotente, não duplica):

```bash
python manage.py create_memed_test_user --slug beleza
```

## Validações já realizadas (API, ambiente de produção do sistema)

- Login pela URL de atalho (`beleza`) + CPF/CNPJ → **HTTP 200**
- `GET /api/clinica-beleza/memed/token/?professional=<id>` → **HTTP 200**, token
  válido, `environment=integration`, dados da clínica preenchidos
- `GET /api/clinica-beleza/consultas/<id>/prescricoes/` → **HTTP 200**
- `GET /api/clinica-beleza/patients/<id>/prescricoes/` → **HTTP 200**

## Texto para o formulário da Memed

Campo "Forneça as instruções detalhadas para acessar a Memed no seu sistema" —
texto pronto para colar:

```
Sistema: LWK Sistemas — módulo Clínica da Beleza (prescrição digital integrada via Memed).

PASSO 1 — Acessar o login:
Abra https://lwksistemas.com.br/loja/beleza/login

PASSO 2 — Entrar com as credenciais de teste:
- CPF/CNPJ da loja: 347.870.818-45
- Usuário: memed.teste
- Senha: MemedTeste@2026

PASSO 3 — Abrir o atendimento:
No menu lateral, clique em "Clínica da Beleza" e depois em "Consultas".
Na lista, abra a consulta do paciente "Paciente Teste Memed" (status "Em atendimento").
(Caso prefira criar outro atendimento, clique em "Nova consulta", selecione o cliente, o profissional e o procedimento e confirme.)

PASSO 4 — Abrir a Memed:
Dentro da consulta, na barra de abas, clique no botão "Receituário" para abrir o módulo de prescrição de medicamentos, ou no botão "Exames" para solicitar exames. Ambos abrem o editor da Memed (módulo plataforma.prescricao) com o paciente já carregado.

Observações:
- Ambiente atual: homologação (integração). As chaves api-key/secret-key ficam somente no nosso backend; o token do prescritor é obtido no servidor e repassado ao script da Memed via data-token.
- Identificação do prescritor: por CPF do profissional (ou registro do conselho + UF). No usuário de teste é usado o prescritor padrão de homologação.
- As prescrições emitidas são registradas no histórico do paciente (aba Histórico).
```

## Observações

- Ambiente atual: **homologação** (`integration`). Ao receber as chaves de
  produção da Memed, defina as variáveis `MEMED_API_KEY_PROD` / `MEMED_SECRET_KEY_PROD`
  e troque `MEMED_ENVIRONMENT=production`.
- Como o profissional de teste não tem CPF/registro de conselho cadastrado, o
  sistema usa o **prescritor padrão de homologação** da Memed (`MEMED_PRESCRITOR_ID`).
  Para um médico real, basta cadastrar o CPF ou o registro do conselho (CRM/COREN/CRF)
  que ele é identificado automaticamente.
- A chave/segredo da Memed ficam **somente no backend** — nunca são expostas no navegador.
