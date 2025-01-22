from typing import List, Dict, Any
from jinja2 import Template

class HTMLRenderer:
    def __init__(self, template_str: str):
        self.template = Template(template_str)

    def render(self, results: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
        return self.template.render(results=results, metadata=metadata)

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
                        <td>{{ repo.stargazers_count }}</td>
                        <td>{{ repo.forks_count }}</td>
                        <td>{{ repo.open_issues_count }}</td>
                        <td>{{ repo.documentation_stats.quality_summary.score }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <h2>Metadata</h2>
            <p><strong>Timestamp:</strong> {{ metadata.timestamp }}</p>
            <h3>Settings</h3>
            <pre>{{ metadata.settings | tojson(indent=2) }}</pre>
            <h3>Rate Limit Information</h3>
            <p>Rate limit remaining: {{ metadata.rate_limit_info.rate_limit_remaining }}</p>
            <p>Rate limit reset time: {{ metadata.rate_limit_info.rate_limit_reset }}</p>
        </body>
        </html>
        """
