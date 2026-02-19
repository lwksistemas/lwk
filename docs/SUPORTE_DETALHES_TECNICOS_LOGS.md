# Suporte: Detalhes técnicos e logs por chamado

## Objetivo
Quando a loja abre um chamado, o suporte poder ver contexto técnico para diagnosticar: erros e falhas do backend (Heroku), do frontend (Vercel) e do navegador do usuário. Incluir na loja um bloco "Detalhes técnicos" ao abrir o chamado.

---

## Análise de viabilidade

| Fonte | Viável? | Como |
|-------|---------|------|
| **Erros do navegador** | ✅ Sim | Capturar no frontend com `window.onerror` e `unhandledrejection`, guardar os últimos N erros em memória e enviar no campo "detalhes_tecnicos" ao criar o chamado. |
| **Detalhes da página (URL, user agent, data/hora)** | ✅ Sim | Coletar no momento de abrir o modal e enviar junto no chamado. |
| **Logs do backend (Heroku)** | ⚠️ Parcial | Heroku expõe logs via [Heroku Logs API](https://devcenter.heroku.com/articles/log-drains#api). É preciso `HEROKU_API_KEY`. Opções: (1) Endpoint interno só para suporte que chama a API Heroku e retorna últimas linhas (por tempo ou número de linhas); (2) Job que periodicamente grava logs no nosso banco (mais complexo). Recomendação: criar endpoint `GET /api/suporte/chamados/:id/logs-backend/` que usa a API Heroku para os últimos X minutos, apenas para usuários suporte/superadmin. |
| **Logs do frontend (Vercel)** | ⚠️ Parcial | A Vercel tem API para [logs de funções](https://vercel.com/docs/rest-api/endpoints#log-drains). Erros de build/deploy e de funções serverless aparecem lá. Erros de runtime no navegador **não** aparecem na Vercel. Podemos ter endpoint que busca logs Vercel por período para o suporte. |

---

## O que foi implementado

1. **Campo `detalhes_tecnicos` no chamado**  
   - Modelo `Chamado` com `detalhes_tecnicos` (TextField, opcional).  
   - API `criar-chamado/` aceita `detalhes_tecnicos` e grava no chamado.  
   - Serializer e list/detail incluem `detalhes_tecnicos`.

2. **Na loja (ao abrir chamado)**  
   - Captura de erros do navegador: `window.onerror` e `unhandledrejection`, buffer com os últimos 10 erros.  
   - No modal "Abrir chamado": bloco **"Detalhes técnicos"** com opção "Incluir erros recentes do navegador e informações da página".  
   - São enviados: URL, user agent, data/hora e lista de erros (mensagem e stack quando houver). Tudo em texto no campo `detalhes_tecnicos`.

3. **No portal do suporte**  
   - No modal de atendimento do chamado, nova seção **"Detalhes técnicos"** exibida quando `detalhes_tecnicos` estiver preenchido (texto formatado em bloco monospace).

4. **Logs Heroku / Vercel (futuro)**  
   - **Heroku:** Configurar `HEROKU_API_KEY` no backend e criar endpoint restrito a suporte/superadmin que chama a [API de log sessions](https://devcenter.heroku.com/articles/log-drains#api) e retorna as últimas linhas (ex.: últimos 5–10 minutos). No modal de atendimento, botão "Carregar logs do backend (Heroku)" que chama esse endpoint e exibe o texto.  
   - **Vercel:** Similar com token Vercel e endpoint de logs; útil para erros de API routes e build, não para erros no navegador.

---

## Resumo

- **Sim, é possível** que o suporte veja erros e falhas do backend (Heroku), do frontend (Vercel) e do navegador.  
- **Já em uso:** detalhes técnicos enviados pela loja (erros do navegador + URL, user agent, data/hora) no campo "Detalhes técnicos" do chamado e exibidos no modal de atendimento.  
- **Próximos passos opcionais:** endpoints para buscar logs Heroku e Vercel quando o suporte abrir o chamado, com exibição no mesmo modal de "Detalhes técnicos" ou em seção "Logs do backend / frontend".
