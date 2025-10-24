CREATE TABLE [CONSUMPTION_PRIMA].[HrEmployeeHistory]
(
	[EMPLOYEE_ID] [int] NULL,
	[FULL_NAME] [varchar](102) NULL,
	[COUNTRY_ID] [int] NULL,
	[OFFICE_COUNTRY_NAME] [varchar](100) NULL,
	[OFFICE_NAME] [varchar](30) NULL,
	[DEPARTMENT_ID] [int] NULL,
	[DEPARTMENT] [varchar](100) NULL,
	[FULL_DEPARTMENT] [varchar](208) NULL,
	[POSITION_ID] [int] NULL,
	[POSITION] [varchar](100) NULL,
	[TIME_FRAME_ID] [int] NULL,
	[TIME_FRAME] [nvarchar](200) NULL,
	[CONTRACT_CLASS_NAME] [nvarchar](200) NULL,
	[PHONE] [varchar](100) NULL,
	[PHONE_EXTENTION] [varchar](65) NULL,
	[MOBILE_PHONE] [varchar](100) NULL,
	[START_DATE] [datetime] NULL,
	[STOP_DATE_CONCEPTION] [datetime] NULL,
	[EXPIRY_DATE_CONCEPTION] [datetime] NULL,
	[RECORD_STATUS] [varchar](10) NULL,
	[BILLABLE_ID] [int] NULL,
	[BILLABILITY] [nvarchar](200) NULL,
	[FTE] [float] NULL,
	[ContractHoursPerWeek] [float] NULL,
	[CountryHoursPerWeek] [float] NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
);