CREATE TABLE [STAGING_FINANCE_FILE].[COGNOS_Template_SubAccounts] (
    [Account]        VARCHAR (13)  NULL,
    [AccountName]    VARCHAR (250) NULL,
    [AccountSort]    SMALLINT      NULL,
    [SubAccountName] VARCHAR (250) NULL,
    [SubAccountSort] SMALLINT      NULL,
    [Companies]      VARCHAR (50)  NULL,
    [Summary]        VARCHAR (10)  NULL,
    [Category]       VARCHAR (250) NULL,
    [CategorySort]   TINYINT       NULL,
    [Group]          VARCHAR (250) NULL,
    [GroupSort]      TINYINT       NULL,
    [Template]       VARCHAR (100) NULL
)
WITH (CLUSTERED COLUMNSTORE INDEX, DISTRIBUTION = ROUND_ROBIN);

