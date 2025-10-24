CREATE TABLE [CONSUMPTION_ClinOpsFinance].[HrContractAttendance]
(
	[Employee_Id] [int] NOT NULL,
	[ContractId] [int] NOT NULL,
	[ContractHistoryStartDate] [date] NULL,
	[ContractHistoryEndDate] [date] NULL,
	[EmployeeFullName] [varchar](102) NULL,
	[OfficeCountryId] [int] NULL,
	[OfficeCountryCode] [varchar](2) NULL,
	[OfficeCountryName] [varchar](100) NULL,
	[DATE] [date] NULL,
	[Date (Utilization)] [date] NULL,
	[Country] [varchar](100) NULL,
	[PrimaGlobalCountryName] [varchar](100) NULL,
	[DepartmentId] [int] NULL,
	[Department] [varchar](100) NULL,
	[ContractPositionId] [int] NULL,
	[Position] [varchar](100) NULL,
	[ContractClassName] [nvarchar](200) NULL,
	[ContractClassType] [varchar](10) NULL,
	[BILLABLE_ID] [int] NULL,
	[BILLABILITY] [nvarchar](4000) NULL,
	[IS_HOLIDAY] [int] NULL,
	[IS_VACATION] [int] NULL,
	[IS_SICK_LEAVE] [numeric](38, 1) NULL,
	[IS_DAY_OFF] [int] NULL,
	[IS_BUSINESS_TRIP] [int] NULL,
	[IS_WEEKEND] [int] NULL,
	[IS_DISMISS] [int] NULL,
	[ATTENDANCE] [varchar](38) NULL,
	[IS_LongTermLeave] [int] NULL,
	[FTE] [float] NULL,
	[ContractTimeFrameId] [int] NULL,
	[ContractTimeFrameType] [nvarchar](200) NULL,
	[ContractHoursPerWeek] [float] NULL,
	[CountryHoursPerWeek] [float] NULL,
	[ContractRank] [bigint] NULL,
	[Hours Expected, Daily] [float] NULL,
	[UtilizationDateId] [int] NULL
)
WITH
(
	DISTRIBUTION = HASH ( [Employee_Id],[DATE] ),
	CLUSTERED COLUMNSTORE INDEX
)
GO
