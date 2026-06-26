ALTER TABLE clinica_beleza_produtoestoque
ADD COLUMN IF NOT EXISTS dias_alerta_validade INTEGER NOT NULL DEFAULT 90;

INSERT INTO django_migrations (app, name, applied)
SELECT 'clinica_beleza', '0051_produto_dias_alerta_validade', NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'clinica_beleza' AND name = '0051_produto_dias_alerta_validade'
);
