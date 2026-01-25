# 📝 Passo a Passo: Configurar DNS no Registro.br

## 🎯 Objetivo

Configurar o domínio `lwksistemas.com.br` para funcionar com o sistema.

---

## 📋 Passo 1: Acessar o Painel

1. Abra o navegador
2. Acesse: https://registro.br/painel/
3. Faça login com suas credenciais
4. Você verá a lista de domínios

---

## 📋 Passo 2: Selecionar o Domínio

1. Localize `lwksistemas.com.br` na lista
2. Clique no domínio
3. Você verá as opções de gerenciamento

---

## 📋 Passo 3: Acessar Configuração DNS

Procure por uma destas opções:
- "Editar Zona"
- "Gerenciar DNS"
- "Configurar DNS"
- "DNS"

Clique nela.

---

## 📋 Passo 4: Adicionar Primeiro Registro (Raiz)

### Clique em "Adicionar Registro" ou botão "+"

Preencha:
```
┌─────────────────────────────────────┐
│ Tipo:  A                            │
│ Nome:  @  (ou deixe em branco)      │
│ Valor: 76.76.21.21                  │
│ TTL:   3600                         │
└─────────────────────────────────────┘
```

Clique em "Salvar" ou "Adicionar"

**O que faz**: Aponta `lwksistemas.com.br` para o servidor da Vercel

---

## 📋 Passo 5: Adicionar Segundo Registro (WWW)

### Clique em "Adicionar Registro" ou botão "+" novamente

Preencha:
```
┌─────────────────────────────────────┐
│ Tipo:  A                            │
│ Nome:  www                          │
│ Valor: 76.76.21.21                  │
│ TTL:   3600                         │
└─────────────────────────────────────┘
```

Clique em "Salvar" ou "Adicionar"

**O que faz**: Aponta `www.lwksistemas.com.br` para o servidor da Vercel

---

## 📋 Passo 6: Adicionar Terceiro Registro (API)

### Clique em "Adicionar Registro" ou botão "+" novamente

Preencha:
```
┌─────────────────────────────────────────────────┐
│ Tipo:  CNAME                                    │
│ Nome:  api                                      │
│ Valor: tropical-clam-2bwosmygf01khdf8s44ficex   │
│        .herokudns.com                           │
│ TTL:   3600                                     │
└─────────────────────────────────────────────────┘
```

**IMPORTANTE**: Copie o valor exatamente como está acima!

Clique em "Salvar" ou "Adicionar"

**O que faz**: Aponta `api.lwksistemas.com.br` para o servidor do Heroku

---

## 📋 Passo 7: Salvar Alterações

1. Revise os 3 registros adicionados
2. Clique em "Salvar Alterações" ou "Aplicar"
3. Confirme se solicitado

---

## 📋 Passo 8: Aguardar Propagação

⏳ **Tempo de espera**: 1 a 2 horas (pode ser até 48h)

### Como verificar se propagou:

**Opção 1: Terminal**
```bash
nslookup lwksistemas.com.br
```

Se retornar `76.76.21.21`, propagou! ✅

**Opção 2: Online**
1. Acesse: https://dnschecker.org/
2. Digite: `lwksistemas.com.br`
3. Clique em "Search"
4. Veja se aparece `76.76.21.21` em vários locais

---

## 📋 Passo 9: Atualizar Variáveis (Após DNS Propagar)

### No terminal, execute:

```bash
cd ~/lwksistemas
./atualizar_variaveis_dominio.sh
```

Isso vai atualizar:
- ALLOWED_HOSTS no Heroku
- CORS_ORIGINS no Heroku

---

## 📋 Passo 10: Atualizar Frontend

```bash
cd frontend

# Remover variável antiga (se existir)
vercel env rm NEXT_PUBLIC_API_URL production

# Adicionar nova variável
vercel env add NEXT_PUBLIC_API_URL production
```

Quando solicitado, digite:
```
https://api.lwksistemas.com.br
```

Depois faça o deploy:
```bash
vercel --prod
```

---

## 📋 Passo 11: Testar o Sistema

Abra o navegador e acesse:

### Frontend
✅ https://lwksistemas.com.br  
✅ https://www.lwksistemas.com.br

### Logins
✅ https://lwksistemas.com.br/superadmin/login  
✅ https://lwksistemas.com.br/suporte/login  
✅ https://lwksistemas.com.br/loja/harmonis/login

### Backend
✅ https://api.lwksistemas.com.br  
✅ https://api.lwksistemas.com.br/admin/

---

## ✅ Resumo Visual

```
Você está aqui → Passo 1: Acessar Registro.br
                 ↓
                 Passo 2: Selecionar domínio
                 ↓
                 Passo 3: Acessar DNS
                 ↓
                 Passo 4: Adicionar @ → 76.76.21.21
                 ↓
                 Passo 5: Adicionar www → 76.76.21.21
                 ↓
                 Passo 6: Adicionar api → tropical-clam...
                 ↓
                 Passo 7: Salvar alterações
                 ↓
                 Passo 8: Aguardar 1-2 horas ⏳
                 ↓
                 Passo 9: Executar script
                 ↓
                 Passo 10: Atualizar frontend
                 ↓
                 Passo 11: Testar sistema
                 ↓
                 🎉 PRONTO!
```

---

## 🆘 Problemas Comuns

### Não encontro onde adicionar DNS
- Procure por: "Zona DNS", "Editar DNS", "Gerenciar DNS"
- Entre em contato com suporte do Registro.br

### Erro ao adicionar CNAME
- Certifique-se de copiar o valor completo
- Não adicione ponto (.) no final
- Valor: `tropical-clam-2bwosmygf01khdf8s44ficex.herokudns.com`

### DNS não propaga
- Aguarde mais tempo (até 48h)
- Verifique se salvou as alterações
- Limpe cache DNS: `sudo systemd-resolve --flush-caches`

### Site não carrega após DNS propagar
- Aguarde mais 30 minutos
- Limpe cache do navegador (Ctrl+Shift+Del)
- Teste em modo anônimo
- Verifique se executou os passos 9 e 10

---

## 💡 Dicas

1. **Não remova registros antigos** até confirmar que os novos funcionam
2. **Copie e cole** os valores para evitar erros
3. **Aguarde pacientemente** a propagação
4. **Teste em modo anônimo** do navegador
5. **Mantenha as URLs antigas** funcionando até confirmar as novas

---

## 📞 Suporte

Se tiver dúvidas:
1. Consulte: `DNS_CONFIGURACAO_REGISTRO_BR.md`
2. Consulte: `CONFIGURAR_DOMINIO.md`
3. Entre em contato com suporte do Registro.br

---

## 🎉 Resultado Final

Após completar todos os passos, você terá:

✅ Sistema acessível via domínio próprio  
✅ URLs profissionais e amigáveis  
✅ HTTPS automático (SSL grátis)  
✅ Subdomínio API separado  
✅ Sistema completo funcionando  

**Tudo pronto para usar!** 🚀

---

**Comece agora**: Acesse https://registro.br/painel/ e siga os passos! ⏰
