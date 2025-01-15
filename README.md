# GitHub Repository Scraper

A configurable tool to scrape GitHub repositories based on topics and star counts.

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up your GitHub token:
```bash
export GITHUB_TOKEN=your_github_token
```

## Configuration

Edit `config/settings.yaml` to configure:
- API settings
- Scraping parameters
- Output format and location

## Usage

Run the scraper:
```bash
python main.py
```

## Testing

Run tests:
```bash
pytest tests/
```
