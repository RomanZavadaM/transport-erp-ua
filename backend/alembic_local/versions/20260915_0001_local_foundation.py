from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa

from alembic import op

revision = "20260915_local_0001"
down_revision = None
branch_labels = ("local",)
depends_on = None

UTC_NOW = sa.text("(strftime('%Y-%m-%dT%H:%M:%fZ','now'))")

PERMISSIONS: tuple[tuple[str, str, str], ...] = (
    ("user.read", "Read users", "identity"),
    ("user.create", "Create users", "identity"),
    ("user.update", "Update users", "identity"),
    ("user.status.change", "Change user status", "identity"),
    ("user.roles.manage", "Manage user roles", "identity"),
    ("role.read", "Read roles", "identity"),
    ("role.manage", "Manage roles", "identity"),
    ("permission.read", "Read permissions", "identity"),
    ("vehicle.read", "Read vehicles", "fleet"),
    ("vehicle.create", "Create vehicles", "fleet"),
    ("vehicle.update", "Update vehicles", "fleet"),
    ("vehicle.status.change", "Change vehicle status", "fleet"),
    ("vehicle_document.read", "Read vehicle documents", "fleet"),
    ("vehicle_document.manage", "Manage vehicle documents", "fleet"),
    ("odometer.read", "Read odometer", "fleet"),
    ("odometer.record", "Record odometer", "fleet"),
    ("odometer.correct", "Correct odometer", "fleet"),
    ("driver.read", "Read drivers", "drivers"),
    ("driver.read.minimum", "Read minimum driver projection", "drivers"),
    ("driver.create", "Create drivers", "drivers"),
    ("driver.update", "Update drivers", "drivers"),
    ("driver.status.change", "Change driver status", "drivers"),
    ("driver_document.read", "Read driver documents", "drivers"),
    ("driver_document.manage", "Manage driver documents", "drivers"),
    ("stop.read", "Read stops", "planning"),
    ("stop.manage", "Manage stops", "planning"),
    ("route.read", "Read routes", "planning"),
    ("route.manage", "Manage routes", "planning"),
    ("schedule.read", "Read schedules", "planning"),
    ("schedule.manage", "Manage schedules", "planning"),
    ("trip.read", "Read trips", "trips"),
    ("trip.create", "Create trips", "trips"),
    ("trip.cancel", "Cancel trips", "trips"),
    ("trip.depart", "Depart trips", "trips"),
    ("trip.complete", "Complete trips", "trips"),
    ("trip.close", "Close trips", "trips"),
    ("trip.event.create", "Create trip events", "trips"),
    ("duty.read", "Read duties", "dispatch"),
    ("duty.create", "Create duties", "dispatch"),
    ("duty.update_plan", "Update duty plan", "dispatch"),
    ("duty.vehicle.assign", "Assign vehicle", "dispatch"),
    ("duty.driver.assign", "Assign driver", "dispatch"),
    ("duty.replace_vehicle", "Replace vehicle", "dispatch"),
    ("duty.replace_driver", "Replace driver", "dispatch"),
    ("duty.depart", "Depart duty", "dispatch"),
    ("duty.return", "Return duty", "dispatch"),
    ("duty.close", "Close duty", "dispatch"),
    ("duty.cancel", "Cancel duty", "dispatch"),
    ("release.read", "Read release", "release"),
    ("release.evaluate", "Evaluate release", "release"),
    ("release.authorize", "Authorize release", "release"),
    ("medical_check.read", "Read medical checks", "release"),
    ("medical_check.perform", "Perform medical check", "release"),
    ("medical_check.invalidate", "Invalidate medical check", "release"),
    ("technical_check.read", "Read technical checks", "release"),
    ("technical_check.perform", "Perform technical check", "release"),
    ("technical_check.invalidate", "Invalidate technical check", "release"),
    ("driver_predeparture_check.read", "Read driver predeparture checks", "release"),
    ("driver_predeparture_check.perform", "Perform driver predeparture check", "release"),
    ("driver_predeparture_check.invalidate", "Invalidate driver predeparture check", "release"),
    ("waybill.read", "Read waybills", "waybill"),
    ("waybill.create", "Create waybills", "waybill"),
    ("waybill.generate", "Generate waybills", "waybill"),
    ("waybill.issue", "Issue waybills", "waybill"),
    ("waybill.return", "Return waybills", "waybill"),
    ("waybill.close", "Close waybills", "waybill"),
    ("waybill.correct", "Correct waybills", "waybill"),
    ("fuel.read", "Read fuel operations", "fuel"),
    ("fuel.record", "Record fuel operations", "fuel"),
    ("fuel.reverse", "Reverse fuel operations", "fuel"),
    ("defect.read", "Read defects", "maintenance"),
    ("defect.manage", "Manage defects", "maintenance"),
    ("maintenance.read", "Read maintenance", "maintenance"),
    ("maintenance.manage", "Manage maintenance", "maintenance"),
    ("repair.read", "Read repairs", "maintenance"),
    ("repair.manage", "Manage repairs", "maintenance"),
    ("report.operational.read", "Read operational reports", "reports"),
    ("report.management.read", "Read management reports", "reports"),
    ("report.export", "Export reports", "reports"),
    ("audit.read", "Read audit", "audit"),
    ("audit.read.own", "Read own audit", "audit"),
    ("audit.export", "Export audit", "audit"),
    ("settings.read", "Read settings", "settings"),
    ("settings.manage", "Manage settings", "settings"),
    ("template.read", "Read templates", "settings"),
    ("template.manage", "Manage templates", "settings"),
    ("numbering.manage", "Manage numbering", "settings"),
)

ADMIN_PERMISSION_CODES = {
    "user.read",
    "user.create",
    "user.update",
    "user.status.change",
    "user.roles.manage",
    "role.read",
    "role.manage",
    "permission.read",
    "settings.read",
    "settings.manage",
    "template.read",
    "template.manage",
    "numbering.manage",
    "audit.read",
    "audit.export",
}


def _stable_uuid(key: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"https://transporterp.ua/{key}"))


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("legal_name", sa.Text(), nullable=False),
        sa.Column("edrpou", sa.String(length=10), nullable=False, unique=True),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Kyiv"),
        sa.Column("default_locale", sa.String(length=5), nullable=False, server_default="uk"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("status IN ('ACTIVE','SUSPENDED')", name="ck_companies_status"),
        sa.CheckConstraint("default_locale IN ('uk','en','es','fr','de')", name="ck_companies_locale"),
        sa.CheckConstraint("length(edrpou) BETWEEN 8 AND 10", name="ck_companies_edrpou"),
        sa.UniqueConstraint("id", name="uq_companies_company_id"),
    )
    op.create_index("ix_companies_status", "companies", ["status"])

    op.create_table(
        "company_settings",
        sa.Column("company_id", sa.Text(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("settings_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_by", sa.Text(), nullable=True),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("company_id", sa.Text(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("username", sa.Text(collation="NOCASE"), nullable=False),
        sa.Column("email", sa.Text(collation="NOCASE"), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("preferred_locale", sa.String(length=5), nullable=True),
        sa.Column("driver_id", sa.Text(), nullable=True),
        sa.Column("last_login_at", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_by", sa.Text(), nullable=True),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("company_id", "username", name="uq_users_company_username"),
        sa.UniqueConstraint("company_id", "id", name="uq_users_company_id"),
        sa.CheckConstraint("status IN ('ACTIVE','SUSPENDED','DISABLED')", name="ck_users_status"),
        sa.CheckConstraint(
            "preferred_locale IS NULL OR preferred_locale IN ('uk','en','es','fr','de')",
            name="ck_users_locale",
        ),
        sa.ForeignKeyConstraint(
            ["company_id", "created_by"], ["users.company_id", "users.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["company_id", "updated_by"], ["users.company_id", "users.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ux_users_company_email",
        "users",
        ["company_id", "email"],
        unique=True,
        sqlite_where=sa.text("email IS NOT NULL"),
    )
    op.create_index("ix_users_company_status", "users", ["company_id", "status"])

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("company_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("expires_at", sa.Text(), nullable=False),
        sa.Column("revoked_at", sa.Text(), nullable=True),
        sa.Column("rotated_from_id", sa.Text(), sa.ForeignKey("user_sessions.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["company_id", "user_id"], ["users.company_id", "users.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint("expires_at > created_at", name="ck_user_sessions_expiry"),
    )
    op.create_index("ix_user_sessions_user_expiry", "user_sessions", ["user_id", "expires_at"])
    op.create_index(
        "ix_user_sessions_active_expiry",
        "user_sessions",
        ["expires_at"],
        sqlite_where=sa.text("revoked_at IS NULL"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("company_id", sa.Text(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("system_role", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=UTC_NOW),
    )
    op.create_index(
        "ux_roles_tenant_code",
        "roles",
        ["company_id", "code"],
        unique=True,
        sqlite_where=sa.text("company_id IS NOT NULL"),
    )
    op.create_index(
        "ux_roles_system_code",
        "roles",
        ["code"],
        unique=True,
        sqlite_where=sa.text("company_id IS NULL"),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("code", sa.String(length=120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=False),
    )

    op.create_table(
        "user_roles",
        sa.Column("company_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("role_id", sa.Text(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("assigned_by", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
        sa.ForeignKeyConstraint(
            ["company_id", "user_id"], ["users.company_id", "users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["company_id", "assigned_by"], ["users.company_id", "users.id"], ondelete="RESTRICT"
        ),
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Text(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", sa.Text(), sa.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.create_table(
        "api_idempotency_keys",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("company_id", sa.Text(), nullable=False),
        sa.Column("actor_user_id", sa.Text(), nullable=False),
        sa.Column("command_scope", sa.String(length=180), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body_json", sa.Text(), nullable=True),
        sa.Column("result_entity_type", sa.String(length=80), nullable=True),
        sa.Column("result_entity_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("expires_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id", "actor_user_id"], ["users.company_id", "users.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "company_id", "actor_user_id", "command_scope", "idempotency_key",
            name="uq_idempotency_scope",
        ),
        sa.CheckConstraint("expires_at > created_at", name="ck_idempotency_expiry"),
    )
    op.create_index("ix_idempotency_expiry", "api_idempotency_keys", ["expires_at"])

    op.create_table(
        "local_nodes",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("company_id", sa.Text(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("central_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )
    op.create_index(
        "uq_local_nodes_single_active",
        "local_nodes",
        ["active"],
        unique=True,
        sqlite_where=sa.text("active = 1"),
    )

    op.create_table(
        "transfer_requests",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("origin", sa.String(length=30), nullable=False),
        sa.Column("external_request_id", sa.Text(), nullable=True),
        sa.Column("rule_code", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("requested_by", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("handled_by", sa.Text(), nullable=True),
        sa.Column("handled_at", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.CheckConstraint("origin IN ('MANUAL','CENTRAL_REQUEST','RULE')", name="ck_transfer_requests_origin"),
        sa.CheckConstraint(
            "status IN ('OPEN','CONVERTED','REJECTED','CANCELLED')",
            name="ck_transfer_requests_status",
        ),
    )

    op.create_table(
        "transfer_batches",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("origin_node_id", sa.Text(), sa.ForeignKey("local_nodes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_id", sa.Text(), sa.ForeignKey("transfer_requests.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING_APPROVAL"),
        sa.Column("prepared_reason", sa.String(length=30), nullable=False),
        sa.Column("prepared_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("prepared_by", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("payload_checksum", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.Text(), nullable=True),
        sa.Column("last_attempt_at", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error_code", sa.Text(), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("acknowledged_at", sa.Text(), nullable=True),
        sa.Column("central_ack_id", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.Text(), nullable=True),
        sa.Column("cancelled_by", sa.Text(), nullable=True),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint(
            "status IN ('PENDING_APPROVAL','TRANSFERRING','FAILED','ACKNOWLEDGED','CANCELLED')",
            name="ck_transfer_batches_status",
        ),
        sa.CheckConstraint(
            "prepared_reason IN ('MANUAL','CENTRAL_REQUEST','RULE')",
            name="ck_transfer_batches_reason",
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_transfer_batches_attempts"),
        sa.CheckConstraint(
            "status NOT IN ('TRANSFERRING','FAILED','ACKNOWLEDGED') "
            "OR (approved_at IS NOT NULL AND approved_by IS NOT NULL)",
            name="ck_transfer_batches_approval",
        ),
        sa.CheckConstraint(
            "status != 'ACKNOWLEDGED' OR "
            "(acknowledged_at IS NOT NULL AND central_ack_id IS NOT NULL)",
            name="ck_transfer_batches_ack",
        ),
    )
    op.create_index("ix_transfer_batches_status_prepared", "transfer_batches", ["status", "prepared_at"])
    op.create_index("ix_transfer_batches_request", "transfer_batches", ["request_id"])
    op.create_index(
        "ux_transfer_batches_central_ack",
        "transfer_batches",
        ["central_ack_id"],
        unique=True,
        sqlite_where=sa.text("central_ack_id IS NOT NULL"),
    )

    op.create_table(
        "transfer_items",
        sa.Column("transfer_batch_id", sa.Text(), sa.ForeignKey("transfer_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("entity_version", sa.Integer(), nullable=False),
        sa.Column("payload_checksum", sa.String(length=64), nullable=False),
        sa.Column("transfer_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("transfer_batch_id", "entity_type", "entity_id"),
        sa.CheckConstraint("entity_version >= 1", name="ck_transfer_items_version"),
    )

    op.create_table(
        "transfer_delivery_queue",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("transfer_batch_id", sa.Text(), sa.ForeignKey("transfer_batches.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("available_at", sa.Text(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_attempt_at", sa.Text(), nullable=True),
        sa.Column("last_error_code", sa.Text(), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.Text(), nullable=True),
        sa.CheckConstraint("attempt_count >= 0", name="ck_transfer_delivery_attempts"),
    )
    op.create_index(
        "ix_transfer_delivery_ready",
        "transfer_delivery_queue",
        ["completed_at", "available_at"],
    )

    op.create_table(
        "record_authority",
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("authority", sa.String(length=10), nullable=False, server_default="LOCAL"),
        sa.Column("transfer_lock_batch_id", sa.Text(), sa.ForeignKey("transfer_batches.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("central_version", sa.Integer(), nullable=True),
        sa.Column("central_ack_id", sa.Text(), nullable=True),
        sa.Column("central_synced_at", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("entity_type", "entity_id"),
        sa.CheckConstraint("authority IN ('LOCAL','CENTRAL')", name="ck_record_authority_value"),
        sa.CheckConstraint(
            "authority != 'CENTRAL' OR transfer_lock_batch_id IS NULL",
            name="ck_record_authority_central_unlocked",
        ),
    )
    op.create_index("ix_record_authority_state", "record_authority", ["authority"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("occurred_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("actor_user_id", sa.Text(), nullable=True),
        sa.Column("node_id", sa.Text(), sa.ForeignKey("local_nodes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.Text(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("before_json", sa.Text(), nullable=True),
        sa.Column("after_json", sa.Text(), nullable=True),
        sa.Column("changed_fields_json", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_audit_occurred", "audit_log", ["occurred_at"])
    op.create_index("ix_audit_entity", "audit_log", ["entity_type", "entity_id", "occurred_at"])
    op.create_index("ix_audit_actor", "audit_log", ["actor_user_id", "occurred_at"])
    op.create_index("ix_audit_request", "audit_log", ["request_id"])
    op.execute(
        "CREATE TRIGGER trg_audit_log_no_update BEFORE UPDATE ON audit_log "
        "BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER trg_audit_log_no_delete BEFORE DELETE ON audit_log "
        "BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END"
    )

    op.create_table(
        "backup_runs",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("started_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("completed_at", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("backup_path", sa.Text(), nullable=False),
        sa.Column("manifest_path", sa.Text(), nullable=True),
        sa.Column("db_checksum", sa.String(length=64), nullable=True),
        sa.Column("file_count", sa.Integer(), nullable=True),
        sa.Column("backup_size_bytes", sa.Integer(), nullable=True),
        sa.Column("app_version", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.CheckConstraint("status IN ('RUNNING','SUCCESS','FAILED')", name="ck_backup_runs_status"),
    )
    op.create_index("ix_backup_runs_status_started", "backup_runs", ["status", "started_at"])

    op.create_table(
        "system_integrity_alerts",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("check_code", sa.String(length=120), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("entity_id", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.Text(), nullable=False, server_default=UTC_NOW),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("acknowledged_at", sa.Text(), nullable=True),
        sa.Column("acknowledged_by", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.Text(), nullable=True),
        sa.Column("resolution_comment", sa.Text(), nullable=True),
        sa.CheckConstraint("severity IN ('INFO','WARNING','ERROR','CRITICAL')", name="ck_integrity_severity"),
        sa.CheckConstraint("status IN ('OPEN','ACKNOWLEDGED','RESOLVED')", name="ck_integrity_status"),
    )
    op.create_index(
        "ix_integrity_status_severity_detected",
        "system_integrity_alerts",
        ["status", "severity", "detected_at"],
    )
    op.create_index("ix_integrity_code_detected", "system_integrity_alerts", ["check_code", "detected_at"])

    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.Text()),
        sa.column("code", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("domain", sa.String()),
    )
    op.bulk_insert(
        permissions_table,
        [
            {"id": _stable_uuid(f"permission/{code}"), "code": code, "description": description, "domain": domain}
            for code, description, domain in PERMISSIONS
        ],
    )

    admin_role_id = _stable_uuid("role/ADMIN")
    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Text()),
        sa.column("company_id", sa.Text()),
        sa.column("code", sa.String()),
        sa.column("name", sa.Text()),
        sa.column("system_role", sa.Boolean()),
        sa.column("active", sa.Boolean()),
    )
    op.bulk_insert(
        roles_table,
        [
            {
                "id": admin_role_id,
                "company_id": None,
                "code": "ADMIN",
                "name": "Адміністратор",
                "system_role": True,
                "active": True,
            }
        ],
    )

    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Text()),
        sa.column("permission_id", sa.Text()),
    )
    op.bulk_insert(
        role_permissions_table,
        [
            {
                "role_id": admin_role_id,
                "permission_id": _stable_uuid(f"permission/{code}"),
            }
            for code in sorted(ADMIN_PERMISSION_CODES)
        ],
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_no_delete")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_no_update")
    for table_name in (
        "system_integrity_alerts",
        "backup_runs",
        "audit_log",
        "record_authority",
        "transfer_delivery_queue",
        "transfer_items",
        "transfer_batches",
        "transfer_requests",
        "local_nodes",
        "api_idempotency_keys",
        "role_permissions",
        "user_roles",
        "permissions",
        "roles",
        "user_sessions",
        "users",
        "company_settings",
        "companies",
    ):
        op.drop_table(table_name)
