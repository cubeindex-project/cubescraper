# Cube Scraper

Utility scripts for downloading cube store product listings and normalizing them for insertion into Supabase.

## Project structure

```
src/                # scraping and data-import scripts
data/
  raw/              # raw product listings downloaded from stores
  processed/        # normalized product data ready for inspection/import
```

## Usage

Fetch products from a Shopify store:

```
python src/fetch_stores_products.py scs
```

Normalize and upload to Supabase (requires `.env.local` with credentials):

```
python src/add_cubes_to_database.py
```
