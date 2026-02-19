# Como Sincronizar Profissionais Pendentes

## Situação Atual

Há **3 profissionais** na fila de sincronização aguardando para serem enviados ao servidor:

1. **Dra. Ivone Felix** (ID: 15)
   - Especialidade: Dermatologista
   - Telefone: 15 98765 2654
   - Email: pjluiz25@hotmail.com
   - Criar acesso: Sim (perfil profissional)

2. **Fabio Felix** (ID: 16)
   - Especialidade: Esteticista
   - Telefone: 16 98769 2098
   - Sem email

3. **Dr. Fabio Felix** (ID: 17)
   - Especialidade: Esteticista
   - Telefone: 16 98769 2098
   - Sem email

## Como Sincronizar

### Opção 1: Sincronização Manual (Recomendado)

1. **Acesse qualquer página da clínica** (ex: Agenda, Profissionais, Dashboard)
   - URL: https://lwksistemas.com.br/loja/clinica-luiz-000172/agenda

2. **Localize o indicador de status** no canto superior direito
   - Você verá: `🟢 Online` e `3 na fila`

3. **Clique no botão de sincronização** (ícone de setas circulares 🔄)
   - O botão ficará girando durante a sincronização
   - Aguarde a mensagem de confirmação

4. **Verifique o resultado**
   - Mensagem de sucesso: "✅ Sincronização concluída! 3 itens sincronizados com sucesso."
   - Se houver erro: Verifique o console (F12) para detalhes

### Opção 2: Sincronização Automática

O sistema sincroniza automaticamente quando:
- A internet volta após estar offline
- Você recarrega a página estando online

### Opção 3: Ver Detalhes da Fila

1. **Clique no botão de informações** (ícone ℹ️)
2. **Visualize todos os itens** na fila com seus detalhes
3. **Feche o modal** quando terminar

## Possíveis Problemas

### Problema 1: Profissional Duplicado
**Sintoma**: Erro ao sincronizar dizendo que o profissional já existe

**Causa**: Você pode ter criado o mesmo profissional duas vezes (IDs 16 e 17 são muito similares)

**Solução**:
1. Clique no botão de lixeira (🗑️) para limpar a fila
2. Acesse a lista de profissionais
3. Verifique se os profissionais já foram criados
4. Se necessário, crie novamente (apenas uma vez)

### Problema 2: Email Inválido
**Sintoma**: Erro ao sincronizar Dra. Ivone Felix

**Causa**: O email `pjluiz25@hotmail.com` pode já estar em uso ou ser inválido

**Solução**:
1. Limpe a fila (botão 🗑️)
2. Edite o profissional com um email diferente
3. Ou remova o email se não for necessário criar acesso

### Problema 3: Telefone Duplicado
**Sintoma**: Erro dizendo que o telefone já está em uso

**Causa**: O sistema pode não permitir telefones duplicados

**Solução**:
1. Verifique se já existe um profissional com esse telefone
2. Use telefones diferentes para cada profissional
3. Ou remova o telefone se não for obrigatório

## Verificar Sincronização

Após sincronizar com sucesso:

1. **Acesse a lista de profissionais**
   - URL: https://lwksistemas.com.br/loja/clinica-luiz-000172/clinica-beleza/profissionais

2. **Verifique se os 3 profissionais aparecem**
   - Dra. Ivone Felix
   - Fabio Felix
   - Dr. Fabio Felix

3. **Configure os horários de trabalho**
   - Clique em "Horários de trabalho" para cada profissional
   - Defina os dias e horários que cada um trabalha
   - Defina os intervalos (almoço)

4. **Verifique na agenda**
   - Acesse: https://lwksistemas.com.br/loja/clinica-luiz-000172/agenda
   - Selecione cada profissional no dropdown
   - Verifique se os horários e intervalos aparecem corretamente

## Logs de Debug

Ao sincronizar, abra o Console (F12) para ver logs detalhados:

```
🔄 [offline] Sincronização manual iniciada...
📋 [offline-sync] 3 itens pendentes na fila
🔄 [offline-sync] Processando profissional (key: 15)...
📤 [offline-sync] Enviando profissional para /professionals/
✅ [offline-sync] Profissional sincronizado com sucesso
🔄 [offline-sync] Processando profissional (key: 16)...
📤 [offline-sync] Enviando profissional para /professionals/
✅ [offline-sync] Profissional sincronizado com sucesso
🔄 [offline-sync] Processando profissional (key: 17)...
📤 [offline-sync] Enviando profissional para /professionals/
✅ [offline-sync] Profissional sincronizado com sucesso
✅ [offline] Sincronização manual concluída: 3 enviados, 0 erros
```

Se houver erros, os logs mostrarão detalhes como:
- Campos inválidos
- Valores duplicados
- Problemas de validação

## Limpar Fila (Se Necessário)

Se os profissionais já foram criados manualmente ou se houver erros persistentes:

1. **Clique no botão de lixeira** (🗑️)
2. **Confirme a ação** (os dados não sincronizados serão perdidos)
3. **Verifique se a fila foi limpa** (contador deve mostrar "0 na fila")

⚠️ **ATENÇÃO**: Limpar a fila remove permanentemente os dados não sincronizados!

## Observações Importantes

### Sobre os Profissionais Duplicados
Você tem dois profissionais muito similares:
- **Fabio Felix** (ID: 16)
- **Dr. Fabio Felix** (ID: 17)

Ambos têm:
- Mesma especialidade: Esteticista
- Mesmo telefone: 16 98769 2098
- Sem email

**Recomendação**: Decida qual manter e limpe a fila para evitar duplicação. Depois crie apenas um deles.

### Sobre Criar Acesso
A **Dra. Ivone Felix** está configurada para criar acesso automático com perfil "profissional". Isso significa que:
- Um usuário será criado automaticamente
- Ela poderá fazer login no sistema
- Terá acesso apenas aos seus próprios agendamentos

Se não quiser criar acesso, limpe a fila e recrie sem a opção `criar_acesso: true`.

## Próximos Passos

Após sincronizar os profissionais:

1. ✅ Configure horários de trabalho para cada um
2. ✅ Configure intervalos (almoço)
3. ✅ Teste a agenda selecionando cada profissional
4. ✅ Verifique se os logs de debug mostram os horários corretos
5. ✅ Crie agendamentos de teste para validar o sistema
