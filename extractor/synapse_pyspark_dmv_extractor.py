SERVER = ""
DATABASE = ""
TEMP_FOLDER = ""
TARGET_FODER = ""

from shared_utils.process_spark_base import ProcessSparkBase
utils = ProcessSparkBase(SERVER, DATABASE, TEMP_FOLDER)

QUERY_OBJECTS = """
    SELECT
        o.object_id,
        s.name AS schema_name,
        o.name AS object_name,
        CASE o.type
            WHEN 'U' THEN 'Table'
            WHEN 'V' THEN 'View'
            WHEN 'P' THEN 'Stored Procedure'
        END AS object_type,
        o.create_date,
        o.modify_date
    FROM sys.objects o
    JOIN sys.schemas s ON o.schema_id = s.schema_id
    WHERE o.type IN ('U', 'V', 'P')
        AND o.is_ms_shipped = 0
        AND s.name IN ('CONSUMPTION_FINANCE', 'CONSUMPTION_POWERBI', 'CONSUMPTION_PRIMA',
                       'STAGING_FINANCE_COGNOS', 'STAGING_FINANCE_FILE', 'ADMIN', 'dbo')
"""

QUERY_DEPENDENCIES = """
    SELECT
        d.referencing_id AS referencing_object_id,
        d.referenced_id AS referenced_object_id,
        d.referenced_schema_name,
        d.referenced_entity_name
    FROM sys.sql_expression_dependencies d
    WHERE d.referencing_id IS NOT NULL
        AND d.referenced_id IS NOT NULL
"""

QUERY_DEFINITIONS = """
    SELECT
        m.object_id,
        o.name AS object_name,
        s.name AS schema_name,
        m.definition
    FROM sys.sql_modules m
    JOIN sys.objects o ON m.object_id = o.object_id
    JOIN sys.schemas s ON o.schema_id = s.schema_id
    WHERE o.is_ms_shipped = 0
        AND s.name IN ('CONSUMPTION_FINANCE', 'CONSUMPTION_POWERBI', 'CONSUMPTION_PRIMA',
                       'STAGING_FINANCE_COGNOS', 'STAGING_FINANCE_FILE', 'ADMIN', 'dbo')
"""

QUERY_LOGS = """
    SELECT DISTINCT
        SUBSTRING(r.command, 1, 4000) AS command_text
    FROM sys.dm_pdw_exec_requests r
    WHERE r.submit_time >= DATEADD(day, -21, GETDATE())
        AND r.status = 'Completed'
        AND (
            r.command LIKE 'SELECT %'
            OR r.command LIKE 'INSERT %'
            OR r.command LIKE 'UPDATE %'
            OR r.command LIKE 'MERGE %'
        )
"""

QUERY_TABLE_COLUMNS = """
    SELECT
        o.object_id,
        s.name AS schema_name,
        o.name AS table_name,
        c.name AS column_name,
        t.name AS data_type,
        c.max_length,
        c.precision,
        c.scale,
        c.is_nullable,
        c.column_id
    FROM sys.tables o
    JOIN sys.schemas s ON o.schema_id = s.schema_id
    JOIN sys.columns c ON o.object_id = c.object_id
    JOIN sys.types t ON c.user_type_id = t.user_type_id
    WHERE o.is_ms_shipped = 0
        AND s.name IN ('CONSUMPTION_FINANCE', 'CONSUMPTION_POWERBI', 'CONSUMPTION_PRIMA',
                       'STAGING_FINANCE_COGNOS', 'STAGING_FINANCE_FILE', 'ADMIN', 'dbo')
"""

def extract_to_parquet(query, output_filename):

    df = utils.read_dwh(query)

    output_path = f"{TARGET_FODER}{output_filename}"
    df.coalesce(1).write.mode("overwrite").parquet(output_path)
	
extract_to_parquet(QUERY_OBJECTS, "objects")
extract_to_parquet(QUERY_DEPENDENCIES, "dependencies")
extract_to_parquet(QUERY_DEFINITIONS, "definitions")
extract_to_parquet(QUERY_LOGS, "query_logs")
extract_to_parquet(QUERY_TABLE_COLUMNS, "table_columns")