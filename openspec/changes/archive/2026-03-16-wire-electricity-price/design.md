## Context

The macro driver system has two price trajectories (oil, electricity) but only oil price feeds downstream nodes. `electricity_price` is computed each year but nothing reads it. The `DEFAULT_ELASTICITIES` list documents an intended link (`electricity_price → ev_operating_cost_advantage`, elasticity -0.05) that was never wired into the DAG.

The oil price affects powertrain preference via `compute_pt_pref_shift_node(oil_price, powertrain_pref_oil_elasticity) → multiplier`. We need electricity price to also affect this same multiplier.

## Goals / Non-Goals

**Goals:**

- Wire electricity price into the powertrain preference shift computation
- Follow the same elasticity pattern used for oil price
- Combined effect: `shift = oil_effect * electricity_effect`
- New `ev_elec_price_elasticity` input node with default -0.05

**Non-Goals:**

- Electricity price affecting VMT (too fine-grained for this model's resolution)
- Electricity price affecting grid carbon intensity (different causal mechanism)
- Adding a separate `ev_cost_adjustment` intermediate node (unnecessary complexity)

## Decisions

### 1. Extend existing compute function rather than adding intermediate nodes

Modify `compute_pt_pref_shift_node` to take `electricity_price` and `ev_elec_price_elasticity` as additional parameters. The function computes oil effect and electricity effect independently, then multiplies them. This keeps one multiplier flowing into `post_new_entry`.

**Alternative considered**: A new `ev_cost_adjustment` intermediate node that feeds into a `combined_preference` combiner node. Rejected — adds two nodes and an abstraction layer for a simple multiplicative combination.

### 2. Baseline electricity price as parameter with sensible default

The elasticity computation needs a baseline to measure percentage change from. Use a `baseline_electricity_price` parameter defaulting to the first value in the trajectory (same pattern as oil price baseline of $75/bbl).

### 3. Negative elasticity convention

`ev_elec_price_elasticity = -0.05` means: a 10% rise in electricity price produces a 0.5% decrease in the powertrain preference shift. This makes the shift drop below 1.0, reducing BEV share — economically correct since higher electricity costs erode EV operating advantage.

## Risks / Trade-offs

- **Small effect size**: At -0.05, electricity price has half the magnitude of oil price (0.1) on powertrain preference. This is intentional — fuel cost is a larger share of operating cost for ICEVs than electricity is for BEVs. → Can be tuned via the adjustable input node.
- **Independence assumption**: Oil and electricity effects are multiplied independently. In reality they're correlated (both track energy markets). → Acceptable simplification for a 10-year macro model.
