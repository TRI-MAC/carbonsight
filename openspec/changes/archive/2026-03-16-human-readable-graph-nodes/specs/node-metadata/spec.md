## ADDED Requirements

### Requirement: Node display name field

Every DAG node SHALL have an optional `display_name` field (string or null) on the `Node` dataclass. When provided, this is the human-readable name shown in the UI. When null, the frontend SHALL fall back to the internal `name`.

#### Scenario: Node with display name

- **WHEN** a Node is created with `display_name="Surviving Fleet"`
- **THEN** the node's `display_name` attribute returns `"Surviving Fleet"`

#### Scenario: Node without display name

- **WHEN** a Node is created without specifying `display_name`
- **THEN** the node's `display_name` attribute is `None`

### Requirement: Node description field

Every DAG node SHALL have an optional `description` field (string or null) on the `Node` dataclass. Descriptions for compute nodes SHALL reference upstream dependencies by their display names.

#### Scenario: Compute node with upstream references

- **WHEN** the `post_scrappage` node has a description
- **THEN** the description references "Survival Curves" and "Aged Fleet" (the display names of its upstream nodes)

#### Scenario: Input node description

- **WHEN** an input node like `fleet_inventory` has a description
- **THEN** the description explains what data the node holds and its source

### Requirement: All fleet and emissions nodes have metadata

All 26 nodes defined in `fleet_nodes.py` and `emissions_nodes.py` SHALL have non-null `display_name` and `description` values.

#### Scenario: Fleet input nodes have metadata

- **WHEN** `create_fleet_dynamics_nodes()` is called
- **THEN** every returned Node has a non-null `display_name` and `description`

#### Scenario: Emissions nodes have metadata

- **WHEN** `create_emissions_nodes()` is called
- **THEN** every returned Node has a non-null `display_name` and `description`

### Requirement: API serves display metadata

The `/graph/nodes` and `/graph/nodes/{name}` endpoints SHALL include `display_name` and `description` fields in their JSON responses.

#### Scenario: List nodes includes display metadata

- **WHEN** a client calls `GET /graph/nodes`
- **THEN** each node object in the response contains `display_name` (string or null) and `description` (string or null)

#### Scenario: Single node includes display metadata

- **WHEN** a client calls `GET /graph/nodes/post_scrappage`
- **THEN** the response includes `display_name: "Surviving Fleet"` and a non-null `description`

### Requirement: Graph explorer shows display names

The graph explorer SHALL display `display_name` as the primary label on each node. The internal `name` SHALL be shown as a secondary label in smaller, monospace text.

#### Scenario: Node box rendering

- **WHEN** a node with `display_name="Surviving Fleet"` and `name="post_scrappage"` is rendered
- **THEN** "Surviving Fleet" is shown as the primary label and "post_scrappage" is shown below it in smaller monospace text

#### Scenario: Fallback when no display name

- **WHEN** a node has `display_name=null`
- **THEN** the node box shows `name` as the primary label (current behavior)

### Requirement: Detail panel shows description

The node detail panel SHALL display the node's `description` when a node is selected. The description SHALL appear between the type/tags section and the upstream connections section.

#### Scenario: Description in detail panel

- **WHEN** a user clicks on the "post_scrappage" node
- **THEN** the detail panel shows the display name as the header, and the description text in a dedicated section

#### Scenario: No description available

- **WHEN** a user clicks on a node with `description=null`
- **THEN** the description section is not rendered
