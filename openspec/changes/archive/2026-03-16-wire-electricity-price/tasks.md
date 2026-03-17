## 1. Data model

- [x] 1.1 Add `ev_elec_price_elasticity` field (default -0.05) to `MacroDriverDefaults` in `data/models.py`

## 2. Macro driver compute functions

- [x] 2.1 Extend `compute_pt_pref_shift_node` in `macro_drivers.py` to accept `electricity_price` and `ev_elec_price_elasticity`, combining oil and electricity effects multiplicatively
- [x] 2.2 Add `ev_elec_price_elasticity` input node to `create_macro_driver_nodes()` with display_name="EV Electricity Price Elasticity" and description
- [x] 2.3 Update `powertrain_preference_shift` node description to reference **Electricity Price** and **EV Electricity Price Elasticity** as additional upstream inputs
- [x] 2.4 Update `DEFAULT_ELASTICITIES` to point to the actual node names used in the DAG

## 3. Verification

- [x] 3.1 Run backend tests — confirm no regressions
- [x] 3.2 Verify `electricity_price` is no longer a leaf node: it should appear as upstream of `powertrain_preference_shift` in the graph API response
- [x] 3.3 Verify that flat electricity trajectory produces preference shift identical to oil-only effect
