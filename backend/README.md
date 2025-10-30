# Ekiden

This directory is for the Ekiden research platform

## Intended use
The primary use of Carbon Sight Causal Modeling is for research and development of counterfactual simulations in the domain of LDV decarbonization. The intended users are researchers interested in climate change, including public policy researchers, transportation researchers, causal modelers, climate change mitigation strategists and behavioral scientists.

## Licensing
Carbon Sight Causal Modeling is released under an MIT License. Copyright (c) 2025 Toyota Research Institute, Inc. Toyota did not provide any of the materials used to build the model. The model here is for reference and verification of the procedures described in the paper. See the paper for more details.
The model is provided as-is. Toyota Research Institute disclaims all warranties, expressed or implied, including any warranty of merchantability and fitness for a particular purpose.


## Streamlit application
The backend is a Streamlit app with main file at `ekiden.py`.

## Running locally
You can either run the app in your host machine directly or by using Docker. To run directly, follow these steps:

1. Create a virtual environment: `python -m virtualenv venv; source venv/bin/activate`
2. Install dependencies: `pip install -r requirements-freeze.txt`
3. Run the app: `python -m streamlit run ekiden.py`

In Docker, simply run `./run_locally.sh`

## How to modify the causal model
The model code is stored in `causal_carbon_graph.py` and it consists of a list of nodes (the result of `causal_carbon_nodes()`), each of which has a set of metadata, including possibly a function to compute its value based on the upstream value of other nodes. Those functions have signatures like:
```
def compute_new_veh_t0(
    value: DataFrame,
    veh_mpg: DataFrame,
    veh_mpge: DataFrame,
    veh_battery_size: DataFrame,
) -> DataFrame:
```

The Ekiden backend will figure out which nodes to grab the upstream data from using the variable names in the signature. So in the above case, the backend will know that the node that is associated with this function is connected to the `veh_mpg`, `veh_mpge`, and `veh_battery_size` nodes from the function signature. That's how the system knows how to draw connections between the nodes in the graph. In order to add new nodes, define a new node in the list output of `causal_carbon_nodes` and associate that node to others using the function signatures. Note that the system will alert if the graph is no longer a DAG.
