
CREATE TABLE [CONSUMPTION_PRIMAREPORTING].[RaEcSubmissions]
(
	[Project Code] [varchar](20) NULL,
	[Project Name] [varchar](255) NULL,
	[Country ID] [int] NULL,
	[Country] [varchar](100) NULL,
	[Type] [nvarchar](200) NULL,
	[Authority] [nvarchar](200) NULL,
	[InitialReviewFlag] [int] NULL,
	[Site Id] [int] NULL,
	[Site Name] [varchar](255) NULL,
	[Sites] [varchar](2000) NULL,
	[Description] [nvarchar](max) NULL,
	[SubmissionStatusId] [int] NULL,
	[SubmissionStatus] [nvarchar](400) NULL,
	[ResponsibleEmployeeId] [int] NULL,
	[ResponsibleEmployee] [varchar](102) NULL,
	[Submission (planned)] [datetime] NULL,
	[Submission (Forecast)] [datetime] NULL,
	[Submission (Actual)] [datetime] NULL,
	[Submission Variance] [int] NULL,
	[Approval (planned)] [datetime] NULL,
	[Approval (Forecast)] [datetime] NULL,
	[Approval (Actual)] [datetime] NULL,
	[Approval Variance] [int] NULL,
	[ApprovalEnrolledSubjects] [int] NULL,
	[ApprovalScreenedSubjects] [int] NULL,
	[NotifiedEnrolledSubjects] [int] NULL,
	[NotifiedScreenedSubjects] [int] NULL,
	[Comments] [nvarchar](1000) NULL,
	[NaApprovalDate] [bit] NULL,
	[IsNonPsiSubmission] [bit] NULL,
	[ProjectIsTest] [bit] NULL,
	[SrcCreatedAt] [datetime] NULL,
	[SrcUpdatedAt] [datetime] NULL,
	[Country Submission] [varchar](3) NULL,
	[Initial Study Approval] [varchar](3) NULL,
	[Reporting Site ID] [varchar](2000) NULL
)
WITH
(
	DISTRIBUTION = ROUND_ROBIN,
	HEAP
)
GO