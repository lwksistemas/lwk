# Boletos via Mercado Pago

O sistema passou a aceitar **Mercado Pago** como opção para gerar boletos das lojas, além do Asaas.

## Como ativar

1. **Criar aplicação no Mercado Pago**
   - Acesse: https://www.mercadopago.com.br/settings/account/applications/create-app
   - Crie uma aplicação e anote o **Access Token** (produção ou teste).

2. **Configurar no sistema**
   - **Opção A – Admin Django:** em `/admin/` → **Configuração Mercado Pago** → edite o registro, preencha o Access Token, marque **Integração habilitada** e **Usar Mercado Pago para novos boletos**.
   - **Opção B – API:**  
     - `GET /api/superadmin/mercadopago-config/` (superuser) – ver configuração atual.  
     - `PATCH /api/superadmin/mercadopago-config/` com body:  
       `{ "access_token": "SEU_TOKEN", "enabled": true, "use_for_boletos": true }`.

3. **Comportamento**
   - Com **Usar Mercado Pago para novos boletos** ativo, **novas cobranças** de lojas (nova loja ou novo boleto) passam a ser geradas via Mercado Pago (boleto bancário).
   - Lojas que já têm boleto no Asaas continuam com Asaas até que um novo boleto seja gerado (quando aí pode passar a usar MP, se a opção estiver ligada).
   - Na tela de **Assinatura** e **Financeiro** da loja, o botão de boleto continua o mesmo: para Asaas faz download do PDF; para Mercado Pago abre o link do boleto em nova aba.

## Referências

- Criar app: https://www.mercadopago.com.br/settings/account/applications/create-app  
- Integrações: https://www.mercadopago.com.br/business/integrations  
- API Pagamentos (boleto): https://www.mercadopago.com.br/developers/pt/reference/payments/_payments/post  
