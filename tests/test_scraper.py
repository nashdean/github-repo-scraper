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
        'stars': {
            'min': 100,
            'max': 500
        },
        'push_date_filter': {
            'enabled': True,
            'type': 'days',
            'days': 30
        },
        'doc_filter': {
            'enabled': True,
            'min_readme_words': 200,
            'min_code_comment_ratio': 5,
            'require_docs_folder': True,
            'docs_folder_patterns': ['docs', 'documentation', 'doc', 'wiki'],
            'score_threshold': {
                'enabled': True,
                'min': 50,
                'max': None
            },
            'markdown_scoring': {
                'enabled': True,
                'weight': 5,
                'min_files': 2,
                'quality_checks': {
                    'enabled': False,
                    'grammar_weight': 10,
                    'max_grammar_errors': 10
                }
            }
        },
        'max_repos': 2
    }

def test_scraper_initialization(mock_api_client, config):
    scraper = GitHubScraper(mock_api_client, config)
    assert scraper.client == mock_api_client
    assert scraper.config == config

def test_search_query_formation(mock_api_client, config):
    scraper = GitHubScraper(mock_api_client, config)
    query = scraper._create_search_query('python')
    assert query == "topic:python stars:100..500 pushed:>=2023-09-30"

def test_should_include_repo(mock_api_client, config):
    scraper = GitHubScraper(mock_api_client, config)
    repo = {
        'documentation_stats': {
            'has_readme': True,
            'readme_word_count': 250,
            'docs_folders': ['docs'],
            'code_comment_ratio': 6,
            'quality_summary': {
                'score': 60
            }
        }
    }
    assert scraper._should_include_repo(repo) == True

    repo['documentation_stats']['quality_summary']['score'] = 40
    assert scraper._should_include_repo(repo) == False

def test_save_results(mock_api_client, config):
    scraper = GitHubScraper(mock_api_client, config)
    scraper.results = [
        {
            'id': 1,
            'name': 'repo1',
            'full_name': 'user/repo1',
            'owner': {
                'login': 'user',
                'id': 1,
                'type': 'User',
                'html_url': 'https://github.com/user',
                'email': 'user@example.com',
                'avatar_url': 'https://github.com/user.png',
                'social_links': {}
            },
            'description': 'A test repository',
            'html_url': 'https://github.com/user/repo1',
            'language': 'Python',
            'topics': ['python'],
            'visibility': 'public',
            'forks_count': 10,
            'stargazers_count': 100,
            'watchers_count': 50,
            'open_issues_count': 5,
            'created_at': '2023-01-01T00:00:00Z',
            'updated_at': '2023-01-01T00:00:00Z',
            'pushed_at': '2023-01-01T00:00:00Z',
            'has_issues': True,
            'has_discussions': False,
            'has_pages': False,
            'fork': False,
            'license': None,
            'documentation_stats': {
                'has_readme': True,
                'readme_word_count': 250,
                'docs_folders': ['docs'],
                'code_comment_ratio': 6,
                'quality_summary': {
                    'score': 60
                }
            },
            'recent_activity': {},
            'emails': [],
            'social_links': {}
        }
    ]
    output_settings = {
        'format': 'json',
        'path': 'data/repos'
    }
    with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
        scraper.save_results(output_settings)
        mock_file.assert_called_once_with('data/repos/repositories_20230930_000000.json', 'w')
