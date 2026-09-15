CREATE OR REPLACE FUNCTION deny_row_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION USING
        MESSAGE = TG_TABLE_NAME || ' is append-only; ' || TG_OP || ' is not allowed',
        ERRCODE = '55000';
END;
$$;

CREATE TRIGGER trg_audit_log_immutable
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION deny_row_mutation();
CREATE TRIGGER trg_audit_seals_immutable
    BEFORE UPDATE OR DELETE ON audit_partition_seals
    FOR EACH ROW EXECUTE FUNCTION deny_row_mutation();
CREATE TRIGGER trg_trip_events_immutable
    BEFORE UPDATE OR DELETE ON trip_events
    FOR EACH ROW EXECUTE FUNCTION deny_row_mutation();
CREATE TRIGGER trg_duty_events_immutable
    BEFORE UPDATE OR DELETE ON duty_events
    FOR EACH ROW EXECUTE FUNCTION deny_row_mutation();
CREATE TRIGGER trg_trip_snapshots_immutable
    BEFORE UPDATE OR DELETE ON trip_actual_snapshots
    FOR EACH ROW EXECUTE FUNCTION deny_row_mutation();
CREATE TRIGGER trg_release_evaluations_immutable
    BEFORE UPDATE OR DELETE ON release_rule_evaluations
    FOR EACH ROW EXECUTE FUNCTION deny_row_mutation();

CREATE OR REPLACE FUNCTION protect_completed_pre_trip_check()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'pre_trip_checks cannot be deleted; use invalidation workflow'
            USING ERRCODE = '55000';
    END IF;

    IF OLD.status IN ('PASSED','FAILED') THEN
        RAISE EXCEPTION 'completed pre_trip_check is immutable; use invalidation workflow'
            USING ERRCODE = '55000';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_pre_trip_checks_protect_completed
    BEFORE UPDATE OR DELETE ON pre_trip_checks
    FOR EACH ROW EXECUTE FUNCTION protect_completed_pre_trip_check();

CREATE OR REPLACE FUNCTION protect_waybill_version()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'waybill_versions cannot be deleted'
            USING ERRCODE = '55000';
    END IF;

    IF OLD.generation_status <> 'PENDING' THEN
        RAISE EXCEPTION 'finalized waybill_version is immutable'
            USING ERRCODE = '55000';
    END IF;

    IF NEW.id IS DISTINCT FROM OLD.id
       OR NEW.company_id IS DISTINCT FROM OLD.company_id
       OR NEW.waybill_id IS DISTINCT FROM OLD.waybill_id
       OR NEW.version_no IS DISTINCT FROM OLD.version_no
       OR NEW.document_template_version_id IS DISTINCT FROM OLD.document_template_version_id
       OR NEW.snapshot IS DISTINCT FROM OLD.snapshot
       OR NEW.snapshot_schema_version IS DISTINCT FROM OLD.snapshot_schema_version
       OR NEW.snapshot_sha256 IS DISTINCT FROM OLD.snapshot_sha256
       OR NEW.created_at IS DISTINCT FROM OLD.created_at
       OR NEW.created_by IS DISTINCT FROM OLD.created_by
       OR NEW.previous_version_id IS DISTINCT FROM OLD.previous_version_id
       OR NEW.correction_case_id IS DISTINCT FROM OLD.correction_case_id
       OR NEW.correction_reason IS DISTINCT FROM OLD.correction_reason THEN
        RAISE EXCEPTION 'waybill_version business content is immutable'
            USING ERRCODE = '55000';
    END IF;

    IF NEW.generation_status NOT IN ('READY','FAILED') THEN
        RAISE EXCEPTION 'waybill_version may only finalize PENDING to READY or FAILED'
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_waybill_versions_protect
    BEFORE UPDATE OR DELETE ON waybill_versions
    FOR EACH ROW EXECUTE FUNCTION protect_waybill_version();

ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_company_policy ON companies
    USING (id = app_current_company_id())
    WITH CHECK (id = app_current_company_id());

DO $$
DECLARE
    rec record;
    nullable_company boolean;
BEGIN
    FOR rec IN
        SELECT c.table_name
        FROM information_schema.columns c
        JOIN information_schema.tables t
          ON t.table_schema = c.table_schema
         AND t.table_name = c.table_name
        WHERE c.table_schema = 'public'
          AND c.column_name = 'company_id'
          AND t.table_type = 'BASE TABLE'
          AND c.table_name <> 'alembic_version'
        ORDER BY c.table_name
    LOOP
        SELECT (is_nullable = 'YES')
        INTO nullable_company
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = rec.table_name
          AND column_name = 'company_id';

        EXECUTE 'ALTER TABLE ' || quote_ident(rec.table_name)
            || ' ENABLE ROW LEVEL SECURITY';

        IF nullable_company THEN
            EXECUTE 'CREATE POLICY tenant_visible ON ' || quote_ident(rec.table_name)
                || ' FOR SELECT USING '
                || '(company_id IS NULL OR company_id = app_current_company_id())';
            EXECUTE 'CREATE POLICY tenant_write ON ' || quote_ident(rec.table_name)
                || ' FOR ALL USING (company_id = app_current_company_id())'
                || ' WITH CHECK (company_id = app_current_company_id())';
        ELSE
            EXECUTE 'CREATE POLICY tenant_isolation ON ' || quote_ident(rec.table_name)
                || ' USING (company_id = app_current_company_id())'
                || ' WITH CHECK (company_id = app_current_company_id())';
        END IF;
    END LOOP;
END;
$$;
