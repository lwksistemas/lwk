# ⚡ AÇÃO IMEDIATA: Configurar Domínio

## 🎯 O que fazer AGORA

### 1. Acesse o Registro.br
👉 https://registro.br/painel/dominios/?dominio=lwksistemas.com.br

### 2. Adicione 3 Registros DNS

Copie e cole exatamente como está:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGISTRO 1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tipo:  A
Nome:  @
Valor: 76.76.21.21
TTL:   3600
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGISTRO 2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tipo:  A
Nome:  www
Valor: 76.76.21.21
TTL:   3600
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGISTRO 3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tipo:  CNAME
Nome:  api
Valor: tropical-clam-2bwosmygf01khdf8s44ficex.herokudns.com
TTL:   3600
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3. Salve as Alterações

### 4. Aguarde 1-2 horas ⏳

---

## ⏰ Depois que o DNS propagar

### Execute estes comandos:

```bash
# 1. Atualizar backend
./atualizar_variaveis_dominio.sh

# 2. Atualizar frontend
cd frontend
vercel env add NEXT_PUBLIC_API_URL production
# Digite: https://api.lwksistemas.com.br

# 3. Deploy
vercel --prod
```

---

## ✅ Pronto!

Seu sistema estará em:
- **https://lwksistemas.com.br**
- **https://api.lwksistemas.com.br**

---

## 📚 Guias Detalhados

Se precisar de ajuda:
- **Passo a passo visual**: `PASSO_A_PASSO_DNS.md`
- **Guia completo DNS**: `DNS_CONFIGURACAO_REGISTRO_BR.md`
- **Guia geral**: `CONFIGURAR_DOMINIO.md`

---

## 🚀 Ação Imediata

**Configure o DNS AGORA!**

👉 https://registro.br/painel/dominios/?dominio=lwksistemas.com.br

Adicione os 3 registros acima e aguarde a propagação.

---

**Tempo estimado**: 5 minutos para configurar + 1-2 horas de propagação
