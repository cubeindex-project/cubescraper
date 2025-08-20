# Cube Scraper

Cube Scraper is a collection of small Python utilities for building a cube
product index.  The scripts can download listings from several cube stores,
normalize the data and push it to a Supabase database.  A separate tool keeps
vendor prices in sync with the database.

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
data/
  raw/              # raw product listings downloaded from stores
  processed/        # normalized product data ready for inspection/import
```

## Usage

### 1. Fetch products from a Shopify store

Download all products for a supported store (e.g. `scs`, `cubicle`):

```
python src/scrap_cubes_from_stores/fetch_stores_products.py scs
```

The script writes `<store>_products.json` to `data/raw/`.

### 2. Normalize and upload to Supabase

After downloading product files, normalize them and upsert into the database:

```
python src/scrap_cubes_from_stores/add_cubes_to_database.py
```

### 3. Track vendor prices

Periodically update prices and availability for known vendor links:

```
python src/price_tracking/fetch_cube_price.py --limit 20 --log
```

Force check all supported links (ignoring cooldown) with:

```
python src/price_tracking/fetch_cube_price.py --force --log
```

## License

This project is available under the MIT License.  See `LICENSE` for details.

