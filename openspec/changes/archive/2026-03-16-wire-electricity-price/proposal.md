## Why

`electricity_price` is a dead-end node in the causal graph. It computes a yearly price from the trajectory input but nothing downstream reads it. Meanwhile, `oil_price` correctly feeds two causal channels (VMT adjustment and powertrain preference shift). Electricity price should affect EV adoption: rising electricity costs erode the EV operating cost advantage, dampening BEV preference.

## What Changes

- Add a new input node `ev_elec_price_elasticity` (scalar, default -0.05) to `macro_drivers.py`
- Extend `compute_pt_pref_shift_node` to accept `electricity_price` and `ev_elec_price_elasticity`, combining the oil and electricity effects into a single multiplier
- Update the `powertrain_preference_shift` node registration to wire the new upstream edges
- Add display name and description metadata to the new node

## Capabilities

### New Capabilities

### Modified Capabilities

- `macro-fleet-linkage`: Electricity price now feeds into powertrain preference shift via elasticity

## Impact

- **Backend**: `carbonsight/domain/macro_drivers.py` (new node, modified compute function and node registration)
- **No frontend changes**: The graph explorer already renders whatever the API returns; new node and edges appear automatically
- **No breaking changes**: Existing scenarios produce identical results when `ev_elec_price_elasticity` is at its default (-0.05) and electricity prices are at baseline — the multiplier is ~1.0
