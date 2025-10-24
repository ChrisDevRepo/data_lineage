CREATE TABLE [STAGING_CADENCE].CadenceRates (	
[Department]	 [nvarchar](200) NULL,
[Function name]	 [nvarchar](200) NULL,
[Function code]	 [nvarchar](200) NULL,
[Region code]	 [nvarchar](200) NULL,
[Country code]	 [nvarchar](200) NULL,
[Is Region rate]	 [bit] NULL,
[Function]	 [nvarchar](200) NULL,
[Country]	 [nvarchar](200) NULL,
[Region Rate]	 [decimal](19,4) NULL,
[Country Rate]	 [decimal](19,4) NULL,
[Created_At]    datetime
)	
WITH	
(	
DISTRIBUTION = REPLICATE,	
CLUSTERED INDEX ([Function], [Country])	
)	
GO