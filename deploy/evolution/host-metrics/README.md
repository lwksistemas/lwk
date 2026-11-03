# host-metrics — VM `whatsappnova`

Agente mínimo de CPU/RAM/disco para o painel Capacidade do superadmin LWK.

## Subir na VM (169.150.0.111)

No diretório do compose Evolution (`deploy/evolution`):

1. No `.env`, defina o mesmo token usado pela API LWK para mídia/capacidade:
   ```
   CAPACIDADE_HOST_TOKEN=<mesmo MEDIA_API_TOKEN da API>
   ```
2. `docker compose up -d --build host-metrics`
3. Atualize o nginx com o `location /host-metrics` de `nginx-evolution.conf` e recarregue:
   `sudo nginx -t && sudo systemctl reload nginx`

Teste:
```
curl -s -H "Authorization: Bearer $CAPACIDADE_HOST_TOKEN" \
  https://evolution.lwksistemas.com.br/host-metrics
```
