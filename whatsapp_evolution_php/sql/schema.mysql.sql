-- WhatsApp Evolution API — schema MySQL genérico (PHP backend)
-- Ajuste nomes de tabela/colunas ao seu sistema.

CREATE TABLE IF NOT EXISTS empresas (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(200) NOT NULL,
  slug VARCHAR(80) NOT NULL UNIQUE,
  telefone VARCHAR(20) DEFAULT NULL,
  ativo TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS whatsapp_config (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT UNSIGNED NOT NULL,
  provider ENUM('meta','evolution') NOT NULL DEFAULT 'evolution',
  evolution_instance_name VARCHAR(64) NOT NULL DEFAULT '',
  connection_status ENUM('disconnected','qr_pending','connected','error') NOT NULL DEFAULT 'disconnected',
  connected_phone VARCHAR(32) NOT NULL DEFAULT '',
  connected_at DATETIME NULL,
  whatsapp_numero VARCHAR(20) NOT NULL DEFAULT '',
  whatsapp_ativo TINYINT(1) NOT NULL DEFAULT 0,
  enviar_confirmacao TINYINT(1) NOT NULL DEFAULT 1,
  enviar_proposta_whatsapp TINYINT(1) NOT NULL DEFAULT 1,
  enviar_contrato_whatsapp TINYINT(1) NOT NULL DEFAULT 1,
  enviar_termo_consentimento_whatsapp TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_whatsapp_config_empresa (empresa_id),
  CONSTRAINT fk_whatsapp_config_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS whatsapp_log (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT UNSIGNED NOT NULL,
  telefone VARCHAR(20) NOT NULL,
  mensagem TEXT NOT NULL,
  status ENUM('enviado','falhou') NOT NULL,
  response_json JSON NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_whatsapp_log_empresa (empresa_id, created_at),
  CONSTRAINT fk_whatsapp_log_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tokens públicos (confirmação agenda, assinatura digital, etc.)
CREATE TABLE IF NOT EXISTS whatsapp_acao_token (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT UNSIGNED NOT NULL,
  tipo VARCHAR(40) NOT NULL COMMENT 'agenda_confirmar, assinatura_proposta, termo_consentimento',
  referencia_id BIGINT UNSIGNED NOT NULL,
  token VARCHAR(128) NOT NULL UNIQUE,
  expira_em DATETIME NOT NULL,
  usado_em DATETIME NULL,
  payload_json JSON NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_token_tipo (tipo, referencia_id),
  CONSTRAINT fk_acao_token_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
