-- Idempotente: coluna is_padrao em locais de atendimento e nomes de agenda (migration 0050).
-- Uso manual (schema da loja): SET search_path TO "loja_XXXXX", public; \i fix_is_padrao_local_nomeagenda.sql
-- Ou via Railway SSH: python manage.py ensure_local_nomeagenda_is_padrao --slug NOME

ALTER TABLE clinica_beleza_locais_atendimento
ADD COLUMN IF NOT EXISTS is_padrao BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE clinica_beleza_nomes_agenda
ADD COLUMN IF NOT EXISTS is_padrao BOOLEAN NOT NULL DEFAULT FALSE;

INSERT INTO django_migrations (app, name, applied)
SELECT 'clinica_beleza', '0050_local_nomeagenda_is_padrao', NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'clinica_beleza' AND name = '0050_local_nomeagenda_is_padrao'
);
