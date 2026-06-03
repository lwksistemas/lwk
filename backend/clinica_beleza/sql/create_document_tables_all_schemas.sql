-- ============================================================================
-- SQL para criar tabelas de DocumentTemplate e DocumentoClinico
-- em TODOS os schemas de lojas ativas.
--
-- Uso em produção (Railway):
--   npx railway run python manage.py ensure_document_templates_tables
--
-- Ou executar este SQL diretamente no banco (substituir <SCHEMA> pelo schema
-- de cada loja, ex: loja_12345678000190):
-- ============================================================================

-- Para cada schema de loja, executar:
-- SET search_path TO <SCHEMA>;

-- 1. Tabela: clinica_beleza_document_templates
CREATE TABLE IF NOT EXISTS clinica_beleza_document_templates (
    id BIGSERIAL PRIMARY KEY,
    loja_id INTEGER NOT NULL,
    nome VARCHAR(200) NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    conteudo TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    professional_id BIGINT NOT NULL,
    CONSTRAINT fk_document_template_professional
        FOREIGN KEY (professional_id)
        REFERENCES clinica_beleza_professional(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_document_templates_loja_id
    ON clinica_beleza_document_templates(loja_id);

CREATE INDEX IF NOT EXISTS idx_document_templates_professional_id
    ON clinica_beleza_document_templates(professional_id);

-- 2. Tabela: clinica_beleza_documentos_clinicos
CREATE TABLE IF NOT EXISTS clinica_beleza_documentos_clinicos (
    id BIGSERIAL PRIMARY KEY,
    loja_id INTEGER NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    titulo VARCHAR(200) NOT NULL DEFAULT '',
    conteudo TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    consulta_id BIGINT NOT NULL,
    patient_id BIGINT NOT NULL,
    professional_id BIGINT,
    template_id BIGINT,
    CONSTRAINT fk_documento_clinico_consulta
        FOREIGN KEY (consulta_id)
        REFERENCES clinica_beleza_consultas(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_documento_clinico_patient
        FOREIGN KEY (patient_id)
        REFERENCES clinica_beleza_patient(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_documento_clinico_professional
        FOREIGN KEY (professional_id)
        REFERENCES clinica_beleza_professional(id)
        ON DELETE SET NULL,
    CONSTRAINT fk_documento_clinico_template
        FOREIGN KEY (template_id)
        REFERENCES clinica_beleza_document_templates(id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_documentos_clinicos_loja_id
    ON clinica_beleza_documentos_clinicos(loja_id);

CREATE INDEX IF NOT EXISTS idx_documentos_clinicos_consulta_id
    ON clinica_beleza_documentos_clinicos(consulta_id);

CREATE INDEX IF NOT EXISTS idx_documentos_clinicos_patient_id
    ON clinica_beleza_documentos_clinicos(patient_id);

CREATE INDEX IF NOT EXISTS idx_documentos_clinicos_professional_id
    ON clinica_beleza_documentos_clinicos(professional_id);

-- 3. Marcar migration como aplicada (evita conflito com migrate_all_lojas)
INSERT INTO django_migrations (app, name, applied)
SELECT 'clinica_beleza', '0029_document_templates_and_documentos', NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'clinica_beleza' AND name = '0029_document_templates_and_documentos'
);
