# Cube Scraper

Cube Scraper is a collection of small Python utilities for helping building and maintaining a cube
product index.

[![Fetch Cube Prices](https://github.com/cubeindex-project/cubescraper/actions/workflows/update_cubes_prices.yml/badge.svg)](https://github.com/cubeindex-project/cubescraper/actions/workflows/update_cubes_prices.yml)

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
SUPABASE_SERVICE_KEY=<service-role-key>
```

## Project structure

```
src/                # scraping and data-import scripts
```

## Usage

### Main scripts

- `python src/cubescraper/price_tracker/main.py [--commit]` refreshes vendor link price and availability with optional HTML capture for debugging.

### Deprecated (legacy store scraping)

The older Shopify scraping pipeline is no longer maintained but remains in the repo:

- `src/cubescraper/deprecated/scrap_cubes_from_stores/fetch_stores_products.py` (download raw store product JSON)
- `src/cubescraper/deprecated/scrap_cubes_from_stores/add_cubes_to_database.py` (normalize and upsert products)

## License

This project is available under the MIT License.  See `LICENSE` for details.
