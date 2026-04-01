# Catalog (Product Catalog)

The `catalog` app is responsible for managing and presenting the product catalog in SwedeSweets.

It serves as the **source of truth for available products** and provides a clean, mobile-friendly interface for browsing items before ordering.

---

## Purpose

The catalog replaces unstructured product communication (e.g. SMS lists) with a **clear, structured, and visual product overview**.

It is designed to:

* make it easy for stores to browse products
* reduce ordering mistakes
* support future filtering (tags, categories)
* provide a simple admin interface for managing products

---

## Core Concepts

### Product

Represents a single item that can be ordered.

Fields:

* `code` — unique numeric identifier (used in ordering)
* `name` — display name
* `description` — optional text shown in product detail view
* `ingredients` — optional (useful for food/allergens)
* `image` — optional product image (mobile UX)
* `is_active` — controls availability without deleting history

Additional optional metadata:

* `weight_grams` — weight per unit (e.g. chips bag)
* `units_per_box` — number of units per carton

---

### ProductCategory

A product belongs to **one category**.

Used for:

* grouping products in the UI
* structuring the catalog into sections

Examples:

* Candy
* Chips
* Drinks

---

### ProductTag

A product can have **multiple tags**.

Used for:

* future filtering
* labeling product attributes

Examples:

* Sour
* Vegan
* Gluten-free
* New

---

## Design Principles

### 1. Admin-first (B2B system)

* Products are managed via Django admin
* No public product creation
* Store users only browse and order

---

### 2. Separation of concerns

* Models define data structure
* Views prepare data
* Templates render UI

No business logic in templates.

---

### 3. Availability vs existence

A key design decision:

* `Product exists` → always viewable
* `is_active = False` → shown but marked unavailable

This avoids breaking links and preserves history.

---

### 4. Snapshot-friendly

Orders store:

* product code
* product name

This ensures:

* historical integrity
* independence from catalog changes

---

## Views

### `product_list`

Displays:

* all categories
* active products grouped per category

Optimized with `prefetch_related` to avoid N+1 queries.

---

### `product_detail`

Displays:

* full product information
* image, metadata, description, ingredients

Handles:

* inactive products (shown with warning)
* non-existing products (404)

---

## Templates

Structure:

```text
catalog/templates/catalog/
├── product_list.html
└── product_detail.html
```

Templates extend a global `base.html` and focus only on:

```text
presentation, not logic
```

---

## Media (Images)

Images are stored via:

```text
ImageField(upload_to="products/")
```

Served locally via:

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

---

## Future Improvements

Planned extensions:

* Next/previous product navigation
* search and filtering (tags)
* better mobile UI (cards, sections, chips)
* product variants (sizes, packs)
* multilingual support
* caching for catalog queries

---

## Summary

The catalog app provides:

* a clean, structured product model
* a mobile-friendly browsing experience
* a stable foundation for ordering

It is intentionally simple in v0.1, but designed to scale without breaking existing data or flows.
