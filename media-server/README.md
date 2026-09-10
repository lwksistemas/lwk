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

URLs públicas (`/files/...`): o Django acrescenta `?e=&s=` (HMAC do path +
expiração). Nginx chama `/auth-file`. Com `MEDIA_REQUIRE_SIGNED=0` (padrão)
links antigos sem assinatura continuam válidos (WhatsApp/backup).

Snippet nginx: `nginx-media.conf`. No beta: `deploy/nginx-beta.conf`.

Salvaguardas de exclusão recursiva (`_rmtree_seguro`): só dentro de `/storage`,
nunca a raiz `/storage`, alvo sempre confinado a `/storage/{tenant}`, tenants de
sistema (superadmin/suporte) não podem ser apagados pela raiz.

## Beta

Roda como container Docker a partir deste diretório (ver `docker-compose.beta.yml`,
serviço `media`). Deploy: `docker compose -f docker-compose.beta.yml up -d --build media`.

## Produção (media.lwksistemas.com.br — host 201.23.87.251)

Roda como serviço systemd `media-api.service`, gunicorn a partir de
`/opt/media-api/app.py` (venv própria, usuário `media`). NÃO é Docker.

Sincronizar produção com este repo (após alterar `app.py`):

```bash
# no host de produção (ubuntu@201.23.87.251)
sudo cp /opt/media-api/app.py /opt/media-api/app.py.bak.$(date +%Y%m%d%H%M%S)
sudo cp <app.py-do-repo> /opt/media-api/app.py
sudo chown media:www-data /opt/media-api/app.py
sudo systemctl restart media-api
curl -s http://127.0.0.1:9000/health
```

Dependências (venv de produção): ver `requirements.txt`.
Token: definido em `Environment=MEDIA_API_TOKEN=...` no unit systemd.
