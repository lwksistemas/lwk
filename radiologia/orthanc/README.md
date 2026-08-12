# Orthanc + OHIF (VM de imagens)

Stack PACS LWK. **Não rode no mesmo host do ERP em produção.**

Host alvo produção: `201.23.87.251` (media.lwksistemas.com.br).

**Beta (agora):** Orthanc no ERP (`201.23.81.50`) via overlay compose — VM imagens sem SSH ainda.

```bash
# no servidor ERP (201.23.81.50)
cd /opt/lwk-erp
git pull origin staging
bash scripts/setup-orthanc-beta.sh
```

## Subir (VM imagens — quando SSH disponível)

```bash
# na máquina de desenvolvimento
scp -r radiologia/orthanc deploy@201.23.87.251:/opt/lwk-orthanc

ssh deploy@201.23.87.251
cd /opt/lwk-orthanc
cp .env.example .env
# edite orthanc.json → RegisteredUsers.lwk (senha forte)
docker compose up -d
```

## Django (ERP em 201.23.81.50)

```
ORTHANC_URL=http://201.23.87.251:8042
ORTHANC_USER=lwk
ORTHANC_PASSWORD=...
ORTHANC_WORKLISTS_DIR=/var/lib/orthanc/worklists   # mesmo volume/NFS do compose
RADIOLOGIA_DICOM_UID_ROOT=1.2.826.0.1.3680043.10.742.1
```

O RIS grava arquivos `.wl` (DICOM Modality Worklist) + `.xml` (debug) nesse diretório.
O plugin Worklists do Orthanc lê os `.wl`.

## Teste rápido

```bash
curl -u lwk:SENHA http://127.0.0.1:8042/system
# DCMTK:
# echoscu 127.0.0.1 4242 -aec LWKPACS
# findscu -W 127.0.0.1 4242 -aec LWKPACS -k 0008,0050=
```

OHIF local: `http://VM:3005`. Em produção configure `ohif-app-config.js` para o proxy
`https://api.lwksistemas.com.br/api/radiologia/dicomweb/` (nunca Orthanc público sem tenant).
