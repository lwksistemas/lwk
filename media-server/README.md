# media-server — servidor de mídia LWK

API Flask que guarda fotos e PDFs dos pacientes no disco, isolados por clínica
(CPF/CNPJ) e por paciente.

Estrutura em disco:

```
/storage/{cpf_cnpj_da_clinica}/{paciente-slug}/fotos/{arquivo}
/storage/{cpf_cnpj_da_clinica}/{paciente-slug}/pdf/{arquivo}
```

`app.py` é a **fonte de verdade** — produção e beta rodam o mesmo código.

## Endpoints

- `POST   /upload/{tenant}/`                                — upload (campo `file`, `folder`)
- `DELETE /upload/{tenant}/{path}`                          — apaga arquivo (ou pasta vazia)
- `DELETE /upload/{tenant}/{path}?recursive=true`           — apaga pasta do paciente + conteúdo
- `DELETE /upload/{tenant}/?recursive=true`                 — apaga a loja inteira (`/storage/{tenant}`)
- `GET    /list/`, `/list/{tenant}/`, `/list/{tenant}/{folder}/`
- `GET    /auth-file`                                         — interno (nginx `auth_request`)
- `GET    /health`

Autenticação de API: `Authorization: Bearer <MEDIA_API_TOKEN>` (master, lista
todas as lojas) **ou** Bearer HMAC-SHA256(token, tenant) — só aquela loja.

URLs de arquivo (`/files/...`): o Django acrescenta `?e=&s=` (HMAC do path +
expiração de 2 horas na tela). Nginx chama `/auth-file`. O padrão é
`MEDIA_REQUIRE_SIGNED=1`: endereço sem assinatura recebe 401. `=0` só para
emergência, se a API ainda não estiver assinando.

Snippet nginx: `nginx-media.conf`. No beta: `deploy/nginx-beta.conf`.

Salvaguardas de exclusão recursiva (`_rmtree_seguro`): só dentro de `/storage`,
nunca a raiz `/storage`, alvo sempre confinado a `/storage/{tenant}`, tenants de
sistema (superadmin/suporte) não podem ser apagados pela raiz.

## Beta

Roda como container Docker a partir deste diretório (ver `docker-compose.beta.yml`,
serviço `media`). Deploy: `docker compose -f docker-compose.beta.yml up -d --build media`.

## Produção (media.lwksistemas.com.br — host 201.23.87.251)

Roda em **Docker** (`python:3.13-slim`), mesma imagem do beta. Nginx no host
continua em `127.0.0.1:9000`.

```bash
# no host (ubuntu@201.23.87.251) — arquivos em /opt/media-api
cd /opt/media-api
# .env com MEDIA_API_TOKEN=... e MEDIA_REQUIRE_SIGNED=1 (não versionar)
sudo docker build -t lwk-media:3.13 .
sudo docker rm -f lwk-media
sudo docker run -d --name lwk-media --restart always --memory 256m \
  -p 127.0.0.1:9000:9000 -v /storage:/storage --env-file /opt/media-api/.env \
  lwk-media:3.13
curl -s http://127.0.0.1:9000/health
```

(`docker-compose.prod.yml` existe para quando o plugin Compose estiver instalado.)
O unit systemd `media-api.service` (venv 3.12) fica desabilitado. Storage: `/storage`.
