from engine.parsers.comment_hints_parser import CommentHintsParser

# Exact DDL fetched from DB
ddl = """
        CREATE   PROCEDURE dbo.usp_LineageTest_Hints
        AS
        BEGIN
            -- This comment should be removed by cleaning rules
            /* BLOCK COMMENT TO REMOVE */
            
            -- Dynamic SQL (Regex-blind)
            DECLARE @sql NVARCHAR(MAX);
            SET @sql = 'INSERT INTO dbo.LineageTargetTable SELECT ID FROM dbo.LineageSourceTable';
            EXEC sp_executesql @sql;

            -- Lineage Hints (Should be parsed despite cleaning)
            -- @LINEAGE_INPUTS: dbo.LineageSourceTable
            -- @LINEAGE_OUTPUTS: dbo.LineageTargetTable
        END;
        """

parser = CommentHintsParser()
inputs, outputs = parser.extract_hints(ddl, validate=False)

print(f"Inputs: {inputs}")
print(f"Outputs: {outputs}")

if "dbo.LineageSourceTable" in inputs and "dbo.LineageTargetTable" in outputs:
    print("SUCCESS: Hints extracted successfully in isolation.")
else:
    print("FAILURE: Hints NOT extracted in isolation.")
