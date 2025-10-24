CREATE TABLE [CONSUMPTION_PRIMA].[ETL_CONTROL_setup] (
    [source_server]         VARCHAR (100) NULL,
    [source_database]       VARCHAR (50)  NULL,
    [source_schema]         VARCHAR (50)  NULL,
    [source_object]         VARCHAR (100) NULL,
    [primary_key]           VARCHAR (100) NULL,
    [incremental_load]      CHAR (1)      NULL,
    [load_frequency]        VARCHAR (25)  NULL,
    [project_name]          VARCHAR (50)  NULL,
    [staging_schema]        VARCHAR (50)  NULL,
    [staging_object]        VARCHAR (100) NULL,
    [incremental_column]    VARCHAR (100) NULL,
    [incremental_timestamp] DATETIME      NULL,
    [incremental_key]       BIGINT        NULL,
    [consumption_schema]    VARCHAR (50)  NULL,
    [consumption_object]    VARCHAR (100) NULL,
    [source_system]         VARCHAR (250) NULL
)
WITH (CLUSTERED COLUMNSTORE INDEX, DISTRIBUTION = ROUND_ROBIN);

