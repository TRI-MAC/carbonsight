## 1. Backend: Node dataclass

- [x] 1.1 Add `display_name: str | None = None` and `description: str | None = None` fields to the `Node` dataclass in `core/node.py`

## 2. Backend: Populate node metadata

- [x] 2.1 Add `display_name` and `description` to all fleet input nodes in `fleet_nodes.py` (fleet_inventory, survival_curves, vmt_by_age, powertrain_proportions, annual_sales_volume, sales_growth_rate, reshuffle_probability, new_vehicle_attrs, year_index)
- [x] 2.2 Add `display_name` and `description` to all fleet compute nodes in `fleet_nodes.py` (aged_fleet, post_scrappage, scrapped_vehicles, post_new_entry, post_vmt_assignment, adjusted_vmt, post_used_market, fleet_snapshot)
- [x] 2.3 Add `display_name` and `description` to all emissions input nodes in `emissions_nodes.py` (production_body, production_ice, production_battery_per_kwh, gas_ghg_per_gallon, grid_ghg_per_kwh, disposal_per_vehicle)
- [x] 2.4 Add `display_name` and `description` to all emissions compute nodes in `emissions_nodes.py` (fleet_production_ghg, fleet_usage_ghg, scrapped_disposal_ghg, total_emissions)

## 3. Backend: API endpoints

- [x] 3.1 Add `display_name` and `description` to the `/graph/nodes` list endpoint response in `api.py`
- [x] 3.2 Add `display_name` and `description` to the `/graph/nodes/{name}` detail endpoint response in `api.py`

## 4. Frontend: Types and rendering

- [x] 4.1 Add `display_name?: string` and `description?: string` to the `GraphNode` interface in `types/index.ts`
- [x] 4.2 Update node box label in `GraphPage.tsx` to show `display_name` as primary and `name` as secondary monospace subtitle
- [x] 4.3 Update detail panel header to show `display_name` as title with `name` as subtitle
- [x] 4.4 Add description section to detail panel between type/tags and upstream connections
- [x] 4.5 Update demo fallback data in `GraphPage.tsx` to include `display_name` and `description` fields

## 5. Verification

- [x] 5.1 Run backend tests to confirm Node dataclass changes don't break existing tests
- [x] 5.2 Run frontend tests to confirm GraphPage rendering works with new fields
- [x] 5.3 Verify all 27 nodes have non-null display_name and description by inspection or test
