CREATE TABLE [CONSUMPTION_PRIMAREPORTING].[ProjectEvents]
(
	[RECORD_ID] [int] NULL,
	[PROJECT_CODE] [varchar](20) NULL,
	[PROJECT_NAME] [varchar](255) NULL,
	[REGION_ID] [int] NULL,
	[COUNTRY] [varchar](100) NULL,
	[EVENT_TEMPLATE_ID] [int] NULL,
	[ACTUAL_DATE] [datetime] NULL,
	[PLANNED_DATE] [datetime] NULL,
	[EVENT_NAME] [varchar](200) NULL,
	[EVENT_COMMENTS] [varchar](500) NULL,
	[STATUS_BEFORE] [int] NULL,
	[STATUS_AFTER] [int] NULL,
	[PHASE_BEFORE] [int] NULL,
	[PHASE_AFTER] [int] NULL,
	[SUPPRESS_NOTIFICATION] [bit] NULL,
	[IS_ONHOLD_BEFORE] [bit] NULL,
	[IS_TERMINATED_BEFORE] [bit] NULL,
	[IS_BACKUP_BEFORE] [bit] NULL,
	[PROBABILITY] [int] NULL,
	[CREATED_BY] [varchar](50) NULL,
	[CREATED_AT] [datetime] NULL,
	[UPDATED_BY] [varchar](50) NULL,
	[UPDATED_AT] [datetime] NULL,
	[RECORD_STATUS] [int] NULL,
	[IS_AUTOCREATED] [bit] NULL,
	[PROJECT_PLAN_ID] [int] NULL,
	[Project Code] [varchar](20) NULL,
	[Project Name] [varchar](255) NULL,
	[Event] [varchar](200) NULL,
	[Planned Date] [datetime] NULL,
	[Actual Date] [datetime] NULL,
	[Comments] [varchar](500) NULL,
	[SrcCreatedDate] [datetime] NULL,
	[SrcUpdatedDate] [datetime] NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO
