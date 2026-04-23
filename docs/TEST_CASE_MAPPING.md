# Test Case Mapping

| Test Case | Status | Evidence in code |
|---|---|---|
| TC-001 Producer registration | Implemented | `POST /api/producers/register/` |
| TC-002 Customer registration | Implemented | `POST /api/customers/register/` |
| TC-003 Product listing | Implemented | `POST /api/products/`, owner-only edits on `/api/products/<id>/` |
| TC-004 Category browsing | Implemented | `GET /api/categories/`, `GET /api/products/?category=` |
| TC-005 Search | Implemented | `GET /api/products/?search=` |
| TC-006 Cart add/update/remove | Implemented | `POST /api/cart/add/`, `PATCH/DELETE /api/cart/items/<id>/` |
| TC-007 Single-vendor checkout | Implemented | `POST /api/orders/create/` |
| TC-008 Multi-vendor checkout | Partially implemented strongly | grouped cart + sub-orders + per-producer delivery dates |
| TC-009 Producer incoming orders | Implemented | `GET /api/producer-orders/<producer_id>/` |
| TC-010 Order status updates | Implemented | `PATCH /api/producer-suborders/<id>/status/` |
| TC-011 Inventory updates | Implemented | stock decrement + visibility change + `InventoryLog` |
| TC-012 Weekly settlements | Implemented | `POST /api/settlements/<producer_id>/` |
| TC-013 Food miles | Implemented | order total food miles + postcode distance service |
| TC-014 Organic filtering | Implemented | `GET /api/products/?organic_only=true` |
| TC-015 Allergen visibility | Implemented baseline | `allergen_info` required/defaulted in serializer and exposed in product/cart/order payloads |

## Current automated tests
- browse visible products
- add to cart + create order
- product ownership editing
- customer blocked from producer endpoint
- admin dashboard permission
- status progression validation
- AI recommend endpoint
- AI quality grading endpoint
