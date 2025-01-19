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
