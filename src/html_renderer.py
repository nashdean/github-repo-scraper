from typing import List, Dict, Any
from jinja2 import Template

class HTMLRenderer:
    def __init__(self, template_str: str):
        self.template = Template(template_str)

    def render(self, results: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
        return self.template.render(results=results, metadata=metadata)

    def render_repo(self, repo: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        repo_template_str = self.get_repo_template()
        repo_template = Template(repo_template_str)
        return repo_template.render(repo=repo, metadata=metadata)

    def render_settings(self, metadata: Dict[str, Any]) -> str:
        settings_template_str = self.get_settings_template()
        settings_template = Template(settings_template_str)
        return settings_template.render(metadata=metadata)

    @staticmethod
    def get_default_template() -> str:
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>GitHub Repository Scraper Report</title>
            <style>
                body { font-family: Arial, sans-serif; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>GitHub Repository Scraper Report</h1>
            <p><strong>Total Repositories Stored:</strong> {{ metadata.total_repos_stored }}</p>
            <p><strong>Total Repositories Scraped:</strong> {{ metadata.total_repos_scraped }}</p>
            <table>
                <thead>
                    <tr>
                        <th>Repository</th>
                        <th>Description</th>
                        <th>Stars</th>
                        <th>Forks</th>
                        <th>Open Issues</th>
                        <th>Documentation Score</th>
                    </tr>
                </thead>
                <tbody>
                    {% for repo in results %}
                    <tr>
                        <td><a href="{{ repo.html_url }}">{{ repo.full_name }}</a></td>
                        <td>{{ repo.description or 'No description' }}</td>
                        <td>{{ repo.stargazers_count | int }}</td>
                        <td>{{ repo.forks_count | int }}</td>
                        <td>{{ repo.open_issues_count | int }}</td>
                        <td><a href="score_details/{{ repo.full_name.replace('/', '_') }}.html">{{ repo.documentation_stats.quality_summary.score | int }}</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <h3>Settings</h3>
            <p><a href="settings.html">View Settings</a></p>
            <h3>Rate Limit Information</h3>
            <p>Rate limit remaining: {{ metadata.rate_limit_info.rate_limit_remaining | int }}</p>
            <p>Rate limit reset time: {{ metadata.rate_limit_info.rate_limit_reset }}</p>
            <p><strong>Metadata Timestamp Generated at:</strong> {{ metadata.timestamp }}</p>
        </body>
        </html>
        """

    @staticmethod
    def get_repo_template() -> str:
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ repo.full_name }} Documentation Breakdown</title>
            <style>
                body { font-family: Arial, sans-serif; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; }
                th { background-color: #f2f2f2; }
                .button {
                    display: inline-block;
                    padding: 10px 20px;
                    font-size: 16px;
                    cursor: pointer;
                    text-align: center;
                    text-decoration: none;
                    outline: none;
                    color: #fff;
                    background-color: #4CAF50;
                    border: none;
                    border-radius: 15px;
                    box-shadow: 0 9px #999;
                }
                .button:hover {background-color: #3e8e41}
                .button:active {
                    background-color: #3e8e41;
                    box-shadow: 0 5px #666;
                    transform: translateY(4px);
                }
                .bold { font-weight: bold; }
            </style>
        </head>
        <body>
            <a href="../index.html" class="button">Return to Report</a>
            <h1>{{ repo.full_name }} Documentation Breakdown</h1>
            <p><strong>Description:</strong> {{ repo.description or 'No description' }}</p>
            <p><strong>Stars:</strong> {{ repo.stargazers_count | int }}</p>
            <p><strong>Forks:</strong> {{ repo.forks_count | int }}</p>
            <p><strong>Open Issues:</strong> {{ repo.open_issues_count | int }}</p>
            <h2>Documentation Quality Summary</h2>
            <p><strong>Score:</strong> {{ repo.documentation_stats.quality_summary.score | int }}</p>
            <h3>Issues</h3>
            <ul>
                {% for issue in repo.documentation_stats.quality_summary.issues %}
                <li>{{ issue }}</li>
                {% endfor %}
            </ul>
            <h3>Suggestions</h3>
            <ul>
                {% for suggestion in repo.documentation_stats.quality_summary.suggestions %}
                <li>{{ suggestion }}</li>
                {% endfor %}
            </ul>
            <h3>Scoring Breakdown</h3>
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Criteria</th>
                        <th>Max Score</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    {% for category, details in repo.documentation_stats.quality_summary.scoring_breakdown.items() %}
                    <tr>
                        <td>{{ category }}</td>
                        <td>{{ details.criteria | join(', ') }}</td>
                        <td>{{ details.max_score | int }}</td>
                        <td class="bold">{{ details.score | int }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <h3>Metadata</h3>
            <p><strong>Timestamp:</strong> {{ metadata.timestamp }}</p>
        </body>
        </html>
        """

    @staticmethod
    def get_settings_template() -> str:
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Scraping Session Settings</title>
            <style>
                body { font-family: Arial, sans-serif; }
                .button {
                    display: inline-block;
                    padding: 10px 20px;
                    font-size: 16px;
                    cursor: pointer;
                    text-align: center;
                    text-decoration: none;
                    outline: none;
                    color: #fff;
                    background-color: #4CAF50;
                    border: none;
                    border-radius: 15px;
                    box-shadow: 0 9px #999;
                }
                .button:hover {background-color: #3e8e41}
                .button:active {
                    background-color: #3e8e41;
                    box-shadow: 0 5px #666;
                    transform: translateY(4px);
                }
            </style>
        </head>
        <body>
            <a href="index.html" class="button">Return to Report</a>
            <h1>Scraping Session Settings</h1>
            <pre>{{ metadata.settings | tojson(indent=2) }}</pre>
        </body>
        </html>
        """
