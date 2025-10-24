CREATE TABLE [CONSUMPTION_ClinOpsFinance].NotTrackedProjects
(
  NotTrackedProjectsID INT IDENTITY(1,1)
  ,ProjectCode VARCHAR(100)
  ,Sponsor VARCHAR(400)
)
WITH
(
	DISTRIBUTION = REPLICATE,
	CLUSTERED INDEX (ProjectCode)
)
GO

