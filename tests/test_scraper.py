import pytest
from unittest.mock import Mock, patch
from src.scraper import GitHubScraper

@pytest.fixture
def mock_api_client():
    return Mock()

@pytest.fixture
def config():
    return {
        'topics': ['python'],
        'min_stars': 100,
        'max_repos': 2
    }

def test_scraper_initialization(mock_api_client, config):
    scraper = GitHubScraper(mock_api_client, config)
    assert scraper.client == mock_api_client
    assert scraper.config == config

def test_search_query_formation(mock_api_client, config):
    scraper = GitHubScraper(mock_api_client, config)
    query = scraper._create_search_query('python')
    assert query == "topic:python stars:>=100"
