CREATE PROC [CONSUMPTION_PRIMAREPORTING_PARALLEL].[spLastRowCount] @Count [BIGINT] OUT AS
BEGIN

declare  @somevar  nvarchar(32)  =  (   SELECT TOP 1    request_id
                        FROM            sys.dm_pdw_exec_requests
                        WHERE           session_id = SESSION_ID()
                        ORDER BY end_time DESC
                    )
SET @Count =
(

SELECT  SUM(row_count) AS row_count
FROM    sys.dm_pdw_sql_requests
WHERE   row_count <> -1
AND     request_id = @somevar

)
END;
