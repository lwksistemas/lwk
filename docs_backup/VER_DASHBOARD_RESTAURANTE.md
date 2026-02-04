# Ver as melhorias do Dashboard Restaurante em produção

Se em **https://lwksistemas.com.br/loja/casa5889/dashboard** você ainda vê só:
- título "Dashboard - Restaurante"
- 4 cards (Pedidos Hoje, Mesas Ocupadas, Cardápio, Faturamento)
- **sem** a seção "🚀 Ações Rápidas" com os botões (Cardápio, Mesas, Pedidos, Delivery, PDV, Nota Fiscal, Estoque, Balança, Funcionários)

então o site está servindo uma **versão antiga** do frontend (cache ou deploy não atualizado).

---

## 1. Garantir que o frontend foi deployado (Vercel)

O commit com o dashboard Restaurante completo precisa estar no repositório que o Vercel usa.

```bash
# Na raiz do projeto
git status
git log -1 --oneline
# Deve aparecer algo como: feat(restaurante): dashboard completo ...
```

Se o commit **não** foi enviado para o remoto:

```bash
git push origin master
```

Aguarde **2–3 minutos** para o Vercel terminar o build e publicar.

---

## 2. Forçar o navegador a carregar a versão nova (limpar cache)

O [README](README.md) cita cache agressivo. Faça **uma** das opções:

**Opção A – Página de forçar atualização (recomendado)**  
1. Abra: **https://lwksistemas.com.br/forcar-atualizacao**  
2. Espere a mensagem de conclusão.  
3. Acesse de novo: **https://lwksistemas.com.br/loja/casa5889/dashboard**

**Opção B – Recarregar forçado**  
- **Chrome/Edge:** `Ctrl+Shift+R` (Windows/Linux) ou `Cmd+Shift+R` (Mac).  
- Ou abra o dashboard em **aba anônima** ou em **outro navegador**.

---

## 3. O que você deve ver após a atualização

- Título: **"Dashboard - {nome da loja}"** (ex.: "Dashboard - Casa5889"), não só "Dashboard - Restaurante".
- Bloco **"🚀 Ações Rápidas"** com 9 botões: Cardápio, Mesas, Pedidos, Delivery, PDV, Nota Fiscal, Estoque, Balança, Funcionários.
- Os 4 cards de estatísticas (Pedidos Hoje, Mesas Ocupadas, Cardápio, Faturamento) continuam; os números podem vir da API.
- Texto de dica: "💡 Dashboard Restaurante — Cardápio, Mesas, Pedidos, Delivery, PDV, NF, Estoque, Balança e Funcionários".

Se isso aparecer, as melhorias do dashboard Restaurante estão ativas em produção.

---

## 4. Se ainda não aparecer

- Confirme no **Vercel** (Dashboard → Deployments) que o último deploy concluiu **depois** do commit do dashboard Restaurante.
- Teste em **aba anônima** ou outro navegador para descartar cache local.
- Verifique se a loja **casa5889** é do tipo **Restaurante** no painel superadmin (só lojas desse tipo usam o novo template).
