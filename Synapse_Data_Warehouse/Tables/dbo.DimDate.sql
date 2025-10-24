CREATE TABLE [dbo].[DimDate]
(
	[DimDateKey] [int] NULL,
	[Date] [date] NULL,
	[FullDateUSA] [char](10) NULL,
	[DayOfMonth] [varchar](2) NULL,
	[DaySuffix] [varchar](4) NULL,
	[DayName] [varchar](9) NULL,
	[DayOfWeekUSA] [char](1) NULL,
	[DayOfWeekUK] [char](1) NULL,
	[DayOfWeekInMonth] [varchar](2) NULL,
	[DayOfWeekInYear] [varchar](2) NULL,
	[DayOfQuarter] [varchar](3) NULL,
	[DayOfYear] [varchar](3) NULL,
	[WeekOfMonth] [int] NULL,
	[WeekOfQuarter] [int] NULL,
	[WeekOfYear] [int] NULL,
	[Month] [varchar](2) NULL,
	[MonthName] [varchar](9) NULL,
	[MonthOfQuarter] [varchar](2) NULL,
	[Quarter] [int] NULL,
	[QuarterName] [varchar](9) NULL,
	[Year] [int] NULL,
	[YearName] [char](7) NULL,
	[MonthYear] [char](10) NULL,
	[MMYYYY] [char](6) NULL,
	[FirstDayOfMonth] [date] NULL,
	[LastDayOfMonth] [date] NULL,
	[FirstDayOfQuarter] [date] NULL,
	[LastDayOfQuarter] [date] NULL,
	[FirstDayOfYear] [date] NULL,
	[LastDayOfYear] [date] NULL,
	[IsHolidayUSA] [bit] NULL,
	[IsWeekday] [bit] NULL,
	[HolidayUSA] [varchar](50) NULL,
	[PSIReportingWeekOfYear] [int] NULL,
	[PsiReportingYear] [int] NULL,
	[PsiReportingQuarterNumber] [int] NULL,
	[FirstDayOfWeek] [date] NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	CLUSTERED COLUMNSTORE INDEX
)
GO
