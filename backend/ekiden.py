import json
import networkx as nx
import numpy as np
import pandas as pd
import pandera as pa
from loguru import logger
from streamlit_bokeh3_events import streamlit_bokeh3_events
import streamlit as st
import streamlit_vertical_slider as svs
from datetime import datetime
import os

from typing import Any
import streamlit.components.v1 as components
from ekiden_graph import ScalarEkidenNode, EkidenNode, EkidenGraph, TensorEkidenNode
from causal_carbon_graph import causal_carbon_nodes
from bokeh.transform import factor_mark, factor_cmap
import sys
import streamlit.components.v1 as components
import streamlit_authenticator as stauth


import importlib
import global_vars
import initial_values
import yaml
from yaml.loader import SafeLoader

from bokeh.io import output_file, show
from bokeh.models import (
    BoxZoomTool,
    Circle,
    HoverTool,
    MultiLine,
    Plot,
    TableColumn,
    GraphRenderer,
    LabelSet,
    OpenHead,
    DataTable,
    ColumnDataSource,
    Arrow,
    Range1d,
    ResetTool,
    StaticLayoutProvider,
    CustomJS,
    Legend,
)
from bokeh.palettes import Spectral4
from bokeh.plotting import from_networkx, figure
from bokeh.embed import file_html
from bokeh.events import Tap

from utils import to_snake_case


def render_graph(_graph: EkidenGraph) -> Any:

    node_df = _graph.node_df
    edge_df = _graph.edge_df
    node_cds = ColumnDataSource(node_df)

    x_col = node_df["x"]
    y_col = node_df["y"]
    xs: list[list[int]] = [
        [],
    ] * len(edge_df.index)
    ys: list[list[int]] = [
        [],
    ] * len(edge_df.index)
    source_list = edge_df["source"].to_list()
    target_list = edge_df["target"].to_list()
    for i, (s, t) in enumerate(zip(source_list, target_list)):
        xs[i] = [x_col[s], x_col[t]]
        ys[i] = [y_col[s], y_col[t]]
    edge_df["xs"] = xs
    edge_df["ys"] = ys
    edge_cds = ColumnDataSource(edge_df)

    node_cds.selected.js_on_change(
        "indices",
        CustomJS(
            args=dict(source=node_cds),
            code="""
            document.dispatchEvent(
                new CustomEvent("TAP", {detail: {data: source.data.ekiden_id[source.selected.indices[0]]}})
            )
            """,
        ),
    )

    buffer_percent = 0.05
    x_range = [min(x_col), max(x_col)]
    x_diff = abs(x_range[1] - x_range[0])
    x_range[1] += x_diff * buffer_percent
    x_range[0] -= x_diff * buffer_percent

    y_range = [min(y_col), max(y_col)]
    y_diff = abs(y_range[1] - y_range[0])
    y_range[1] += y_diff * buffer_percent
    y_range[0] -= y_diff * buffer_percent


    plot_size = 700
    plot = figure(
        x_range=x_range,
        y_range=y_range,
        tools="tap,zoom_in,wheel_zoom,pan",
        width=plot_size,
        height=plot_size,
    )
    plot.grid.visible = False
    plot.axis.visible = False

    labels = LabelSet(
        x="x",
        y="y",
        text="ekiden_name",
        x_offset=5,
        y_offset=15,
        text_font_size="0.9em",
        source=node_cds,
    )
    plot.add_layout(labels)

    plot.add_tools(ResetTool())

    oh = OpenHead(line_alpha=0.3, size=10, line_width=2)
    for x, y in zip(xs, ys):
        coords = np.array(list(zip(x, y)))
        rescaled_coords = np.copy(coords)
        arrow_length = np.linalg.norm(coords[1] - coords[0])
        arrow_direction = (coords[1] - coords[0]) / arrow_length
        rescaled_coords[0] = rescaled_coords[0] + (arrow_direction * 15)
        rescaled_coords[1] = rescaled_coords[1] - (arrow_direction * 15)

        x_rescaled, y_rescaled = zip(*rescaled_coords)
        plot.add_layout(
            Arrow(
                end=oh,
                line_width=2,
                line_alpha=0.3,
                x_start=x_rescaled[0],
                y_start=y_rescaled[0],
                x_end=x_rescaled[1],
                y_end=y_rescaled[1],
            )
        )

    markers = ["hex", "circle"]
    colors = [Spectral4[0], Spectral4[1]]
    colors = [
        "#009900",
        "#9999ff",
        "#e0e0e0",
        "#ff3333",
    ]  # ["#99ff99", "#9999ff", "#e0e0e0", "#ff3333"]
    # MARKERS = ["hex", "circle_x", "triangle", "diamond", "asterisk", "square"]
    factors = node_df["node_type"].unique()
    factors_color = np.array(global_vars.NODE_TAGS)  # node_df["tag"].unique()
    color = factor_cmap("Overenskomst", colors, factors_color)

    glyph_renderer = plot.scatter(
        "x",
        "y",
        fill_alpha=1,
        size=30,
        fill_color=factor_cmap("tag", palette=colors, factors=factors_color),
        line_color=None,
        marker=factor_mark("node_type", markers=markers, factors=factors),
        source=node_cds,
    )

    # node_hover_tool.renderers = [glyph_renderer]
    return streamlit_bokeh3_events(
        bokeh_plot=plot,
        events="TAP",
        key="bar",
        refresh_on_update=False,
        debounce_time=0,
        override_height=plot_size,
    )


def run_simulation(graph: EkidenGraph, scenario: str) -> None:

    graph.initialize_scenario(scenario)
    networkx_graph = graph.networkx_graph
    node_df = graph.node_df
    
    max_steps = global_vars.N_YEARS +  global_vars.N_YEARS_TAIL# number of years after year 0
    for i in range(0, max_steps):
        logger.info(f"\n RUNNING STEP {i}")

        logger.info(f" RUNNING global_vars.YEAR: {global_vars.YEAR}")


        x1 = graph.get_node_by_name("current_veh_t1_used_market").history
        if (x1.shape[0] > 0) & (i <= max_steps - 1):  #
            # global_vars.YEAR increases at the end of the i  step
            x0 = graph.get_node_by_name(
                "current_veh_t0"
            ).history  # note that this node does not update history automatically because it has no parents
            x1_partial = x1.loc[
                (x1["year"] == global_vars.YEAR) & (x1["scenario"] == scenario)
            ].copy()

            # advence the year and age with 1
            x1_partial["year"] = global_vars.YEAR + 1
            # x1_partial["age"] += 1

            x0 = pd.concat([x0, x1_partial])

            graph.update_node_history("current_veh_t0", x0)

        for node_idx in graph.node_order():
            node = node_df.loc[node_idx]
            node_inputs = list(networkx_graph.predecessors(node_idx))
            if len(node_inputs) > 0:
                for n in node_inputs:
                    assert graph.get_node_by_id(n).name == node_df["ekiden_name"][n]
                param_names = [
                    to_snake_case(node_df["ekiden_name"][n]) for n in node_inputs
                ]

                param_values = [
                    graph.get_node_by_id(n).latest_value_for_scenario(scenario, i)
                    for n in node_inputs
                ]

                param_dict = {
                    "value": graph.get_node_by_id(node_idx).latest_value_for_scenario(
                        scenario, i
                    )
                } | {k: v for k, v in zip(param_names, param_values)}
                ekiden_node = [n for n in graph.nodes if n.id == node_idx][0]
                assert ekiden_node.function is not None
                # st.write(i, node, param_names, param_values, param_dict)

                try:
                    computed_value = ekiden_node.function(**param_dict)
                except pa.errors.SchemaErrors as e:
                    logger.info("ERROR 1 in schema")
                    logger.error(e.message)
                    raise e

                graph.update_node_value(node_idx, scenario, i, computed_value)


def render_node(node):
    f"Note: *{node.notes}*"
    if node.is_input_node() & (node.tag != "process"):
        f"Modify inputs for **{node.name}**"
    else:
        f"View node history for **{node.name}**"

    if isinstance(node, ScalarEkidenNode):
        if node.is_input_node() & (node.tag != "process"):

            if node.progress_value != None:
                radio_button = st.radio("Choose how to modify:", ["manual adjustement", "use default values", "use progress values"])
            else:
                radio_button = st.radio("radio choice", ["manual adjustement", "use default values"])

            values_by_year = node.forecast["value"].tolist() 
            cols = st.columns(len(values_by_year))


            if radio_button == "use progress values":
                for i, value in enumerate(values_by_year):
                            values_by_year = node.progress_value
            elif radio_button == "use default values":
                    for i, value in enumerate(values_by_year):
                                values_by_year = node.initial_value
            else:
                for i, value in enumerate(values_by_year):
                    with cols[i]:
                        values_by_year[i] = svs.vertical_slider(
                            key=f"{node.id}-{i}",
                            min_value=float(node.min_value),
                            max_value=float(node.max_value),
                            default_value=float(value),
                            step=1.0,
                        )






            node.update_forecast(values_by_year)

            st.line_chart(data=node.forecast, x="year", y="value")
        else:
            st.line_chart(data=node.history, x="year", y="value", color="scenario")
    else:
        if node.is_input_node() & (node.tag != "process"):
            if isinstance(node.progress_value , pd.DataFrame):
                radio_button = st.radio("Choose how to modify:", ["manual adjustement", "use default values", "use progress values"])
            else:
                radio_button = st.radio("Choose how to modify", ["manual adjustement", "use default values"])
            update_col, plot_col = st.columns(2)

            with update_col:
                if radio_button == "use progress values":
                    updated_value = node.progress_value
                elif radio_button == "use default values":
                        updated_value = node.initial_value
                else:
                    updated_value = st.data_editor(node.forecast, hide_index=True)

            with plot_col:
                data_cols = node.data_columns()
                if node.name == "current_veh_t0":
                    pass
                elif "survival" in data_cols:
                    st.line_chart(
                        data=node.forecast, x="age", y=data_cols[3], color="year"
                    )
                elif any(elem in data_cols for elem in ["age_vmt", "high_vmt"]):
                    st.line_chart(
                        data=node.forecast, x="age", y=data_cols[1], color="year"
                    )
                elif any(
                    elem in data_cols for elem in ["freq", "mpge", "mpg", "batt_kwh"]
                ): #and ("year" in data_cols)
                    st.line_chart(
                        data=node.forecast, x="year", y=data_cols[0], color="powertrain"
                    )

            if not updated_value.equals(node.forecast):
                node.update_forecast(updated_value)
                st.rerun()
        else:
            st.write(node.history)

def render_page() -> None:
    st.set_page_config(layout="wide")
    st.title("Carbon Sight Causal Modeling")

    with open('users_config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
    )

    try:
        authenticator.login()
    except Exception as e:
        st.error(e)

    if st.session_state.get('authentication_status') is False:
        st.error('Username/password is incorrect')
        return
    elif st.session_state.get('authentication_status') is None:
        st.warning('Please enter your username and password')
        return

    st.html(
        """
            <style>
                div[aria-label="dialog"]>button[aria-label="Close"] {
                    display: none;
                }
            </style>
        """
    )


    # Prepare Data
    if "graph" not in st.session_state:
        ekiden_graph = EkidenGraph(causal_carbon_nodes())
        st.session_state["graph"] = ekiden_graph
    else:
        ekiden_graph = st.session_state["graph"]

    default_scenario = global_vars.DEFAULT_SCENARIO
    if default_scenario not in ekiden_graph.run_scenarios:
        

        run_simulation(ekiden_graph, default_scenario)

    col1, col2 = st.columns(2)

    with col1:


        result_selection = render_graph(ekiden_graph)

    with col2:

        (
            about_tab,
            node_tab,
            setup_tab,
            results_cum_tab,
            results_year_tab,
        ) = st.tabs(
            [
                "About",
                "Node Details",
                "New Scenario",
                "Results: Cumulative",
                "Results: Year",  
            ]
        )

        with setup_tab:
            scenario = st.text_input("New Scenario Name")
            simulation_kickoff = st.button("Simulate Scenario")

        with node_tab:
            if result_selection and result_selection.get("TAP"):
                selected_node_idx = result_selection.get("TAP")["data"]
                render_node(ekiden_graph.get_node_by_id(selected_node_idx))
            else:
                st.markdown(
                   "- Click on a node in the graph to get started modifying model assumptions. **:blue[BLUE]** nodes represent variables associated mainly with technological changes and **:green[GREEN]** nodes represent variables associated mainly with behavioral factors. You can manually adjust the inputs, or you can use the preset default or progress values. **:gray[GRAY]** nodes represent processes and not intended to be directly manipulated."
                )
                st.write(
                    "- Click on New Scenario to enter new scenario name and to run a simulation."
                )
                st.write("- Inspect the outputs in the Results tabs.")


        with results_cum_tab:
            total_ghg = ekiden_graph.get_node_by_name("Total GHG")
            st.write("Cumulative GHG, Mt")
            df = ekiden_graph.get_node_by_name("Total GHG").history
            df["cumsum_value"] = df.groupby("scenario")["value"].transform(
                pd.Series.cumsum
            )
            df["cumsum_value"] = df["cumsum_value"] / (10**9)
            st.line_chart(data=df, x="year", y="cumsum_value", color="scenario")


            
            total_ghg = ekiden_graph.get_node_by_name("Total GHG")
            
            df = ekiden_graph.get_node_by_name("Total GHG").history
            df_grouped = df.groupby("scenario")["value"].sum().reset_index()
            df_grouped["value"] = df_grouped["value"] / (10**9)
            df_grouped["difference_default"] = df_grouped["value"] - df_grouped.loc[df_grouped["scenario"] == default_scenario, "value"].mean()
            df_grouped.loc[df_grouped["scenario"] == default_scenario, "difference_default"] = 0.00000001 # show something on the graph
            if (df_grouped["scenario"].nunique() > 1):
                st.write("Total GHG difference compared to default, Mt")
                st.bar_chart(df_grouped, x="scenario", color = "scenario", y="difference_default", stack=False)

            # st.divider()
            # st.write("cumulative VMT in billions")
            # df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history
            # df["vmtXn"] = df["vmt"] * df["n"]
            # df_grouped = df.groupby(["scenario", "year"])["vmtXn"].sum().reset_index()
            # df_grouped["cumsum_vmt"] = df_grouped.groupby("scenario")[
            #     "vmtXn"
            # ].transform(pd.Series.cumsum)
            # df_grouped["cumsum_vmt"] = df_grouped["cumsum_vmt"] / (10**9)
            # st.line_chart(data=df_grouped, x="year", y="cumsum_vmt", color="scenario")

            # st.divider()
            # st.write("use_ghg PHEVs")
            # df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history
            # df = df[(df["powertrain"] == "phev")]
            # df_grouped = df.groupby(["scenario", "year"])["use_ghg"].sum().reset_index()
            # st.line_chart(data=df_grouped, x="year", y="use_ghg", color="scenario")

            # st.divider()
            # st.write("ghg_mile_electric")
            # df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history
            # df = df[df["powertrain"] == "phev"]
            # df_grouped = df.groupby(["scenario", "year"])["ghg_mile_electric"].mean().reset_index()
            # st.line_chart(data=df_grouped, x="year", y="ghg_mile_electric", color="scenario")

            # st.divider()
            # st.write("production_ghg")
            # df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history
            # df = df[df["powertrain"] == "phev"]
            # df_grouped = df.groupby(["scenario", "year"])["production_ghg"].mean().reset_index()
            # st.line_chart(data=df_grouped, x="year", y="production_ghg", color="scenario")

            # st.divider()
            # st.write("disposal_cost")
            # df = ekiden_graph.get_node_by_name("disposed_veh_t1").history
            # df = df[df["powertrain"] == "phev"]
            # df_grouped = df.groupby(["scenario", "year"])["ghg_cost_x_n"].mean().reset_index()
            # st.line_chart(data=df_grouped, x="year", y="ghg_cost_x_n", color="scenario")



            # st.divider()
            # st.write("cumulative disposed vehicles, millions")
            # df = ekiden_graph.get_node_by_name("disposed_veh_t1").history
            # df_grouped = df.groupby(["scenario", "year"])["n"].sum().reset_index()
            # df_grouped["cumsum_n"] = df_grouped.groupby("scenario")["n"].transform(
            #     pd.Series.cumsum
            # )
            # df_grouped["cumsum_n"] = df_grouped["cumsum_n"] / (10**6)
            # st.line_chart(data=df_grouped, x="year", y="cumsum_n", color="scenario")

            # st.divider()
            # st.markdown("**Cumulative New Vehicles, millions**")
            # st.write("All")
            # df = ekiden_graph.get_node_by_name("inventory_update").history
            # df = df[df["age"] == 0]
            # df_grouped = df.groupby(["scenario", "year"])["n"].sum().reset_index()
            # df_grouped["cumsum_n"] = df_grouped.groupby("scenario")["n"].transform(
            #     pd.Series.cumsum
            # )
            # df_grouped["cumsum_n"] = df_grouped["cumsum_n"] / (10**6)
            # st.line_chart(data=df_grouped, x="year", y="cumsum_n", color="scenario")


            # df_grouped = df.groupby(["scenario", "year", "powertrain"])["n"].sum().reset_index()
            # df_grouped["cumsum_n"] = df_grouped.groupby(["scenario", "powertrain"])["n"].transform(
            #     pd.Series.cumsum
            # )
            # df_grouped["cumsum_n"] = df_grouped["cumsum_n"] / (10**6)
            # chart_data_c_new_cumsum  = df_grouped

            # c_new_cumsum = st.container()
            
            # col1_new_cumsum, col2_new_cumsum = c_new_cumsum.columns(2)
            # with col1_new_cumsum:
            #     st.write("BEVs")
            #     st.line_chart(data = chart_data_c_new_cumsum[chart_data_c_new_cumsum["powertrain"] == "bev"], x="year", y="cumsum_n", color="scenario")

            #     st.write("PHEVs")
            #     st.line_chart(data = chart_data_c_new_cumsum[chart_data_c_new_cumsum["powertrain"] == "phev"], x="year", y="cumsum_n", color="scenario")

            # with col2_new_cumsum:

            #     st.write("HEVs")
            #     st.line_chart(data = chart_data_c_new_cumsum[chart_data_c_new_cumsum["powertrain"] == "hev"], x="year", y="cumsum_n", color="scenario")

            #     st.write("ICEVs")
            #     st.line_chart(data = chart_data_c_new_cumsum[chart_data_c_new_cumsum["powertrain"] == "icev"], x="year", y="cumsum_n", color="scenario")



        with results_year_tab:
            st.markdown("**Total GHG per year, Mt**")
            st.write("All")
            total_ghg = ekiden_graph.get_node_by_name("Total GHG")
            df = total_ghg.history.copy()
            df["value"] = df["value"] / (10**9)
            st.line_chart(data=df, x="year", y="value", color="scenario")

            # st.divider()
            # st.markdown("**Use GHG per year, Mt**")
            # st.write("All")
            # df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history.copy()
            # df_grouped = df.groupby(["scenario", "year"])["use_ghg"].sum().reset_index()
            # df_grouped["use_ghg"] = df_grouped["use_ghg"] / (10**9)
            # st.line_chart(data=df_grouped, x="year", y="use_ghg", color="scenario")

            # st.divider()
            # st.markdown("**Production GHG per year, Mt**")
            # st.write("All")
            # df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history.copy()
            
            # df_grouped = (
            #     df.groupby(["scenario", "year"])["production_ghg"].sum().reset_index()
            # )
            # df_grouped["production_ghg"] = df_grouped["production_ghg"] / (10**9)
            # st.line_chart(
            #     data=df_grouped, x="year", y="production_ghg", color="scenario"
            # )

            # st.divider()
            # st.markdown("**VMT per year, Billions**")
            # st.write("All")
            # df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history.copy()
            # df["vmtXn"] = df["vmt"] * df["n"]
            # df_grouped = df.groupby(["scenario", "year"])["vmtXn"].sum().reset_index()
            # df_grouped["vmtXn"] = df_grouped["vmtXn"] / (10**9)
            # st.line_chart(data=df_grouped, x="year", y="vmtXn", color="scenario")

            # df_grouped = df.groupby(["scenario", "year", "powertrain"])["vmtXn"].sum().reset_index()
            # df_grouped["vmtXn"] = df_grouped["vmtXn"] / (10**9)

            # chart_data_c_vmt = df_grouped

            # c_vmt = st.container()

            # col1_vmt, col2_vmt = c_vmt.columns(2)
            # with col1_vmt:
            #     st.write("BEVs")
            #     st.line_chart(data = chart_data_c_vmt[chart_data_c_vmt["powertrain"] == "bev"], x="year", y="vmtXn", color="scenario")

            #     st.write("PHEVs")
            #     st.line_chart(data = chart_data_c_vmt[chart_data_c_vmt["powertrain"] == "phev"], x="year", y="vmtXn", color="scenario")

            # with col2_vmt:

            #     st.write("HEVs")
            #     st.line_chart(data = chart_data_c_vmt[chart_data_c_vmt["powertrain"] == "hev"], x="year", y="vmtXn", color="scenario")

            #     st.write("ICEVs")
            #     st.line_chart(data = chart_data_c_vmt[chart_data_c_vmt["powertrain"] == "icev"], x="year", y="vmtXn", color="scenario")




            # st.divider()
            # st.markdown("**Vehicles Current, Millions**")
            # st.write("All")
            # df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history.copy()
            # df_grouped = df.groupby(["scenario", "year"])["n"].sum().reset_index()
            # df_grouped["n"] = df_grouped["n"] / (10**6)
            # st.line_chart(data=df_grouped, x="year", y="n", color="scenario")

            # c_count = st.container()
            
            # df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history.copy()
            # df_grouped = df.groupby(['scenario', 'year','powertrain'])['n'].sum().reset_index()
            # df_grouped["n"] = df_grouped["n"] / (10**6)
            # chart_data_c_count = df_grouped
            
            # col1_count, col2_count = c_count.columns(2)
            # with col1_count:
            #     st.write("BEVs")
            #     st.line_chart(data = chart_data_c_count[chart_data_c_count["powertrain"] == "bev"], x="year", y="n", color="scenario")

            #     st.write("PHEVs")
            #     st.line_chart(data = chart_data_c_count[chart_data_c_count["powertrain"] == "phev"], x="year", y="n", color="scenario")

            # with col2_count:

            #     st.write("HEVs")
            #     st.line_chart(data = chart_data_c_count[chart_data_c_count["powertrain"] == "hev"], x="year", y="n", color="scenario")

            #     st.write("ICEVs")
            #     st.line_chart(data = chart_data_c_count[chart_data_c_count["powertrain"] == "icev"], x="year", y="n", color="scenario")

                



         
            # c_bucket = st.container()
            # c_bucket.markdown("**Proportion High VMT bucket counts**")

            # df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history.copy()
            # df["vmtXn"] = df["n"]*df["vmt"]
            # df_grouped = df.groupby(['scenario', 'year', 'vmt_bucket', 'powertrain'])[['n', 'vmtXn', 'vmt']].sum().reset_index()
            # #df_grouped["n"] = df_grouped["n"] / (10**6)
            # #df_grouped["n"] = df_grouped['vmtXn']
            
            # pivoted_df = df_grouped.pivot_table(index=['scenario', 'year','powertrain'], columns='vmt_bucket', values='n').reset_index()
            # pivoted_df["high_vs_low"] = pivoted_df["high"]/(pivoted_df["low"]+pivoted_df["high"])

            # chart_data_c_bucket = pivoted_df
            
            # col1_buckets, col2_buckets = c_bucket.columns(2)
            # with col1_buckets:
                
            #     st.write("BEVs")
            #     st.line_chart(data = chart_data_c_bucket[chart_data_c_bucket["powertrain"] == "bev"], x="year", y="high_vs_low", color="scenario")

            #     st.write("PHEVs")
            #     st.line_chart(data = chart_data_c_bucket[chart_data_c_bucket["powertrain"] == "phev"], x="year", y="high_vs_low", color="scenario")

            # with col2_buckets:

            #     st.write("HEVs")
            #     st.line_chart(data = chart_data_c_bucket[chart_data_c_bucket["powertrain"] == "hev"], x="year", y="high_vs_low", color="scenario")

            #     st.write("ICEVs")
            #     st.line_chart(data = chart_data_c_bucket[chart_data_c_bucket["powertrain"] == "icev"], x="year", y="high_vs_low", color="scenario")

            # c_bucket_x = st.container()
            # c_bucket_x .markdown("**Prportion High VMT bucket VMT**")

            # df_grouped['x'] = df_grouped['vmtXn']

            # pivoted_df = df_grouped.pivot_table(index=['scenario', 'year','powertrain'], columns='vmt_bucket', values='x').reset_index()
            # pivoted_df["high_vs_low"] = pivoted_df["high"] - pivoted_df["low"]

            # chart_data_c_bucket_x = pivoted_df
            
            # col1_buckets_x , col2_buckets_x = c_bucket_x.columns(2)
            # with col1_buckets_x :
                
            #     st.write("BEVs")
            #     st.line_chart(data = chart_data_c_bucket_x[chart_data_c_bucket_x["powertrain"] == "bev"], x="year", y="high_vs_low", color="scenario")

            #     st.write("PHEVs")
            #     st.line_chart(data = chart_data_c_bucket_x[chart_data_c_bucket_x["powertrain"] == "phev"], x="year", y="high_vs_low", color="scenario")

            # with col2_buckets_x :

            #     st.write("HEVs")
            #     st.line_chart(data = chart_data_c_bucket_x[chart_data_c_bucket_x["powertrain"] == "hev"], x="year", y="high_vs_low", color="scenario")

            #     st.write("ICEVs")
            #     st.line_chart(data = chart_data_c_bucket_x[chart_data_c_bucket_x["powertrain"] == "icev"], x="year", y="high_vs_low", color="scenario")

             


            # st.divider()
            # st.write("vehicles disposed, millions")
            # df = ekiden_graph.get_node_by_name("disposed_veh_t1").history
            # df_grouped = df.groupby(["scenario", "year"])["n"].sum().reset_index()
            # df_grouped["n"] = df_grouped["n"] / (10**6)
            # st.line_chart(data=df_grouped, x="year", y="n", color="scenario")



            # st.divider()
            # st.markdown("**New Vehicles, millions**")
            # st.write("All")
            # df = ekiden_graph.get_node_by_name("inventory_update").history
            # df = df[df["age"] == 0]
            # df_grouped = df.groupby(["scenario", "year"])["n"].sum().reset_index()
            # df_grouped["n"] = df_grouped["n"] / (10**6)
            # st.line_chart(data=df_grouped, x="year", y="n", color="scenario")

            # df_grouped = df.groupby(["scenario", "year", "powertrain"])["n"].sum().reset_index()
            # df_grouped["n"] = df_grouped["n"] / (10**6)
            # chart_data_c_new  = df_grouped

            # c_new= st.container()
            
            # col1_new, col2_new = c_new.columns(2)
            # with col1_new:
            #     st.write("BEVs")
            #     st.line_chart(data = chart_data_c_new[chart_data_c_new["powertrain"] == "bev"], x="year", y="n", color="scenario")

            #     st.write("PHEVs")
            #     st.line_chart(data = chart_data_c_new[chart_data_c_new["powertrain"] == "phev"], x="year", y="n", color="scenario")

            # with col2_new:

            #     st.write("HEVs")
            #     st.line_chart(data = chart_data_c_new[chart_data_c_new["powertrain"] == "hev"], x="year", y="n", color="scenario")

            #     st.write("ICEVs")
            #     st.line_chart(data = chart_data_c_new[chart_data_c_new["powertrain"] == "icev"], x="year", y="n", color="scenario")









            # st.divider()
            # st.write("disposed mean age")
            # df = ekiden_graph.get_node_by_name("disposed_veh_t1").history
            # # df = df.loc[df["powertrain"] == "phev"]
            # df["age_x_n"] = df["age"] * df["n"]
            # df_grouped = (
            #     df.groupby(["year", "scenario"])[["n", "age_x_n"]].sum().reset_index()
            # )
            # df_grouped["mean_age"] = df_grouped["age_x_n"] / df_grouped["n"]
            # st.line_chart(data=df_grouped, x="year", y="mean_age", color="scenario")

            # st.divider()
            # st.write("current mean age")
            # df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history.copy()
            # # df = df.loc[df["powertrain"] == "phev"]
            # df["age_x_n"] = df["age"] * df["n"]
            # df_grouped = (
            #     df.groupby(["year", "scenario"])[["n", "age_x_n"]].sum().reset_index()
            # )
            # df_grouped["mean_age"] = df_grouped["age_x_n"] / df_grouped["n"]
            # st.line_chart(data=df_grouped, x="year", y="mean_age", color="scenario")
        
        with about_tab:
            st.markdown(
                   "**Purpose**: The primary use of Carbon Sight Causal Modeling is for research and development of counterfactual simulations in the domain of LDV decarbonization. The intended users are researchers interested in climate change, including public policy researchers, transportation researchers, causal modelers, climate change mitigation strategists as well as behavioral and social scientists. The source code is available at (url TBA). For more information see the linked paper (url TBA). \n\n  **Licensing**: Carbon Sight Causal Modeling is released under an MIT License. Copyright (c) 2025 Toyota Research Institute, Inc. Toyota did not provide any of the materials used to build the model. The model here is for reference and verification of the procedures described in the paper. See the paper for more details. The model is provided as-is. Toyota Research Institute disclaims all warranties, expressed or implied, including any warranty of merchantability and fitness for a particular purpose.")

#         with resusts_veh_tab:
            

#             df = ekiden_graph.get_node_by_name(
#                 "current_veh_t1_used_market"
#             ).history.copy()
#             # df = df.loc[df["production_year"].between(2027,2027, inclusive="both")]
#             df_grouped_all = (
#                 df.groupby(["year", "scenario"])[["n", "use_ghg", "production_ghg"]]
#                 .sum()
#                 .reset_index()
#             )
#             df_grouped_all["use_ghg"] = df_grouped_all["use_ghg"] / df_grouped_all["n"]
#             df_grouped["production_ghg"] = (
#                 df_grouped_all["production_ghg"] / df_grouped_all["n"]
#             )
#             st.markdown("**Use GHG per Vehicle per Year**")
#             st.write("All")
#             st.line_chart(data=df_grouped_all, x="year", y="use_ghg", color="scenario")


#             df_grouped = (
#                 df.groupby(["year", "scenario", "powertrain"])[["n", "use_ghg", "production_ghg"]]
#                 .sum()
#                 .reset_index()
#             )
#             df_grouped["use_ghg"] = df_grouped["use_ghg"] / df_grouped["n"]
#             df_grouped["production_ghg"] = (
#                 df_grouped["production_ghg"] / df_grouped["n"]
#             )

#             chart_data_c_ghg_vehicle  = df_grouped
                        
#             c_use_ghg_vehicle = st.container()
            
#             col1_use_ghg_vehicle , col2_use_ghg_vehicle  = c_use_ghg_vehicle.columns(2)
#             with col1_use_ghg_vehicle:
#                 st.write("BEVs")
#                 st.line_chart(data = chart_data_c_ghg_vehicle[chart_data_c_ghg_vehicle["powertrain"] == "bev"], x="year", y="use_ghg", color="scenario")

#                 st.write("PHEVs")
#                 st.line_chart(data = chart_data_c_ghg_vehicle[chart_data_c_ghg_vehicle["powertrain"] == "phev"], x="year", y="use_ghg", color="scenario")

#             with col2_use_ghg_vehicle:

#                 st.write("HEVs")
#                 st.line_chart(data = chart_data_c_ghg_vehicle[chart_data_c_ghg_vehicle["powertrain"] == "hev"], x="year", y="use_ghg", color="scenario")

#                 st.write("ICEVs")
#                 st.line_chart(data = chart_data_c_ghg_vehicle[chart_data_c_ghg_vehicle["powertrain"] == "icev"], x="year", y="use_ghg", color="scenario")

#             st.divider()
#             st.markdown("**VMT per vehicle per year**")
#             st.write("All")
#             df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history.copy()
#             df["vmtXn"] = df["vmt"] * df["n"]
#             df_grouped = df.groupby(["scenario", "year"])[["vmtXn", "n"]].sum().reset_index()
            
#             df_grouped["vmt"] = df_grouped["vmtXn"]/df_grouped["n"]
#             st.line_chart(data=df_grouped, x="year", y="vmt", color="scenario")

#             df_grouped = df.groupby(["scenario", "year", "powertrain"])[["vmtXn", "n"]].sum().reset_index()
#             df_grouped["vmt"] = df_grouped["vmtXn"]/df_grouped["n"]
    


#             chart_data_c_vmt_veh = df_grouped

#             c_vmt_veh = st.container()

#             col1_vmt_veh, col2_vmt_veh = c_vmt_veh.columns(2)
#             with col1_vmt_veh:

#                 st.write("BEVs")
#                 st.line_chart(data = chart_data_c_vmt_veh[chart_data_c_vmt_veh["powertrain"] == "bev"], x="year", y="vmt", color="scenario")

#                 st.write("PHEVs")
#                 st.line_chart(data = chart_data_c_vmt_veh[chart_data_c_vmt_veh["powertrain"] == "phev"], x="year", y="vmt", color="scenario")

#             with col2_vmt_veh:

#                 st.write("HEVs")
#                 st.line_chart(data = chart_data_c_vmt_veh[chart_data_c_vmt_veh["powertrain"] == "hev"], x="year", y="vmt", color="scenario")

#                 st.write("ICEVs")
#                 st.line_chart(data = chart_data_c_vmt_veh[chart_data_c_vmt_veh["powertrain"] == "icev"], x="year", y="vmt", color="scenario")


# ###########




#             st.write("UF: PHEV")
#             df = ekiden_graph.get_node_by_name(
#                 "current_veh_t1_used_market"
#             ).history.copy()
#             df = df[df["powertrain"] == "phev"]
#             df_grouped = (
#                 df.groupby(["year", "scenario"])[
#                     [
#                         "uf_real",
#                         "uf_from_range",
#                         "ev_range",
#                         "ev_range_estim",
#                         "batt_kwh",
#                         "mpge",
#                     ]
#                 ]
#                 .mean()
#                 .reset_index()
#             )
#             st.line_chart(
#                 data=df_grouped, x="year", y="uf_from_range", color="scenario"
#             )
#             st.line_chart(data=df_grouped, x="year", y="uf_real", color="scenario")
#             st.line_chart(data=df_grouped, x="year", y="ev_range", color="scenario")
#             st.line_chart(
#                 data=df_grouped, x="year", y="ev_range_estim", color="scenario"
#             )
#             st.line_chart(data=df_grouped, x="year", y="batt_kwh", color="scenario")
#             st.line_chart(data=df_grouped, x="year", y="mpge", color="scenario")

#             st.divider()
#             st.write("VMT per vehicle")
#             df = ekiden_graph.get_node_by_name("current_veh_t1_used_market").history.copy()
#             df["vmtXn"] = df["vmt"] * df["n"]
#             df_grouped = (
#                 df.groupby(["scenario", "year"])[["vmtXn", "n"]].sum().reset_index()
#             )
#             df_grouped["vmt_per_vehicle"] = df_grouped["vmtXn"] / df_grouped["n"]
#             st.line_chart(
#                 data=df_grouped, x="year", y="vmt_per_vehicle", color="scenario"
#             )
#             st.line_chart(
#                 data=df_grouped, x="year", y="vmt_per_vehicle", color="scenario"
#             )

    if simulation_kickoff:
        
        run_simulation(ekiden_graph, scenario)
        st.rerun()
    



    if global_vars.RUN_MULTIPLE:
        counter = 1
        startTime_global = datetime.now()
        # node.set_initial_value(updated_value)
        for scenario_x in global_vars.RUN_MULTIPLE_SCENARIO_CONTENT.keys():
            startTime_local = datetime.now()
            st.write(f"{counter}: Running scenario: {scenario_x}")
            counter += 1
            node_updates = global_vars.RUN_MULTIPLE_SCENARIO_CONTENT[scenario_x]
            for node_to_update in node_updates:
                startTime_node = datetime.now()

                updated_value = global_vars.RUN_MULTIPLE_SCENARIO_CONTENT[scenario_x][
                    node_to_update
                ]
                n = ekiden_graph.get_node_by_name(node_to_update)
                n_years = global_vars.N_YEARS + global_vars.N_YEARS_TAIL

                
                # during the tail years, we are skipping the updates, using the defaults
                # caution, this code for adding tail years is almost duplicated in ekidep_graph; future iterations should have this as a function

                if isinstance(updated_value, pd.DataFrame):
                    if (global_vars.N_YEARS_TAIL > 0):
                        if "year" not in updated_value.columns:
                            logger.info("HERE1")
                            n_rows_in_year = updated_value.shape[0]
                            updated_value = pd.concat([updated_value, pd.concat([updated_value]*(n_years-1))])
                            updated_value["year"] = np.repeat(np.arange(n_years), n_rows_in_year)
                        else:
                            n_rows_in_year = int(updated_value.shape[0]/global_vars.N_YEARS)
                            updated_value = updated_value.sort_values(by = "year")
                            updated_value = pd.concat([updated_value, pd.concat([updated_value[-n_rows_in_year:]]*global_vars.N_YEARS_TAIL)])
                            updated_value["year"] = np.repeat(np.arange(n_years), n_rows_in_year)
            
                    if "year" not in updated_value.columns:
                        self._forecast = pd.concat(
                            [updated_value.assign(year=y) for y in range(n_years)], ignore_index=True
                        )
                    else: # some data frame inputs might have year information already
                        if set(updated_value["year"]) != set(range(n_years)):
                            logger.info(f"WARNING, number of years in an input dataframe is not in the expected range:\n {node_to_update}  \n {set(updated_value["year"])} \n{set(range(n_years))} \n {updated_value}")
                        else:
                            new_forecast = updated_value


                            ###
                elif isinstance(updated_value, list):
                    # add a repetition here
                    if (len(updated_value) == global_vars.N_YEARS) & (global_vars.N_YEARS_TAIL > 0):
                        logger.info(updated_value)
                        logger.info([updated_value[-1]]*global_vars.N_YEARS_TAIL)
                        #logger.info(value[-1]*global_vars.N_YEARS_TAIL)
                        updated_value = updated_value + [updated_value[-1]]*global_vars.N_YEARS_TAIL

                    if len(updated_value) != n_years: 
                        logger.info(f'ERROR: length of entry list for variable {node_to_update} does not match the number of years')
                    df = pd.DataFrame({"value": updated_value, "year": list(range(n_years))})
                    new_forecast = df






                #####
                #     if not "year" in updated_value.columns:
                #         new_forecast = pd.concat(
                #             [updated_value.assign(year=y) for y in range(n_years)],
                #             ignore_index=True,
                #         )
                #     else:
                #         new_forecast = updated_value
                # elif isinstance(updated_value, list):
                #     if len(updated_value) != n_years:
                #         logger.info(
                #             f"ERROR: length of entry list for variable {node_to_update} does not match the number of years"
                #         )
                #     new_forecast = pd.DataFrame(
                #         {"value": updated_value, "year": list(range(n_years))}
                #     )
                #####


                elif isinstance(updated_value, float) | isinstance(updated_value, int):
                    new_forecast = pd.DataFrame(
                        zip(
                            list(range(n_years)),
                            [
                                updated_value,
                            ]
                            * n_years,
                        ),
                        columns=["year", "value"],
                    )
                else:
                    new_forecast = None
                n._forecast = new_forecast

            run_simulation(ekiden_graph, scenario_x)

            for name_i in ekiden_graph.node_df["ekiden_name"]:
                df_out = ekiden_graph.get_node_by_name(name_i).history
                folder_path = "multiple_scenarios/outputs/default_progress/" + scenario_x + "/"
                folder_path = folder_path.replace("=progress", "=p")
                folder_path = folder_path.replace("=default", "=d")
                os.makedirs(folder_path, exist_ok=True)
                file_name = name_i + "_out.csv"
                df_out.to_csv(
                    folder_path + file_name, index=False
                )

                a = ekiden_graph.get_node_by_name(name_i).clear_history # a here just caputres the output, otherwise it prints None in the browser


           
            st.write(f"local time passed: {datetime.now() - startTime_local}")
            st.write(f"global time passed: {datetime.now() - startTime_global}")

    return ekiden_graph

render_page()
