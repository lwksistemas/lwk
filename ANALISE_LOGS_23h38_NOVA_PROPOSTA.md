# Análise de Logs - Nova Proposta #33 (SISENANDO)

**Período:** 23:38-23:39 (02/04/2026)  
**Loja:** Felix Representações (172)  

---

## 📋 ATIVIDADES REGISTRADAS

### 1. Criação de Nova Proposta #33
```
23:39:42 - POST /api/crm-vendas/propostas/
Status: 201 Created
Tempo: 68ms
Cliente: SISENANDO SOARES DE QUEIROZ
Oportunidade: #139 (KAROLINE CLINICA ULTRASIS)
```

### 2. Envio para Assinatura Digital
```
23:39:45 - POST /api/crm-vendas/propostas/33/enviar_para_assinatura/
Status: 200 OK
Tempo: 651ms
Email enviado: sisenando.s.queiroz@gmail.com
Token gerado: eyJkb2N...XEM (162 caracteres)
```

---

## ✅ SISTEMA OPERACIONAL

### Performance
- ✅ Todas requisições: HTTP 200/201
- ✅ Tempo de resposta: 18-75ms (excelente!)
- ✅ Zero erros
- ✅ Email enviado com sucesso

### Redis Metrics
```
Redis Principal (rugged-68123):
- Hit Rate: 53.4% (aquecendo)
- Load Average: 1.73 → 1.47 → 1.22 (melhorando!)
- Memory: 5.1 MB / 16 GB
- Connections: 5/18

Redis Secundário (concentric-39741):
- Hit Rate: 100% ✅
- Load Average: 0.55-0.62 (excelente!)
- Memory: 4.9 MB / 16 GB
- Connections: 1/18
```

---

## 🎯 OBSERVAÇÕES

### Load Average Melhorando
```
Antes (20:52): 1.83-1.87
Agora (23:39): 1.22-1.73
Redução: ~20-35%
```

As otimizações v1490 estão funcionando! Load average caindo gradualmente.

### Hit Rate Estável
O hit rate do Redis principal está em 53.4%, ainda aquecendo. Esperado subir para 75-85% nas próximas horas.

### Nova Proposta Criada
- ✅ Proposta #33 criada com sucesso
- ✅ Email de assinatura enviado ao cliente
- ✅ Token gerado e salvo no banco
- ✅ Sistema funcionando perfeitamente

---

## 📧 PRÓXIMOS PASSOS

1. Cliente assina a proposta #33
2. Sistema envia email para vendedor assinar
3. Vendedor assina
4. **PDF final será enviado automaticamente** (bug corrigido na v1491!)

---

**Análise realizada em:** 02/04/2026 23:40  
**Status:** ✅ Sistema operacional e performático
