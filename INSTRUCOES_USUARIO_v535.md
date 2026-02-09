# Instruções para Resolver o Problema de Bloqueio - v535

## 🎯 Problema Identificado

Você está tentando criar um bloqueio de agenda, mas o sistema está retornando erro 500. O problema é que o **navegador está com cache desatualizado** e está enviando IDs de profissionais incorretos.

### Evidência
- Sua loja tem apenas **2 profissionais**: Marina Souza e Nayara
- Mas o sistema está tentando usar **profissional_id=4** que não existe na sua loja
- Isso acontece porque o navegador armazenou dados antigos em cache

## ✅ Solução Imediata (FAÇA AGORA)

### Opção 1: Hard Refresh (Mais Rápido) ⚡
1. Acesse: https://lwksistemas.com.br/loja/teste-5889/dashboard
2. Pressione **`Ctrl + Shift + R`** (Windows/Linux) ou **`Cmd + Shift + R`** (Mac)
3. Aguarde a página recarregar completamente
4. Tente criar o bloqueio novamente

### Opção 2: Limpar Cache Manualmente 🧹
1. Abra o navegador
2. Pressione **F12** para abrir DevTools
3. Clique com **botão direito** no botão de reload (🔄)
4. Selecione **"Limpar cache e recarregar forçadamente"**
5. Tente criar o bloqueio novamente

### Opção 3: Aba Anônima 🕵️
1. Abra uma **aba anônima/privada** (Ctrl+Shift+N no Chrome)
2. Acesse: https://lwksistemas.com.br/loja/teste-5889/dashboard
3. Faça login novamente
4. Tente criar o bloqueio

## 🔍 Como Verificar se Funcionou

Após limpar o cache:

1. **Abra DevTools** (F12)
2. Vá na aba **"Network"** (Rede)
3. Acesse a página do calendário
4. Procure pela requisição **`/api/clinica/profissionais/`**
5. Clique nela e veja a resposta
6. **Verifique os IDs** dos profissionais retornados

Exemplo esperado:
```json
[
  {"id": 123, "nome": "Marina Souza", "especialidade": "Fisioterapeuta"},
  {"id": 124, "nome": "Nayara", "especialidade": "Dermatologista"}
]
```

7. Agora tente **criar um bloqueio** selecionando Marina
8. Na aba Network, procure pela requisição **`POST /api/clinica/bloqueios/`**
9. Clique nela e veja o **Payload** (dados enviados)
10. **Confirme** que o `profissional_id` é o mesmo ID que apareceu na lista (ex: 123, não 4)

## ✨ Melhorias Implementadas (v535)

Implementamos melhorias para evitar que isso aconteça novamente:

### Backend (v527)
- ✅ **Validação robusta**: Agora o sistema consulta diretamente o banco de dados da sua loja
- ✅ **Logs detalhados**: Registra todas as tentativas de criar bloqueio para debug
- ✅ **Mensagem de erro clara**: Se o problema acontecer, você verá uma mensagem explicando o que fazer

### Frontend (Deployado)
- ✅ **Validação antes de enviar**: Verifica se o profissional selecionado existe na lista
- ✅ **Mensagem de erro detalhada**: Mostra exatamente qual é o problema
- ✅ **Instrução de cache**: Se detectar problema, instrui a limpar o cache

## 🧪 Teste Completo

Após limpar o cache, teste o seguinte:

1. **Criar bloqueio para Marina**:
   - Tipo: Período Específico
   - Profissional: Marina Souza
   - Data: Amanhã
   - Horário: 14:00 - 16:00
   - Motivo: Teste de bloqueio
   - ✅ Deve funcionar

2. **Criar bloqueio para todos**:
   - Tipo: Dia Completo
   - Profissional: (deixar em branco)
   - Data: Próxima semana
   - Motivo: Feriado
   - ✅ Deve funcionar

3. **Verificar no calendário**:
   - Os bloqueios devem aparecer em vermelho
   - Não deve permitir criar agendamento nos horários bloqueados
   - ✅ Deve funcionar

## ❓ Se Ainda Não Funcionar

Se após limpar o cache o problema persistir:

1. **Tire um print** da tela de "Gerenciar Profissionais" mostrando os IDs
2. **Abra DevTools** (F12) → Aba Network
3. **Tente criar o bloqueio**
4. **Tire um print** da requisição POST mostrando o payload enviado
5. **Tire um print** da resposta de erro
6. **Me envie** os prints para análise

## 📊 Informações Técnicas

### Arquitetura Multi-Tenant
O sistema usa **schemas separados** no PostgreSQL para cada loja:
- Cada loja tem sua própria tabela de profissionais
- Os IDs são independentes entre lojas
- O profissional ID 4 pode existir em outra loja, mas não na sua

### Por que aconteceu?
- O navegador armazenou em cache a lista de profissionais de outra loja
- Quando você trocou de loja, o cache não foi atualizado
- O frontend mostrou os nomes corretos (Marina e Nayara) mas enviou IDs antigos (4 e 5)

### Como evitamos?
- Validação no frontend antes de enviar
- Validação no backend consultando diretamente o banco
- Mensagens de erro claras instruindo a limpar cache
- Logs detalhados para debug

## 🎉 Conclusão

O problema é **cache do navegador**. A solução é **limpar o cache** (Ctrl+Shift+R).

As melhorias implementadas garantem que:
1. Se acontecer novamente, você verá uma mensagem clara
2. O sistema valida antes de tentar salvar
3. Temos logs detalhados para debug

**Faça o hard refresh agora e teste!** 🚀
