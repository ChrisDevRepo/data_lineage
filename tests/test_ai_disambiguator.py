"""
Unit Tests for AI Disambiguator
================================

Tests for Azure OpenAI-based SQL table disambiguation.

Author: Vibecoding
Version: 3.7.0
Date: 2025-10-31
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# Import the module to test
from lineage_v3.parsers.ai_disambiguator import AIDisambiguator, AIResult
from lineage_v3.core.duckdb_workspace import DuckDBWorkspace


class TestAIDisambiguatorInit:
    """Test AIDisambiguator initialization."""

    def test_init_requires_workspace(self):
        """Test that AIDisambiguator requires a DuckDBWorkspace."""
        with pytest.raises(TypeError):
            AIDisambiguator()  # Should fail without workspace

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_init_loads_prompt(self, mock_azure_client):
        """Test that system prompt is loaded on initialization."""
        # Mock workspace
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_workspace.conn = Mock()

        # Create disambiguator
        disambiguator = AIDisambiguator(mock_workspace)

        # Verify prompt was loaded
        assert disambiguator.system_prompt is not None
        assert len(disambiguator.system_prompt) > 0

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_init_creates_azure_client(self, mock_azure_client):
        """Test that Azure OpenAI client is created."""
        # Set up environment
        os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'
        os.environ['AZURE_OPENAI_API_KEY'] = 'test-key'

        # Mock workspace
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_workspace.conn = Mock()

        # Create disambiguator
        disambiguator = AIDisambiguator(mock_workspace)

        # Verify Azure client was initialized
        mock_azure_client.assert_called_once()
        assert disambiguator.client is not None


class TestCatalogValidation:
    """Test Layer 1: Catalog validation."""

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_validate_catalog_accepts_valid_table(self, mock_azure_client):
        """Test that catalog validation accepts tables that exist in metadata."""
        # Mock workspace with table in catalog
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.return_value = (1,)  # Table exists
        mock_workspace.conn = mock_conn

        disambiguator = AIDisambiguator(mock_workspace)

        # Test validation
        result = disambiguator._validate_catalog("dbo.TestTable")

        assert result is True
        mock_conn.execute.assert_called_once()

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_validate_catalog_rejects_nonexistent_table(self, mock_azure_client):
        """Test that catalog validation rejects tables not in metadata."""
        # Mock workspace with table NOT in catalog
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.return_value = (0,)  # Table doesn't exist
        mock_workspace.conn = mock_conn

        disambiguator = AIDisambiguator(mock_workspace)

        # Test validation
        result = disambiguator._validate_catalog("dbo.NonExistentTable")

        assert result is False

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_validate_catalog_handles_invalid_format(self, mock_azure_client):
        """Test that catalog validation rejects invalid table format."""
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_workspace.conn = Mock()

        disambiguator = AIDisambiguator(mock_workspace)

        # Test with invalid format (no schema)
        result = disambiguator._validate_catalog("JustTableName")

        assert result is False


class TestRegexImprovementValidation:
    """Test Layer 2: Regex improvement validation."""

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_validate_regex_improvement_accepts_improvement(self, mock_azure_client):
        """Test that validation accepts AI results that improve upon regex baseline."""
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_workspace.conn = Mock()

        disambiguator = AIDisambiguator(mock_workspace)

        # AI found dependencies where regex found none
        ai_response = {'resolved_table': 'dbo.Table1', 'confidence': 0.85}
        parser_result = {
            'quality': {
                'regex_sources': 0,
                'regex_targets': 0,
                'parser_sources': 0,
                'parser_targets': 0
            }
        }

        result = disambiguator._validate_regex_improvement(ai_response, parser_result)

        assert result is True  # AI improved upon baseline

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_validate_regex_improvement_accepts_maintained_level(self, mock_azure_client):
        """Test that validation accepts AI results that maintain regex level."""
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_workspace.conn = Mock()

        disambiguator = AIDisambiguator(mock_workspace)

        # Regex already found some dependencies
        ai_response = {'resolved_table': 'dbo.Table1', 'confidence': 0.85}
        parser_result = {
            'quality': {
                'regex_sources': 2,
                'regex_targets': 1,
                'parser_sources': 2,
                'parser_targets': 1
            }
        }

        result = disambiguator._validate_regex_improvement(ai_response, parser_result)

        assert result is True  # AI maintains baseline (for now, simplified logic)


class TestQueryLogValidation:
    """Test Layer 3: Query log cross-validation."""

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_query_log_validation_boosts_confidence(self, mock_azure_client):
        """Test that query log confirmation boosts confidence."""
        # Mock workspace with query logs
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_conn = Mock()
        # First call: check if query logs exist (return 1)
        # Second call: search for table in logs (return 5 matches)
        mock_conn.execute.return_value.fetchone.side_effect = [(1,), (5,)]
        mock_workspace.conn = mock_conn

        disambiguator = AIDisambiguator(mock_workspace)

        # Test validation
        ai_response = {'resolved_table': 'dbo.Table1', 'confidence': 0.85}
        boosted_confidence = disambiguator._validate_query_logs(ai_response, 'spTestProcedure')

        # Confidence should be boosted
        assert boosted_confidence > 0.85
        assert boosted_confidence <= 0.95  # Max boost

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_query_log_validation_no_boost_if_not_found(self, mock_azure_client):
        """Test that confidence is not boosted if not found in query logs."""
        # Mock workspace with query logs but no matches
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.side_effect = [(1,), (0,)]  # Logs exist, no matches
        mock_workspace.conn = mock_conn

        disambiguator = AIDisambiguator(mock_workspace)

        # Test validation
        ai_response = {'resolved_table': 'dbo.Table1', 'confidence': 0.85}
        confidence = disambiguator._validate_query_logs(ai_response, 'spTestProcedure')

        # Confidence should remain same
        assert confidence == 0.85

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_query_log_validation_handles_no_logs(self, mock_azure_client):
        """Test that validation handles absence of query logs gracefully."""
        # Mock workspace without query logs
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.return_value = (0,)  # No query logs
        mock_workspace.conn = mock_conn

        disambiguator = AIDisambiguator(mock_workspace)

        # Test validation
        ai_response = {'resolved_table': 'dbo.Table1', 'confidence': 0.85}
        confidence = disambiguator._validate_query_logs(ai_response, 'spTestProcedure')

        # Confidence should remain same
        assert confidence == 0.85


class TestDisambiguate:
    """Test main disambiguate() method with mocked AI calls."""

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_disambiguate_returns_none_for_no_candidates(self, mock_azure_client):
        """Test that disambiguate returns None when no candidates provided."""
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_workspace.conn = Mock()

        disambiguator = AIDisambiguator(mock_workspace)

        result = disambiguator.disambiguate(
            reference='TestTable',
            candidates=[],  # No candidates
            sql_context='SELECT * FROM TestTable',
            parser_result={},
            sp_name='spTest'
        )

        assert result is None

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_disambiguate_handles_api_error(self, mock_azure_client):
        """Test that disambiguate handles Azure API errors gracefully."""
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_workspace.conn = Mock()

        # Create disambiguator with mocked AI client that raises error
        disambiguator = AIDisambiguator(mock_workspace)
        disambiguator._call_azure_openai = Mock(side_effect=Exception("API Error"))

        result = disambiguator.disambiguate(
            reference='TestTable',
            candidates=['dbo.TestTable', 'schema2.TestTable'],
            sql_context='SELECT * FROM TestTable',
            parser_result={'quality': {'regex_sources': 0, 'regex_targets': 0}},
            sp_name='spTest'
        )

        # Should return None on error
        assert result is None


class TestHelperMethods:
    """Test helper methods."""

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_resolve_to_object_id(self, mock_azure_client):
        """Test resolving table name to object_id."""
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.return_value = (12345,)  # object_id
        mock_workspace.conn = mock_conn

        disambiguator = AIDisambiguator(mock_workspace)

        object_id = disambiguator._resolve_to_object_id('dbo.TestTable')

        assert object_id == 12345

    @patch('lineage_v3.parsers.ai_disambiguator.AzureOpenAI')
    def test_resolve_to_object_id_handles_not_found(self, mock_azure_client):
        """Test that _resolve_to_object_id returns None when table not found."""
        mock_workspace = Mock(spec=DuckDBWorkspace)
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.return_value = None  # Not found
        mock_workspace.conn = mock_conn

        disambiguator = AIDisambiguator(mock_workspace)

        object_id = disambiguator._resolve_to_object_id('dbo.NonExistent')

        assert object_id is None


# Integration test marker (requires actual Azure OpenAI credentials)
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv('AZURE_OPENAI_API_KEY'),
    reason="Azure OpenAI credentials not configured"
)
class TestAIIntegration:
    """Integration tests that require actual Azure OpenAI API access."""

    def test_real_ai_call(self):
        """Test actual AI disambiguation call (requires credentials)."""
        # This test is skipped unless AZURE_OPENAI_API_KEY is set
        # Use for manual testing with real API
        pytest.skip("Integration test - run manually with credentials")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
