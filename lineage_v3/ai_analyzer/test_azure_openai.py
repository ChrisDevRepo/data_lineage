"""
Azure OpenAI Model Testing Helper
==================================

Purpose: Smoke test Azure OpenAI API connection and evaluate:
1. Model selection (gpt-4.1-nano vs alternatives)
2. System prompt effectiveness for SQL parsing disambiguation
3. Whether fine-tuning is needed

Usage:
    python lineage_v3/ai_analyzer/test_azure_openai.py

Requirements:
    - Set environment variables in .env:
      AZURE_OPENAI_ENDPOINT
      AZURE_OPENAI_API_KEY
      AZURE_OPENAI_MODEL_NAME
      AZURE_OPENAI_DEPLOYMENT
      AZURE_OPENAI_API_VERSION
"""

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure OpenAI Configuration (from environment)
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4.1-nano")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-nano")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# System prompt for SQL parsing disambiguation
SYSTEM_PROMPT = """You are a SQL dependency analyzer specialized in disambiguating ambiguous table references in T-SQL stored procedures.

Your task: Given a SQL stored procedure and a list of candidate table names, identify which specific table is being referenced.

Rules:
1. Use context clues (nearby schema names, naming patterns, business logic)
2. Consider schema conventions (CONSUMPTION_FINANCE.Dim*, STAGING_*, etc.)
3. If multiple tables match, rank them by likelihood
4. Provide confidence score (0.0-1.0)
5. Explain your reasoning briefly

Output format (JSON):
{
  "resolved_table": "schema.table_name",
  "confidence": 0.95,
  "reasoning": "Brief explanation"
}
"""

# Single-shot example for testing
EXAMPLE_USER_PROMPT = """
SQL Context:
```sql
CREATE PROCEDURE [CONSUMPTION_FINANCE].[spLoadFactGLSAP]
AS
BEGIN
    TRUNCATE TABLE STAGING_CADENCE.GL_Staging;

    INSERT INTO FactGLSAP (AccountID, ProjectID, Amount)
    SELECT
        a.AccountID,
        p.ProjectID,
        g.Amount
    FROM GL_Staging g  -- AMBIGUOUS: Which GL_Staging table?
    INNER JOIN DimAccount a ON g.AccountCode = a.AccountCode
    INNER JOIN DimProjects p ON g.ProjectCode = p.ProjectCode;
END
```

Ambiguous Reference: "GL_Staging"

Candidate Tables:
1. STAGING_CADENCE.GL_Staging
2. STAGING_FINANCE.GL_Staging
3. dbo.GL_Staging

Question: Which table does "GL_Staging" refer to?
"""

def test_connection():
    """Test basic Azure OpenAI API connection."""
    print("=" * 80)
    print("AZURE OPENAI CONNECTION TEST")
    print("=" * 80)

    # Validate configuration
    if not API_KEY:
        print("❌ ERROR: AZURE_OPENAI_API_KEY not set in .env")
        return False

    if not ENDPOINT:
        print("❌ ERROR: AZURE_OPENAI_ENDPOINT not set in .env")
        return False

    print(f"Endpoint: {ENDPOINT}")
    print(f"Model: {MODEL_NAME}")
    print(f"Deployment: {DEPLOYMENT}")
    print(f"API Version: {API_VERSION}")
    print()

    try:
        client = AzureOpenAI(
            api_version=API_VERSION,
            azure_endpoint=ENDPOINT,
            api_key=API_KEY,
        )

        print("✅ Client initialized successfully")
        return client

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


def test_basic_completion(client):
    """Test basic completion with simple prompt."""
    print("\n" + "=" * 80)
    print("TEST 1: Basic Completion")
    print("=" * 80)

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                {
                    "role": "user",
                    "content": "Say 'Hello, Azure OpenAI works!' in exactly 5 words.",
                }
            ],
            max_completion_tokens=50,
            temperature=0.0,  # Deterministic
            model=DEPLOYMENT
        )

        result = response.choices[0].message.content
        print(f"Response: {result}")
        print(f"Tokens used: {response.usage.total_tokens}")
        print("✅ Basic completion test passed")
        return True

    except Exception as e:
        print(f"❌ Basic completion failed: {e}")
        return False


def test_sql_disambiguation(client):
    """Test SQL parsing disambiguation with system prompt."""
    print("\n" + "=" * 80)
    print("TEST 2: SQL Disambiguation (Single-Shot Example)")
    print("=" * 80)

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": EXAMPLE_USER_PROMPT,
                }
            ],
            max_completion_tokens=500,
            temperature=0.0,  # Deterministic for testing
            model=DEPLOYMENT
        )

        result = response.choices[0].message.content
        print("User Prompt:")
        print(EXAMPLE_USER_PROMPT[:200] + "...")
        print("\nModel Response:")
        print(result)
        print(f"\nTokens used: {response.usage.total_tokens}")
        print(f"Prompt tokens: {response.usage.prompt_tokens}")
        print(f"Completion tokens: {response.usage.completion_tokens}")
        print("\n✅ SQL disambiguation test completed")
        print("\n📋 MANUAL REVIEW REQUIRED:")
        print("   - Does the model return valid JSON?")
        print("   - Is the resolved table correct (STAGING_CADENCE.GL_Staging)?")
        print("   - Is the reasoning logical?")
        print("   - Is the confidence score reasonable?")
        return True

    except Exception as e:
        print(f"❌ SQL disambiguation failed: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("\n🧪 AZURE OPENAI SMOKE TEST SUITE")
    print("Purpose: Evaluate model, system prompt, and fine-tuning needs")
    print()

    # Test connection
    client = test_connection()
    if not client:
        print("\n❌ ABORT: Cannot proceed without valid connection")
        return

    # Test basic completion
    if not test_basic_completion(client):
        print("\n❌ ABORT: Basic completion failed")
        return

    # Test SQL disambiguation
    test_sql_disambiguation(client)

    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Review model responses above")
    print("2. Document findings in docs/AI_MODEL_EVALUATION.md")
    print("3. Decide on:")
    print("   - Keep gpt-4.1-nano or try different model?")
    print("   - Refine system prompt based on results")
    print("   - Fine-tuning needed? (if responses are poor)")
    print("=" * 80)


if __name__ == "__main__":
    main()
