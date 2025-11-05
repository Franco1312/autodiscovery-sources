"""Tests for ranking and selection."""

from autodiscovery_sources.domain.entities import DiscoveredFile
from autodiscovery_sources.domain.value_objects import Url
from autodiscovery_sources.engine.ranker import Ranker


def test_ranking():
    """Test ranking of candidates."""
    ranker = Ranker()
    
    candidates = [
        DiscoveredFile(
            key="test",
            url=Url(value="https://example.com/test.xlsx"),
            filename="test.xlsx",
            score=0,
        ),
        DiscoveredFile(
            key="test",
            url=Url(value="https://example.com/other.xls"),
            filename="other.xls",
            score=0,
        ),
    ]
    
    match_config = {"patterns": []}
    ranked = ranker.rank(candidates, match_config)
    
    # Both should have extension bonus (30), but order may vary
    # Just verify they both have scores
    assert ranked[0].score >= 30
    assert ranked[1].score >= 30


def test_ranking_with_tokens():
    """Test ranking with strong tokens."""
    ranker = Ranker()
    
    candidates = [
        DiscoveredFile(
            key="test",
            url=Url(value="https://example.com/REM-series.xlsx"),
            filename="REM-series.xlsx",
            score=0,
        ),
        DiscoveredFile(
            key="test",
            url=Url(value="https://example.com/generic.xlsx"),
            filename="generic.xlsx",
            score=0,
        ),
    ]
    
    match_config = {"patterns": []}
    ranked = ranker.rank(candidates, match_config)
    
    # REM should score higher
    assert "REM" in ranked[0].url.value.upper()
    assert ranked[0].score > ranked[1].score

