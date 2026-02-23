# Análise: impacto do monitoramento Asaas + Mercado Pago com 100 lojas no Heroku

## Cenário
- 50 lojas com pagamento **Asaas**
- 50 lojas com pagamento **Mercado Pago**
- Servidor: Heroku (dyno web)

## Como o “monitoramento” funciona hoje

### Não são 2 processos em tempo real
Os dois provedores usam **webhooks (push)**. O servidor **não fica consultando** Asaas nem Mercado Pago em loop.

| Provedor      | Mecanismo              | Quem inicia a comunicação |
|---------------|------------------------|---------------------------|
| **Asaas**     | Webhook HTTP (POST)    | Asaas envia para nossa URL quando há evento (pagamento criado/atualizado/pago) |
| **Mercado Pago** | Webhook HTTP (POST) | Mercado Pago envia para nossa URL quando há evento (payment) |

Ou seja: o servidor só processa quando **recebe** uma requisição do Asaas ou do MP. Não há polling contínuo.

### Carga por evento
- **Cada webhook** = 1 request HTTP no Heroku.
- Por request: leitura do body, 1 consulta à API do provedor (só no MP, para buscar detalhes do pagamento), atualizações no banco (PagamentoLoja, FinanceiroLoja, eventualmente Loja), resposta 200.
- Tempo típico por webhook: **centenas de ms a poucos segundos** (incluindo chamada à API externa).

### Frequência esperada com 100 lojas
- Pagamentos **não** acontecem o tempo todo. Exemplo: 1 boleto pago por loja por mês ≈ 100 eventos/mês ≈ **~3 eventos/dia**.
- Pico conservador: 10–20 pagamentos/dia em horário comercial ≈ **menos de 1 request a cada 30 minutos** em média.
- Conclusão: o número de webhooks por dia é **baixo**; não há “2 sistemas em tempo real” gerando carga contínua.

## Sincronização periódica (apenas Asaas)

Existe **sync por comando** (ex.: `sync_asaas_auto`, `sync_asaas_payments`), que:
- percorre lojas com Asaas;
- para cada loja, busca pagamentos pendentes e consulta a API do Asaas para cada um.

Esse comando **não está** no `Procfile`; ou seja, **não roda sozinho** no Heroku. Só entra em cena se você:
- configurar **Heroku Scheduler** (ou cron externo) para rodar o comando de tempos em tempos, ou
- disparar manualmente.

Se usar Scheduler (ex.: a cada 15 min):
- 1 job a cada 15 min;
- 50 lojas × (1 + poucos pagamentos pendentes) → ordem de **dezenas a ~100 chamadas à API Asaas** por execução;
- execução típica: **1–3 minutos** por run;
- o Scheduler usa **one-off dyno**: sobe, roda o comando e desliga. **Não** é um processo “sempre ligado” no mesmo dyno web.

Mercado Pago **não** tem sync periódico no código; só webhook.

## Resposta direta: o servidor fica lento?

**Não**, nas condições normais:

1. **Só webhooks (sem Scheduler)**  
   - Carga extra é esporádica (poucos requests/dia por pagamento).  
   - Mesmo 50 Asaas + 50 MP: não há “2 monitores em tempo real” rodando no servidor; há só 2 endpoints que **reagem** a eventos.  
   - Impacto no dyno web é **desprezível** perto do tráfego normal da aplicação (login, dashboard, etc.).

2. **Com Heroku Scheduler para Asaas (ex.: a cada 15 min)**  
   - O trabalho pesado roda em **one-off dyno**, não no web.  
   - O dyno web continua atendendo usuários; pode haver um pico breve de uso de DB se o sync escrever muito no mesmo instante, mas ainda assim é moderado para 50 lojas.

3. **Escalabilidade**  
   - 100 lojas é pouco para esse desenho.  
   - O “monitoramento” não dobra porque são 2 provedores: a carga é proporcional ao **número de eventos (pagamentos)** e, se existir, à **frequência do sync** (ex.: 1 job a cada 15 min), não ao número de lojas “paradas” com Asaas ou MP.

## Recomendações

- **Manter** Asaas e MP por webhook; não é necessário “desligar” um para não sobrecarregar.
- Se usar sync do Asaas, preferir **Heroku Scheduler** (ou cron externo) com intervalo razoável (ex.: 15–30 min); evite intervalos muito curtos (ex.: 1 min).
- Monitorar **tempo de resposta** dos endpoints de webhook e **logs** no Heroku; se no futuro o volume de eventos crescer muito (ex.: centenas de pagamentos/dia), aí sim considerar fila (worker) ou otimizações.

## Resumo em uma frase

Com 50 lojas Asaas + 50 lojas Mercado Pago, o servidor **não** fica lento por ter “2 sistemas de monitoramento em tempo real”: ambos são baseados em webhooks (eventos esporádicos), e não há polling contínuo; a carga extra é baixa.
