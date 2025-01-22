import pytest
from unittest.mock import Mock, patch
from src.api_client import GitHubAPIClient

@pytest.fixture
def api_config():
    return {
        'base_url': 'https://api.github.com',
        'timeout': 30,
        'rate_limit_pause': 60,
        'activity_limit': 30
    }

def test_get_user_contributions(api_config):
    with patch('requests.Session') as mock_session:
        mock_response = Mock()
        mock_response.json.return_value = [
            {'type': 'PushEvent', 'created_at': '2024-01-18T00:00:00Z'},
            {'type': 'IssueEvent', 'created_at': '2024-01-17T00:00:00Z'}
        ]
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response

        client = GitHubAPIClient('test_token', api_config)
        result = client.get_user_contributions('test_user')

        assert 'total_contributions' in result
        assert 'contribution_types' in result
        assert 'recent_events' in result
        assert result['total_contributions'] == 2

def test_get_user_profile_html(api_config):
    with patch('requests.Session') as mock_session:
        mock_response = Mock()
        # Simulate HTML with social links and email
        mock_response.text = '''
        <html>
            <body>
                <li itemprop="email"><a>test@example.com</a></li>
                <a rel="nofollow me" href="https://twitter.com/testuser">Twitter</a>
                <a rel="nofollow me" href="https://linkedin.com/in/testuser">LinkedIn</a>
            </body>
        </html>
        '''
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response

        client = GitHubAPIClient('test_token', api_config)
        result = client._get_user_profile_html('testuser')

        assert result['email'] == 'test@example.com'
        assert 'twitter' in result['social_links']
        assert 'linkedin' in result['social_links']

def test_check_rate_limit(api_config):
    with patch('requests.Session') as mock_session:
        mock_response = Mock()
        mock_response.json.return_value = {
            'resources': {
                'core': {
                    'limit': 5000,
                    'remaining': 4999,
                    'reset': 1609459200
                }
            }
        }
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response

        client = GitHubAPIClient('test_token', api_config)
        rate_limit = client.check_rate_limit()

        assert 'resources' in rate_limit
        assert 'core' in rate_limit['resources']
        assert rate_limit['resources']['core']['remaining'] == 4999

def test_search_repositories(api_config):
    with patch('requests.Session') as mock_session:
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {'id': 1, 'name': 'repo1', 'full_name': 'user/repo1'},
                {'id': 2, 'name': 'repo2', 'full_name': 'user/repo2'}
            ]
        }
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response

        client = GitHubAPIClient('test_token', api_config)
        result = client.search_repositories('topic:python', page=1)

        assert 'items' in result
        assert len(result['items']) == 2
        assert result['items'][0]['name'] == 'repo1'

def test_get_repository(api_config):
    with patch('requests.Session') as mock_session:
        mock_repo_response = Mock()
        mock_repo_response.json.return_value = {
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
            }
        }
        mock_repo_response.status_code = 200

        mock_doc_stats_response = Mock()
        mock_doc_stats_response.json.return_value = {
            'has_readme': True,
            'readme_word_count': 250,
            'docs_folders': ['docs'],
            'code_comment_ratio': 6,
            'quality_summary': {
                'score': 60
            }
        }
        mock_doc_stats_response.status_code = 200

        mock_session.return_value.get.side_effect = [mock_repo_response, mock_doc_stats_response]

        client = GitHubAPIClient('test_token', api_config)
        result = client.get_repository('user', 'repo1')

        assert 'id' in result
        assert result['id'] == 1
        assert 'documentation_stats' in result
        assert result['documentation_stats']['has_readme'] == True
