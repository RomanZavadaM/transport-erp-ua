CREATE TABLE companies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    legal_name text NOT NULL,
    edrpou varchar(10) NOT NULL UNIQUE,
    timezone varchar(64) NOT NULL DEFAULT 'Europe/Kyiv',
    default_locale varchar(5) NOT NULL DEFAULT 'uk',
    status varchar(20) NOT NULL DEFAULT 'ACTIVE',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT ck_companies_status CHECK (status IN ('ACTIVE','SUSPENDED')),
    CONSTRAINT ck_companies_locale CHECK (default_locale IN ('uk','en','es','fr','de')),
    CONSTRAINT ck_companies_edrpou CHECK (char_length(edrpou) BETWEEN 8 AND 10),
    CONSTRAINT uq_companies_company_id UNIQUE (id)
);
CREATE INDEX ix_companies_status ON companies(status);

CREATE TABLE company_settings (
    company_id uuid PRIMARY KEY REFERENCES companies(id) ON DELETE RESTRICT,
    settings jsonb NOT NULL DEFAULT '{}'::jsonb,
    updated_at timestamptz NOT NULL DEFAULT now(),
    updated_by uuid NULL,
    row_version bigint NOT NULL DEFAULT 1
);

CREATE TABLE depots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    code varchar(30) NOT NULL,
    name text NOT NULL,
    address text NULL,
    timezone varchar(64) NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_depots_company_code UNIQUE (company_id, code),
    CONSTRAINT uq_depots_company_id UNIQUE (company_id, id)
);
CREATE INDEX ix_depots_company_active ON depots(company_id, active);

CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    username citext NOT NULL,
    email citext NULL,
    password_hash text NOT NULL,
    status varchar(20) NOT NULL DEFAULT 'ACTIVE',
    preferred_locale varchar(5) NULL,
    driver_id uuid NULL,
    last_login_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    updated_by uuid NULL,
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_users_company_username UNIQUE (company_id, username),
    CONSTRAINT uq_users_company_id UNIQUE (company_id, id),
    CONSTRAINT ck_users_status CHECK (status IN ('ACTIVE','SUSPENDED','DISABLED')),
    CONSTRAINT ck_users_locale CHECK (
        preferred_locale IS NULL OR preferred_locale IN ('uk','en','es','fr','de')
    ),
    CONSTRAINT fk_users_created_by FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_users_updated_by FOREIGN KEY (company_id, updated_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT
);
CREATE UNIQUE INDEX ux_users_company_email
    ON users(company_id, email) WHERE email IS NOT NULL;
CREATE INDEX ix_users_company_status ON users(company_id, status);

ALTER TABLE company_settings
    ADD CONSTRAINT fk_company_settings_updated_by
    FOREIGN KEY (company_id, updated_by)
    REFERENCES users(company_id, id) ON DELETE RESTRICT;

CREATE TABLE user_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    user_id uuid NOT NULL,
    token_hash char(64) NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz NULL,
    rotated_from_id uuid NULL REFERENCES user_sessions(id) ON DELETE RESTRICT,
    ip_address inet NULL,
    user_agent text NULL,
    CONSTRAINT fk_user_sessions_user FOREIGN KEY (company_id, user_id)
        REFERENCES users(company_id, id) ON DELETE CASCADE,
    CONSTRAINT ck_user_sessions_expiry CHECK (expires_at > created_at)
);
CREATE INDEX ix_user_sessions_user_expiry ON user_sessions(user_id, expires_at);
CREATE INDEX ix_user_sessions_active_expiry ON user_sessions(expires_at) WHERE revoked_at IS NULL;

CREATE TABLE roles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NULL REFERENCES companies(id) ON DELETE RESTRICT,
    code varchar(80) NOT NULL,
    name text NOT NULL,
    system_role boolean NOT NULL DEFAULT false,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ux_roles_tenant_code ON roles(company_id, code) WHERE company_id IS NOT NULL;
CREATE UNIQUE INDEX ux_roles_system_code ON roles(code) WHERE company_id IS NULL;

CREATE TABLE permissions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(120) NOT NULL UNIQUE,
    description text NOT NULL,
    domain varchar(50) NOT NULL
);

CREATE TABLE user_roles (
    company_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role_id uuid NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at timestamptz NOT NULL DEFAULT now(),
    assigned_by uuid NULL,
    PRIMARY KEY (user_id, role_id),
    CONSTRAINT fk_user_roles_user FOREIGN KEY (company_id, user_id)
        REFERENCES users(company_id, id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_assigned_by FOREIGN KEY (company_id, assigned_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT
);

CREATE TABLE role_permissions (
    role_id uuid NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id uuid NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE api_idempotency_keys (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    actor_user_id uuid NOT NULL,
    command_scope varchar(180) NOT NULL,
    idempotency_key varchar(200) NOT NULL,
    request_hash char(64) NOT NULL,
    response_status integer NULL,
    response_body jsonb NULL,
    result_entity_type varchar(80) NULL,
    result_entity_id uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    CONSTRAINT fk_idempotency_actor FOREIGN KEY (company_id, actor_user_id)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_idempotency_scope UNIQUE (
        company_id, actor_user_id, command_scope, idempotency_key
    ),
    CONSTRAINT ck_idempotency_expiry CHECK (expires_at > created_at)
);
CREATE INDEX ix_idempotency_expiry ON api_idempotency_keys(expires_at);
