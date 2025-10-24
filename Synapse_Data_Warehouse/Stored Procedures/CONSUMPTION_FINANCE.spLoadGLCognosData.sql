CREATE PROC [CONSUMPTION_FINANCE].[spLoadGLCognosData] AS
BEGIN

SET NOCOUNT ON

DECLARE @servername VARCHAR(100) = CAST( SERVERPROPERTY( 'ServerName' ) AS VARCHAR(100) )
DECLARE @procname NVARCHAR(128) = '[CONSUMPTION_FINANCE].[spLoadGLCognosData]'
DECLARE @procid VARCHAR(100) = ( SELECT OBJECT_ID(@procname) )

BEGIN TRY

DECLARE @MSG VARCHAR(max) = 'Start Time:' + CONVERT(VARCHAR(30), FORMAT(GETDATE(), 'dd-MMM-yyyy hh:mm:ss tt')) + ' ' + @ProcName
DECLARE @AffectedRecordCount BIGINT = 0
DECLARE @Count BIGINT = 0
DECLARE @ProcessId BIGINT
DECLARE @RowsInTargetBegin BIGINT
DECLARE @RowsInTargetEnd BIGINT
DECLARE @StartTime DATETIME 
DECLARE @EndTime DATETIME 

SET @RowsInTargetBegin = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[GLCognosData])
SET @StartTime = GETDATE()

RAISERROR (@MSG, 0, 0) 

truncate table [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500];

if object_id('tempdb..#thc') is not null
begin drop table #thc; end

;with cte as
(
select
*,
Lag(LocalAmountYTD, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Previous_LocalAmountYTD
from [STAGING_FINANCE_COGNOS].[v_CCR2PowerBI_facts]
where Account = 'HC100500'
)
select 
*,
case when Previous_LocalAmountYTD is NULL then LocalAmountPTD else (LocalAmountYTD - Previous_LocalAmountYTD) end as Fixed_LocalAmountPTD
into #thc
from cte;

-- 2022 and 2023

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from #thc
where cast(Periode as int) >= 2203 and cast(Periode as int) <= 2312
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 1
)
select
cte1.*,
(cte1.LocalAmountYTD / 2) as LocalAmountPTD_03, 
(cte1.LocalAmountYTD / 2) as LocalAmountPTD_06, 
(cte1.LocalAmountYTD / 2) * (-1) as LocalAmountPTD_09, 
(cte1.LocalAmountYTD / 2) * (-1) as LocalAmountPTD_12,
(cte1.LocalAmountYTD / 2) as LocalAmountYTD_03, 
cte1.LocalAmountYTD as LocalAmountYTD_06, 
(cte1.LocalAmountYTD / 2) * (-1) as LocalAmountYTD_09, 
0 as LocalAmountYTD_12
into #t00
from cte1
join cte2
on cte1.Company = cte2.Company and cte1.Dim1 = cte2.Dim1 and cte1.Currency = cte2.Currency and cte1.Year = cte2.Year
where cte1.Month = '06';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '03' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '03' as [Periode]
      ,[Year]
      ,'03' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_03
      ,[TransAmountYTD]
      ,LocalAmountPTD_03
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from #thc
where cast(Periode as int) >= 2203 and cast(Periode as int) <= 2312
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 1
)
select
cte1.*,
(cte1.LocalAmountYTD / 2) as LocalAmountPTD_09, 
(cte1.LocalAmountYTD / 2) as LocalAmountPTD_12, 
(cte1.LocalAmountYTD / 2) as LocalAmountYTD_09, 
cte1.LocalAmountYTD as LocalAmountYTD_12
into #t00
from cte1
join cte2
on cte1.Company = cte2.Company and cte1.Dim1 = cte2.Dim1 and cte1.Currency = cte2.Currency and cte1.Year = cte2.Year
where cte1.Month = '12';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from #thc
where cast(Periode as int) >= 2203 and cast(Periode as int) <= 2312
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 2
)
select 
t06.*,
(t06.LocalAmountYTD / 2) as LocalAmountPTD_03,
(t06.LocalAmountYTD / 2) as LocalAmountPTD_06,
((t12.LocalAmountYTD - t06.LocalAmountYTD) / 2) as  LocalAmountPTD_09,
((t12.LocalAmountYTD - t06.LocalAmountYTD) / 2) as  LocalAmountPTD_12,
(t06.LocalAmountYTD / 2) as LocalAmountYTD_03,
t06.LocalAmountYTD as LocalAmountYTD_06,
(t06.LocalAmountYTD + (t12.LocalAmountYTD - t06.LocalAmountYTD) / 2) as  LocalAmountYTD_09,
t12.LocalAmountYTD as LocalAmountYTD_12
into #t00
from cte1 as t06
join cte2
on t06.Company = cte2.Company and t06.Dim1 = cte2.Dim1 and t06.Currency = cte2.Currency and t06.Year = cte2.Year
join cte1 as t12
on t12.Company = cte2.Company and t12.Dim1 = cte2.Dim1 and t12.Currency = cte2.Currency and t12.Year = cte2.Year
where t06.Month = '06' and t12.Month = '12';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '03' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '03' as [Periode]
      ,[Year]
      ,'03' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_03
      ,[TransAmountYTD]
      ,LocalAmountPTD_03
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

-- 2024

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from #thc
where cast(Periode as int) >= 2403 and cast(Periode as int) <= 2412
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 1
)
select 
cte1.*,
(cte1.LocalAmountYTD / 2) as LocalAmountPTD_03,
(cte1.LocalAmountYTD / 2) as LocalAmountPTD_06,
(cte1.LocalAmountYTD * (-1)) as LocalAmountPTD_09,
(cte1.LocalAmountYTD / 2) as LocalAmountYTD_03,
cte1.LocalAmountYTD as LocalAmountYTD_06,
0 as LocalAmountYTD_09
into #t00
from cte1
join cte2
on cte1.Company = cte2.Company and cte1.Dim1 = cte2.Dim1 and cte1.Currency = cte2.Currency and cte1.Year = cte2.Year
where cte1.Month = '06';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '03' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '03' as [Periode]
      ,[Year]
      ,'03' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_03
      ,[TransAmountYTD]
      ,LocalAmountPTD_03
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from #thc
where cast(Periode as int) >= 2403 and cast(Periode as int) <= 2412
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 1
)
select 
cte1.*,
cte1.LocalAmountYTD as LocalAmountPTD_09,
(cte1.LocalAmountYTD * (-1)) as LocalAmountPTD_12,
cte1.LocalAmountYTD as LocalAmountYTD_09,
0 as LocalAmountYTD_12
into #t00
from cte1
join cte2
on cte1.Company = cte2.Company and cte1.Dim1 = cte2.Dim1 and cte1.Currency = cte2.Currency and cte1.Year = cte2.Year
where cte1.Month = '09';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from #thc
where cast(Periode as int) >= 2403 and cast(Periode as int) <= 2412
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 1
)
select 
cte1.*,
cte1.LocalAmountYTD as LocalAmountPTD_12,
cte1.LocalAmountYTD as LocalAmountYTD_12
into #t00
from cte1
join cte2
on cte1.Company = cte2.Company and cte1.Dim1 = cte2.Dim1 and cte1.Currency = cte2.Currency and cte1.Year = cte2.Year
where cte1.Month = '12';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
	  ,Lag(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Previous_Month
from #thc
where cast(Periode as int) >= 2403 and cast(Periode as int) <= 2412
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 2
)
select
t09.*, 
(t06.LocalAmountYTD /2) as LocalAmountPTD_03,
(t06.LocalAmountYTD /2) as LocalAmountPTD_06,
(t09.LocalAmountYTD - t06.LocalAmountPTD) as LocalAmountPTD_09,
(t09.LocalAmountYTD * (-1)) as LocalAmountPTD_12,
(t06.LocalAmountYTD /2) as LocalAmountYTD_03,
t06.LocalAmountYTD as LocalAmountYTD_06,
t09.LocalAmountYTD as LocalAmountYTD_09,
0 as LocalAmountYTD_12
into #t00
from cte1 as t09
join cte2
on t09.Company = cte2.Company and t09.Dim1 = cte2.Dim1 and t09.Currency = cte2.Currency and t09.Year = cte2.Year
join cte1 as t06
on t09.Company = t06.Company and t09.Dim1 = t06.Dim1 and t09.Currency = t06.Currency and t09.Year = t06.Year
where t09.Month = '09' and t09.Previous_Month = '06' and t06.Month = '06';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '03' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '03' as [Periode]
      ,[Year]
      ,'03' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_03
      ,[TransAmountYTD]
      ,LocalAmountPTD_03
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
	  ,Lag(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Previous_Month
from #thc
where cast(Periode as int) >= 2403 and cast(Periode as int) <= 2412
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 2
)
select
t12.*, 
(t06.LocalAmountYTD /2) as LocalAmountPTD_03,
(t06.LocalAmountYTD /2) as LocalAmountPTD_06,
t06.LocalAmountYTD * (-1) as LocalAmountPTD_09,
t12.LocalAmountYTD as LocalAmountPTD_12,
(t06.LocalAmountYTD /2) as LocalAmountYTD_03,
t06.LocalAmountYTD as LocalAmountYTD_06,
0 as LocalAmountYTD_09,
t12.LocalAmountYTD as LocalAmountYTD_12
into #t00
from cte1 as t12
join cte2
on t12.Company = cte2.Company and t12.Dim1 = cte2.Dim1 and t12.Currency = cte2.Currency and t12.Year = cte2.Year
join cte1 as t06
on t12.Company = t06.Company and t12.Dim1 = t06.Dim1 and t12.Currency = t06.Currency and t12.Year = t06.Year
where t12.Month = '12' and t12.Previous_Month = '06' and t06.Month = '06';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '03' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '03' as [Periode]
      ,[Year]
      ,'03' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_03
      ,[TransAmountYTD]
      ,LocalAmountPTD_03
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
	  ,Lag(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Previous_Month
from #thc
where cast(Periode as int) >= 2403 and cast(Periode as int) <= 2412
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 2
)
select
t12.*, 
t09.LocalAmountYTD as LocalAmountPTD_09,
(t12.LocalAmountYTD - t09.LocalAmountYTD) as LocalAmountPTD_12,
t09.LocalAmountYTD as LocalAmountYTD_09,
t12.LocalAmountYTD as LocalAmountYTD_12
into #t00
from cte1 as t12
join cte2
on t12.Company = cte2.Company and t12.Dim1 = cte2.Dim1 and t12.Currency = cte2.Currency and t12.Year = cte2.Year
join cte1 as t09
on t12.Company = t09.Company and t12.Dim1 = t09.Dim1 and t12.Currency = t09.Currency and t12.Year = t09.Year
where t12.Month = '12' and t12.Previous_Month = '09' and t09.Month = '09';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from #thc
where cast(Periode as int) >= 2403 and cast(Periode as int) <= 2412
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 3
)
select 
t06.*, 
(t06.LocalAmountYTD / 2) as LocalAmountPTD_03,
(t06.LocalAmountYTD / 2) as LocalAmountPTD_06,
(t09.LocalAmountYTD - t06.LocalAmountYTD) as LocalAmountPTD_09,
(t12.LocalAmountYTD - t09.LocalAmountYTD) as LocalAmountPTD_12,
(t06.LocalAmountYTD / 2) as LocalAmountYTD_03,
t06.LocalAmountYTD as LocalAmountYTD_06,
t09.LocalAmountYTD as LocalAmountYTD_09,
t12.LocalAmountYTD as LocalAmountYTD_12
into #t00
from cte1 as t06
join cte2
on t06.Company = cte2.Company and t06.Dim1 = cte2.Dim1 and t06.Currency = cte2.Currency and t06.Year = cte2.Year
join cte1 as t09
on t09.Company = cte2.Company and t09.Dim1 = cte2.Dim1 and t09.Currency = cte2.Currency and t09.Year = cte2.Year
join cte1 as t12
on t12.Company = cte2.Company and t12.Dim1 = cte2.Dim1 and t12.Currency = cte2.Currency and t12.Year = cte2.Year
where t06.Month = '06' and t09.Month = '09' and t12.Month = '12';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '03' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '03' as [Periode]
      ,[Year]
      ,'03' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_03
      ,[TransAmountYTD]
      ,LocalAmountPTD_03
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

-- 2025 and after

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from #thc
where cast(Periode as int) >= 2503
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 1
)
select 
cte1.*,
cte1.LocalAmountYTD as LocalAmountPTD_03,
(cte1.LocalAmountYTD * (-1)) as LocalAmountPTD_06,
cte1.LocalAmountYTD as LocalAmountYTD_03,
0 as LocalAmountYTD_06
into #t00
from cte1
join cte2
on cte1.Company = cte2.Company and cte1.Dim1 = cte2.Dim1 and cte1.Currency = cte2.Currency and cte1.Year = cte2.Year
where cte1.Month = '03';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '03' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '03' as [Periode]
      ,[Year]
      ,'03' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_03
      ,[TransAmountYTD]
      ,LocalAmountPTD_03
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      --,Fixed_LocalAmountPTD as [LocalAmountPTD]
	  ,[LocalAmountPTD]				
      ,[TransAmountPTD]
      ,[Vtyp]
from #thc
where cast(Periode as int) >= 2503
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 1
)
select 
cte1.*,
cte1.LocalAmountPTD as LocalAmountPTD_06,
(cte1.LocalAmountYTD * (-1)) as LocalAmountPTD_09,
cte1.LocalAmountYTD as LocalAmountYTD_06,
0 as LocalAmountYTD_09
into #t00
from cte1
join cte2
on cte1.Company = cte2.Company and cte1.Dim1 = cte2.Dim1 and cte1.Currency = cte2.Currency and cte1.Year = cte2.Year
where cte1.Month = '06';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from #thc
where cast(Periode as int) >= 2503
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 1
)
select 
cte1.*,
cte1.LocalAmountYTD as LocalAmountPTD_09,
(cte1.LocalAmountYTD * (-1)) as LocalAmountPTD_12,
cte1.LocalAmountYTD as LocalAmountYTD_09,
0 as LocalAmountYTD_12
into #t00
from cte1
join cte2
on cte1.Company = cte2.Company and cte1.Dim1 = cte2.Dim1 and cte1.Currency = cte2.Currency and cte1.Year = cte2.Year
where cte1.Month = '09';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from #thc
where cast(Periode as int) >= 2503
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 1
)
select 
cte1.*,
cte1.LocalAmountYTD as LocalAmountPTD_12,
cte1.LocalAmountYTD as LocalAmountYTD_12
into #t00
from cte1
join cte2
on cte1.Company = cte2.Company and cte1.Dim1 = cte2.Dim1 and cte1.Currency = cte2.Currency and cte1.Year = cte2.Year
where cte1.Month = '12';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
	  ,Lag(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Previous_Month
from #thc
where cast(Periode as int) >= 2503
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 2
)
select
t09.*, 
t06.LocalAmountYTD as LocalAmountPTD_06,
(t09.LocalAmountYTD - t06.LocalAmountYTD) as LocalAmountPTD_09,
(t09.LocalAmountYTD * (-1)) as LocalAmountPTD_12,
t06.LocalAmountYTD as LocalAmountYTD_06,
t09.LocalAmountYTD as LocalAmountYTD_09,
0 as LocalAmountYTD_12
into #t00
from cte1 as t09
join cte2
on t09.Company = cte2.Company and t09.Dim1 = cte2.Dim1 and t09.Currency = cte2.Currency and t09.Year = cte2.Year
join cte1 as t06
on t09.Company = t06.Company and t09.Dim1 = t06.Dim1 and t09.Currency = t06.Currency and t09.Year = t06.Year
where t09.Month = '09' and t09.Previous_Month = '06' and t06.Month = '06';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
	  ,Lag(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Previous_Month
from #thc
where cast(Periode as int) >= 2503
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 2
)
select
t12.*, 
t06.LocalAmountYTD as LocalAmountPTD_06,
(t06.LocalAmountYTD * (-1)) as LocalAmountPTD_09,
t12.LocalAmountYTD as LocalAmountPTD_12,
t06.LocalAmountYTD as LocalAmountYTD_06,
0 as LocalAmountYTD_09,
t12.LocalAmountYTD as LocalAmountYTD_12
into #t00
from cte1 as t12
join cte2
on t12.Company = cte2.Company and t12.Dim1 = cte2.Dim1 and t12.Currency = cte2.Currency and t12.Year = cte2.Year
join cte1 as t06
on t12.Company = t06.Company and t12.Dim1 = t06.Dim1 and t12.Currency = t06.Currency and t12.Year = t06.Year
where t12.Month = '12' and t12.Previous_Month = '06' and t06.Month = '06';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
	  ,Lag(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Previous_Month
from #thc
where cast(Periode as int) >= 2503
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 2
)
select
t12.*, 
t09.LocalAmountYTD as LocalAmountPTD_09,
(t12.LocalAmountYTD - t09.LocalAmountYTD) as LocalAmountPTD_12,
t09.LocalAmountYTD as LocalAmountYTD_09,
t12.LocalAmountYTD as LocalAmountYTD_12
into #t00
from cte1 as t12
join cte2
on t12.Company = cte2.Company and t12.Dim1 = cte2.Dim1 and t12.Currency = cte2.Currency and t12.Year = cte2.Year
join cte1 as t09
on t12.Company = t09.Company and t12.Dim1 = t09.Dim1 and t12.Currency = t09.Currency and t12.Year = t09.Year
where t12.Month = '12' and t12.Previous_Month = '09' and t09.Month = '09';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      --,Fixed_LocalAmountPTD as [LocalAmountPTD]
	  ,[LocalAmountPTD]				
      ,[TransAmountPTD]
      ,[Vtyp]
	  ,Lag(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Previous_Month
from #thc
where cast(Periode as int) >= 2503
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 2
)
select
t06.*, 
t03.LocalAmountYTD as LocalAmountPTD_03,
t06.LocalAmountPTD as LocalAmountPTD_06,
(t06.LocalAmountYTD * (-1)) as LocalAmountPTD_09,
t03.LocalAmountYTD as LocalAmountYTD_03,
t06.LocalAmountYTD as LocalAmountYTD_06,
0 as LocalAmountYTD_09
into #t00
from cte1 as t06
join cte2
on t06.Company = cte2.Company and t06.Dim1 = cte2.Dim1 and t06.Currency = cte2.Currency and t06.Year = cte2.Year
join cte1 as t03
on t06.Company = t03.Company and t06.Dim1 = t03.Dim1 and t06.Currency = t03.Currency and t06.Year = t03.Year
where t06.Month = '06' and t06.Previous_Month = '03' and t03.Month = '03';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '03' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '03' as [Periode]
      ,[Year]
      ,'03' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_03
      ,[TransAmountYTD]
      ,LocalAmountPTD_03
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
	  ,Lag(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Previous_Month
from #thc
where cast(Periode as int) >= 2503
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 2
)
select
t09.*, 
t03.LocalAmountYTD as LocalAmountPTD_03,
(t03.LocalAmountYTD * (-1)) as LocalAmountPTD_06,
t09.LocalAmountYTD as LocalAmountPTD_09,
(t09.LocalAmountYTD * (-1)) as LocalAmountPTD_12,
t03.LocalAmountYTD as LocalAmountYTD_03,
0 as LocalAmountYTD_06,
t09.LocalAmountYTD as LocalAmountYTD_09,
0 as LocalAmountYTD_12
into #t00
from cte1 as t09
join cte2
on t09.Company = cte2.Company and t09.Dim1 = cte2.Dim1 and t09.Currency = cte2.Currency and t09.Year = cte2.Year
join cte1 as t03
on t09.Company = t03.Company and t09.Dim1 = t03.Dim1 and t09.Currency = t03.Currency and t09.Year = t03.Year
where t09.Month = '09' and t09.Previous_Month = '03' and t03.Month = '03';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '03' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '03' as [Periode]
      ,[Year]
      ,'03' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_03
      ,[TransAmountYTD]
      ,LocalAmountPTD_03
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
	  ,Lag(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Previous_Month
from #thc
where cast(Periode as int) >= 2503
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 2
)
select
t12.*, 
t03.LocalAmountYTD as LocalAmountPTD_03,
(t03.LocalAmountYTD * (-1)) as LocalAmountPTD_06,
0 as LocalAmountPTD_09,
t12.LocalAmountYTD as LocalAmountPTD_12,
t03.LocalAmountYTD as LocalAmountYTD_03,
0 as LocalAmountYTD_06,
0 as LocalAmountYTD_09,
t12.LocalAmountYTD as LocalAmountYTD_12
into #t00
from cte1 as t12
join cte2
on t12.Company = cte2.Company and t12.Dim1 = cte2.Dim1 and t12.Currency = cte2.Currency and t12.Year = cte2.Year
join cte1 as t03
on t12.Company = t03.Company and t12.Dim1 = t03.Dim1 and t12.Currency = t03.Currency and t12.Year = t03.Year
where t12.Month = '12' and t12.Previous_Month = '03' and t03.Month = '03';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '03' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '03' as [Periode]
      ,[Year]
      ,'03' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_03
      ,[TransAmountYTD]
      ,LocalAmountPTD_03
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
	  ,Lag(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Previous_Month
	  ,Lead(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Next_Month
from #thc
where cast(Periode as int) >= 2503
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 3
)
select
t09.*, 
t03.LocalAmountYTD as LocalAmountPTD_03,
(t03.LocalAmountYTD * (-1)) as LocalAmountPTD_06,
t09.LocalAmountYTD as LocalAmountPTD_09,
(t12.LocalAmountYTD - t09.LocalAmountYTD) as LocalAmountPTD_12,
t03.LocalAmountYTD as LocalAmountYTD_03,
0 as LocalAmountYTD_06,
t09.LocalAmountYTD as LocalAmountYTD_09,
t12.LocalAmountYTD as LocalAmountYTD_12
into #t00
from cte1 as t09
join cte2
on t09.Company = cte2.Company and t09.Dim1 = cte2.Dim1 and t09.Currency = cte2.Currency and t09.Year = cte2.Year
join cte1 as t03
on t09.Company = t03.Company and t09.Dim1 = t03.Dim1 and t09.Currency = t03.Currency and t09.Year = t03.Year
join cte1 as t12
on t09.Company = t12.Company and t09.Dim1 = t12.Dim1 and t09.Currency = t12.Currency and t09.Year = t12.Year
where t09.Month = '09' and t09.Previous_Month = '03' and t03.Month = '03' and t09.Next_Month = '12' and t12.Month = '12';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '03' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '03' as [Periode]
      ,[Year]
      ,'03' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_03
      ,[TransAmountYTD]
      ,LocalAmountPTD_03
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

;with cte1 as
(
select
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
	  ,Lag(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Previous_Month
	  ,Lead(Month, 1) over (partition by Company, Dim1, Currency, Year order by Month) as Next_Month
from #thc
where cast(Periode as int) >= 2503
),
cte2 as
(
select *
from
(
select 
Company, Dim1, Currency, Year, count(*) as row_count
from cte1
group by Company, Dim1, Currency, Year
) t
where row_count = 3
)
select
t09.*, 
t06.LocalAmountYTD as LocalAmountPTD_06,
(t09.LocalAmountYTD - t06.LocalAmountYTD) as LocalAmountPTD_09,
(t12.LocalAmountYTD - t09.LocalAmountYTD) as LocalAmountPTD_12,
t06.LocalAmountYTD as LocalAmountYTD_06,
t09.LocalAmountYTD as LocalAmountYTD_09,
t12.LocalAmountYTD as LocalAmountYTD_12
into #t00
from cte1 as t09
join cte2
on t09.Company = cte2.Company and t09.Dim1 = cte2.Dim1 and t09.Currency = cte2.Currency and t09.Year = cte2.Year
join cte1 as t06
on t09.Company = t06.Company and t09.Dim1 = t06.Dim1 and t09.Currency = t06.Currency and t09.Year = t06.Year
join cte1 as t12
on t09.Company = t12.Company and t09.Dim1 = t12.Dim1 and t09.Currency = t12.Currency and t09.Year = t12.Year
where t09.Month = '09' and t09.Previous_Month = '06' and t06.Month = '06' and t09.Next_Month = '12' and t12.Month = '12';

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       left([Perakt], 2) + '06' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '06' as [Periode]
      ,[Year]
      ,'06' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_06
      ,[TransAmountYTD]
      ,LocalAmountPTD_06
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '09' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '09' as [Periode]
      ,[Year]
      ,'09' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_09
      ,[TransAmountYTD]
      ,LocalAmountPTD_09
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00
union all
select 
       left([Perakt], 2) + '12' + right([Perakt], 2) as [Perakt]
      ,left([Periode], 2) + '12' as [Periode]
      ,[Year]
      ,'12' as [Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,LocalAmountYTD_12
      ,[TransAmountYTD]
      ,LocalAmountPTD_12
      ,[TransAmountPTD]
      ,[Vtyp]
from #t00;

-- before 2022

if object_id('tempdb..#t00') is not null
begin drop table #t00; end

insert into [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,Fixed_LocalAmountPTD as [LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from #thc
where cast(Periode as int) < 2203;

if object_id('tempdb..#thc') is not null
begin drop table #thc; end

truncate table [CONSUMPTION_FINANCE].[GLCognosData];

begin transaction 

insert into [CONSUMPTION_FINANCE].[GLCognosData]
(
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
)
select 
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from [STAGING_FINANCE_COGNOS].[GLCognosData_HC100500]
union all
select 
       [Perakt]
      ,[Periode]
      ,[Year]
      ,[Month]
      ,[Actuality]
      ,[Company]
      ,[Currency]
      ,[Account]
      ,[Dim1]
      ,[Dim2]
      ,[Dim3]
      ,[Dim4]
      ,[Btyp]
      ,[Etyp]
      ,[KonsType]
      ,[JournalNbr]
      ,[Partner]
      ,[OriginCompany]
      ,[TransCurrency]
      ,[PartnerDim]
      ,[LocalAmountYTD]
      ,[TransAmountYTD]
      ,[LocalAmountPTD]
      ,[TransAmountPTD]
      ,[Vtyp]
from [STAGING_FINANCE_COGNOS].[v_CCR2PowerBI_facts]
where Account <> 'HC100500';

exec [dbo].[spLastRowCount] @Count = @Count output
set @AffectedRecordCount = @Count + @AffectedRecordCount

commit transaction

SET @RowsInTargetEnd = (SELECT COUNT(*) FROM [CONSUMPTION_FINANCE].[GLCognosData])
SET @EndTime = GETDATE()
SET @MSG = @MSG + ': New Rows Processed = ' + CAST((@RowsInTargetEnd - @RowsInTargetBegin) AS VARCHAR(30)) + ', within: ' + CAST(DATEDIFF(Second, @StartTime, @EndTime) AS VARCHAR(30)) + ' Sec.'

EXEC [dbo].LogMessage @LogLevel = 'INFO', @HostName = @servername, @CallSite = 'FINANCE ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @MSG, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = NULL, @ErrorLine = NULL ,@ErrorSeverity = NULL, @ErrorState = NULL
RAISERROR (@MSG ,0,0) 

END TRY

BEGIN CATCH

rollback transaction

DECLARE @ErrorNum int, @ErrorLine int, @ErrorSeverity int, @ErrorState int
DECLARE @ErrorProcedure nvarchar(126), @ErrorMessage nvarchar(2048) 

--store all the error information for logging the error
SELECT @ErrorNum       = ERROR_NUMBER() 
      ,@ErrorLine      = 0
      ,@ErrorSeverity  = ERROR_SEVERITY()
      ,@ErrorState     = ERROR_STATE()
      ,@ErrorProcedure = ERROR_PROCEDURE()
      ,@ErrorMessage   = ERROR_MESSAGE()

SET @MSG = @MSG + ' : Proc Error ' + ' - ' + ISNULL(@ErrorMessage, ' ') 
EXEC [dbo].LogMessage @LogLevel = 'ERROR',  @HostName = @servername, @CallSite = 'FINANCE ETL', @ProcessId = @procid, @ProcessName = @ProcName, @Message = @ErrorMessage, @AffectedRecordCount = @AffectedRecordCount, @ErrorNum = @ErrorNum, @ErrorLine = @ErrorLine ,@ErrorSeverity = @ErrorSeverity, @ErrorState = @ErrorState
RAISERROR (@MSG ,@ErrorSeverity,@ErrorState) 

END CATCH

END