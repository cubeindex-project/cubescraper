# Cube Scraper

Cube Scraper is a collection of small Python utilities for helping building and maintaining a cube product index.

[![Update Cube Prices](https://github.com/cubeindex-project/cubescraper/actions/workflows/update-prices.yml/badge.svg?branch=main)](https://github.com/cubeindex-project/cubescraper/actions/workflows/update-prices.yml)

## Requirements

- Python 3.9 or newer
- [Supabase](https://supabase.com) project credentials

Install dependencies with:

```
pip install -r requirements.txt
```

Copy `.env.example` to `.env.local` and fill in your credentials:

```
SUPABASE_URL=<https://your-project.supabase.co>
SUPABASE_SECRET_KEY=<secret-key>
```

## Usage

### Main scripts

- `scripts/update-prices.sh` refreshes vendor link price and availability.
- `scripts/run-info-scraper-server.sh` starts a local server that takes HTTP requests to scrape cube product information from vendor websites.

## License

This project is available under the Apache 2.0 License.  See `LICENSE` for details.
