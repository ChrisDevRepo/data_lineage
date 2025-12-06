from engine.parsers.comment_hints_parser import CommentHintsParser
import re
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# EXACT DDL from Log Dump (Step 573) - Base version
base_ddl = """
        CREATE   PROCEDURE dbo.usp_LineageTest_Hints
        AS
        BEGIN
            -- Lineage Hints
            -- @LINEAGE_INPUTS: dbo.LineageSourceTable
            -- @LINEAGE_OUTPUTS: dbo.LineageTargetTable
        END;
        """

# Variations
variations = {
    "LF (\\n)": base_ddl,
    "CRLF (\\r\\n)": base_ddl.replace('\n', '\r\n'),
    "CR (\\r)": base_ddl.replace('\n', '\r'),
    "Mixed": base_ddl.replace('\n', '\r\n', 5) # First 5 CRLF, rest LF
}

parser = CommentHintsParser()
pattern = r'--\s*@LINEAGE_INPUTS:\s*(.+?)(?:\n|$)'

for name, ddl_var in variations.items():
    print(f"\n--- Testing {name} ---")
    print(f"DDL Repr fragment: {repr(ddl_var)[0:100]}...")
    
    matches = list(re.finditer(pattern, ddl_var, re.IGNORECASE | re.MULTILINE))
    print(f"Matches: {len(matches)}")
    for m in matches:
        print(f"  Match: {m.group(0)!r}")
        print(f"  Capture: {m.group(1)!r}")
        
    print(f"  Expected Capture: 'dbo.LineageSourceTable'")
    if matches and 'dbo.LineageSourceTable' in matches[0].group(1):
        print("  ✅ SUCCESS")
    else:
        print("  ❌ FAILURE")


