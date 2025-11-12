"""
Test Option A: Simplified Preprocessing Rules (7 → 3)

Backup of original patterns before testing simplified version.
"""

# ORIGINAL ENHANCED_REMOVAL_PATTERNS (11 patterns)
ORIGINAL_PATTERNS = [
    # 1. IF EXISTS
    (r'\bIF\s+EXISTS\s*\((?:[^()]|\([^()]*\))*\)\s*',
     '-- IF EXISTS removed\n',
     re.IGNORECASE),

    # 2. IF NOT EXISTS
    (r'\bIF\s+NOT\s+EXISTS\s*\((?:[^()]|\([^()]*\))*\)\s*',
     '-- IF NOT EXISTS removed\n',
     re.IGNORECASE),

    # 3. CATCH blocks
    (r'BEGIN\s+/\*\s*CATCH\s*\*/.*?END\s+/\*\s*CATCH\s*\*/',
     'BEGIN /* CATCH */\n  -- Error handling removed\n  SELECT 1;\nEND /* CATCH */',
     re.DOTALL),

    # 4. ROLLBACK
    (r'ROLLBACK\s+TRANSACTION\s*;.*?(?=END|$)',
     'ROLLBACK TRANSACTION;\n  -- Rollback path removed\n  SELECT 1;\n',
     re.DOTALL),

    # 5. Utility EXEC
    (r'\bEXEC(?:UTE)?\s+(?:\[?dbo\]?\.)?\[?(spLastRowCount|LogMessage)\]?[^;]*;?', '', re.IGNORECASE),

    # 6. DECLARE with SELECT → literal
    (r'DECLARE\s+(@\w+)\s+(\w+(?:\([^\)]*\))?)\s*=\s*\((?:[^()]|\([^()]*\))*\)',
     r'DECLARE \1 \2 = 1  -- Admin query removed',
     0),

    # 7. SET with SELECT → literal
    (r'SET\s+(@\w+)\s*=\s*\((?:[^()]|\([^()]*\))*\)',
     r'SET \1 = 1  -- Admin query removed',
     0),

    # 8. Simple DECLARE
    (r'\bDECLARE\s+@\w+\s+[^\n;]+(?:;|\n)', '', 0),

    # 9. SET variable
    (r'\bSET\s+@\w+\s*=\s*[^\n;]+(?:;|\n)', '', 0),

    # 10. SET session options
    (r'\bSET\s+(NOCOUNT|XACT_ABORT|ANSI_NULLS|QUOTED_IDENTIFIER)\s+(ON|OFF)\b', '', 0),
]

# SIMPLIFIED VERSION (5 patterns - keeping IF EXISTS, combining DECLARE/SET)
SIMPLIFIED_PATTERNS = [
    # 1. IF EXISTS (keep - important for control flow)
    (r'\bIF\s+EXISTS\s*\((?:[^()]|\([^()]*\))*\)\s*',
     '-- IF EXISTS removed\n',
     re.IGNORECASE),

    # 2. IF NOT EXISTS (keep - important for control flow)
    (r'\bIF\s+NOT\s+EXISTS\s*\((?:[^()]|\([^()]*\))*\)\s*',
     '-- IF NOT EXISTS removed\n',
     re.IGNORECASE),

    # 3. CATCH/ROLLBACK (combined)
    (r'BEGIN\s+/\*\s*CATCH\s*\*/.*?END\s+/\*\s*CATCH\s*\*/',
     'BEGIN /* CATCH */ SELECT 1; END /* CATCH */',
     re.DOTALL),

    # 4. ROLLBACK paths
    (r'ROLLBACK\s+TRANSACTION\s*;.*?(?=END|$)',
     'ROLLBACK TRANSACTION; SELECT 1;',
     re.DOTALL),

    # 5. ALL DECLARE/SET @var (combined - no create-then-remove)
    (r'\b(DECLARE|SET)\s+@\w+[^;]*;?', '', re.IGNORECASE | re.MULTILINE),
]

print("Original: 11 patterns (with conflicts)")
print("Simplified: 5 patterns (no conflicts)")
print()
print("Key changes:")
print("- Removed DECLARE with SELECT → literal (pattern 6)")
print("- Removed SET with SELECT → literal (pattern 7)")
print("- Combined patterns 6-10 into single pattern 5")
print("- No more create-then-remove conflicts!")
