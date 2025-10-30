import inspect
import networkx as nx
import numpy as np
import pandas as pd
import pint
import pydot

from loguru import logger

from enum import Enum

from abc import abstractmethod

from utils import to_snake_case

from collections.abc import Callable

import pandera as pa

from pandera import DataFrameModel

GLOBAL_NODE_ID = 0

import global_vars

NodeType = Enum("NodeType", ["Scalar", "Tensor"])

NodeTag = Enum("NodeTag", global_vars.NODE_TAGS)

EkidenCallback = Callable[..., float | pd.DataFrame] | None

DEFAULT_SCENARIO = global_vars.DEFAULT_SCENARIO


class EkidenNode: 
    _id: int
    notes: str
    tag: str
    name: str
    function: EkidenCallback
    adjacency: list[int]
    _history: pd.DataFrame
    _initial_value: pd.DataFrame | float
    _progress_value: pd.DataFrame | float
    _current_value: pd.DataFrame | float
    _forecast: pd.DataFrame

    @abstractmethod
    def __init__(
        self, name: str, function: EkidenCallback, value: float | pd.DataFrame, progress_value: float | pd.DataFrame, tag:str, notes:str
    ):
        global GLOBAL_NODE_ID
        self._id = GLOBAL_NODE_ID
        GLOBAL_NODE_ID += 1
        self.name = name
        self.tag = tag
        self.notes = notes


        self.function = function
        self.adjacency = []
        self._history = pd.DataFrame(columns=["scenario", "year"])
        self._initial_value = value
        self._progress_value = progress_value
        n_years = global_vars.N_YEARS + global_vars.N_YEARS_TAIL
        if isinstance(value, pd.DataFrame):
            if (global_vars.N_YEARS_TAIL > 0):
                if "year" not in value.columns:
                    #logger.info("HERE1")
                    n_rows_in_year = value.shape[0]
                    value = pd.concat([value, pd.concat([value]*(n_years-1))])
                    value["year"] = np.repeat(np.arange(n_years), n_rows_in_year)
                else:
                    n_rows_in_year = int(value.shape[0]/global_vars.N_YEARS)
                    value = value.sort_values(by = "year")
                    value = pd.concat([value, pd.concat([value[-n_rows_in_year:]]*global_vars.N_YEARS_TAIL)])
                    value["year"] = np.repeat(np.arange(n_years), n_rows_in_year)
       
            if "year" not in value.columns:
                self._forecast = pd.concat(
                    [value.assign(year=y) for y in range(n_years)], ignore_index=True
                )
            else: # some data frame inputs might have year information already
                if set(value["year"]) != set(range(n_years)):
                    logger.info(f"WARNING, number of years in an input dataframe is not in the expected range:\n {name}  \n {set(value["year"])} \n{set(range(n_years))} \n {value}")
                else:
                    self._forecast = value

        elif isinstance(value, list):
            # add a repetition here
            if (len(value) == global_vars.N_YEARS) & (global_vars.N_YEARS_TAIL > 0):
                # logger.info(value)
                # logger.info([value[-1]]*global_vars.N_YEARS_TAIL)
                #logger.info(value[-1]*global_vars.N_YEARS_TAIL)
                value = value + [value[-1]]*global_vars.N_YEARS_TAIL

            if len(value) != n_years: 
                logger.info(f'ERROR: length of entry list for variable {self.name} does not match the number of years')
            df = pd.DataFrame({"value": value, "year": list(range(n_years))})
            self._forecast = df
        elif (isinstance(value, float) | isinstance(value, int)):
            self._forecast = pd.DataFrame(
                zip(list(range(n_years)),[value,]* n_years,),
                columns=["year", "value"],
            )
        else:
            self._forecast = None
        

    @abstractmethod
    def node_type(self) -> NodeType:
        pass


    def node_tag(self) -> NodeTag:
        return self.tag


    def node_notes(self) -> str:
        return self.notes



    # @property
    # def notes(self) -> str:
    #     return self._notes
    
    # @property
    # def tag(self) -> str:
    #     return self._tag

    @property
    def id(self) -> int:
        return self._id

    @property
    def history(self) -> pd.DataFrame:
        return self._history
    
    @property
    def clear_history(self) -> None:
        self._history = pd.DataFrame(columns=["scenario", "year"])
        return(None)


    @property
    def initial_value(self) -> pd.DataFrame | float:
        return self._initial_value
    
    @property
    def progress_value(self) -> pd.DataFrame | float:
        return self._progress_value

    def set_initial_value(self, value: float | pd.DataFrame) -> None:
       self._initial_value = value # it seems this is not being used

    def get_df_for_scenario(self, scenario: str) -> pd.DataFrame:
        # todo: this is terrible hack, but I cannot pass values across time steps otherwise
        if self.name == "current_veh_t0":
            return self.history.loc[self.history["scenario"] == scenario]
        if self.is_input_node():
            return self.forecast
        else:
           return self.history.loc[self.history["scenario"] == scenario]

    def append_to_scenario(
        self, scenario: str, year: int, value: float | pd.DataFrame
    ) -> None:
        global_vars.YEAR = year
        global_vars.CALENDAR_YEAR = year + global_vars.START_YEAR

        if isinstance(value, pd.DataFrame):
            scenario_value = value.copy()
            scenario_value["scenario"] = [
                scenario,
            ] * len(scenario_value)
            scenario_value["year"] = [
                year,
            ] * len(scenario_value)
            self._history = pd.concat(
                [self.history, scenario_value],
                # ignore_index=True
            )
        elif isinstance(value, (int, float)):
            self._history = pd.concat(
                [
                    self.history,
                    pd.DataFrame(
                        [{"scenario": scenario, "year": year, "value": value}]
                    ),
                ],
                # ignore_index=True,
            )

    def associate_directed_edge_to(self, other_node: "EkidenNode") -> None:
        if other_node.id not in self.adjacency:
            self.adjacency.append(other_node.id)

    def latest_value_for_scenario(
        self, scenario: str, year: int
    ) -> pd.DataFrame | float:
        scenario_df = self.get_df_for_scenario(scenario)
        if self.is_input_node():
            latest_values = scenario_df[scenario_df["year"] == year]
        else:
            latest_values = scenario_df[
                scenario_df["year"] == scenario_df["year"].max()
            ]

        if "value" in latest_values.columns and len(latest_values) == 1:
            return latest_values["value"].iloc[0]
        else:
            return latest_values

    def is_input_node(self) -> bool:
        return self.function is None

    @property
    def forecast(self) -> pd.DataFrame:
        return self._forecast


class ScalarEkidenNode(EkidenNode):
    min_value: float
    max_value: float

    def __init__(
        self,
        name: str,
        function: EkidenCallback,
        value: float,
        progress_value: float,
        min_value: float,
        max_value: float,
        tag: str,
        notes: str,
    ):
        EkidenNode.__init__(self, name, function, value, progress_value, tag, notes)
        self.min_value = min_value
        self.max_value = max_value
        self._dtypes = None

    def update_forecast(self, updated_forecast_values: list[float]):
         self._forecast["value"] = updated_forecast_values

    def node_type(self) -> NodeType:
        return NodeType.Scalar

    def cumulative_value_for_scenario(self, scenario: str) -> float:
        return np.sum(self.get_df_for_scenario(scenario)["value"])


class TensorEkidenNode(EkidenNode):
    _schema: pa.DataFrameModel

    

    def __init__(
        self,
        name: str,
        function: EkidenCallback,
        value: pd.DataFrame,
        progress_value: pd.DataFrame,
        tag: str,
        notes: str,
    ):
        EkidenNode.__init__(self, name, function, value, progress_value, tag, notes)

        
    def node_type(self) -> NodeType:
        return NodeType.Tensor

    def update_forecast(self, updated_forecast_values: pd.DataFrame):
        self._forecast = updated_forecast_values

    def data_columns(self):
        numeric_cols = self.history.select_dtypes(include="number").columns.to_list()
        return [c for c in numeric_cols if c not in ["year"]]

    def powertrains(self):
        if "powertrain" in self.history.columns:
            return self.history["powertrain"].unique()
        else:
            return []


class EkidenGraph:
    _networkx_graph: nx.DiGraph
    _node_df: pd.DataFrame
    _edge_df: pd.DataFrame
    _nodes: list[EkidenNode]
    _year: int

    def __init__(self, nodes: list[EkidenNode]):
        self._nodes = nodes
        self._networkx_graph = self.graph_from_nodes()
        self.df_from_graph()
        self._edge_df = nx.to_pandas_edgelist(self._networkx_graph)

    def initialize_scenario(self, scenario: str) -> None:
        for n in self._nodes:
            n.append_to_scenario(scenario, 0, n.initial_value)

    @property
    def run_scenarios(self) -> list[str]:
        return list(
            set(sum([n.history["scenario"].unique().tolist() for n in self._nodes], []))
        )

    @property
    def node_df(self) -> pd.DataFrame:
        return self._node_df

    @property
    def edge_df(self) -> pd.DataFrame:
        return self._edge_df

    @property
    def networkx_graph(self) -> nx.DiGraph:
        return self._networkx_graph

    @property
    def nodes(self) -> list[EkidenNode]:
        return self._nodes

    def node_order(self) -> list[int]:
        return list(nx.topological_sort(self.networkx_graph))

    def get_node_by_id(self, _id: int) -> EkidenNode:
        try:
            return next(n for n in self.nodes if n.id == _id)
        except Exception as e:
            raise ValueError(
                f"Encountered error while searching in id list {[n.id for n in self.nodes]} for id {_id}"
            )

    def get_node_by_name(self, name: str) -> EkidenNode:
        try:
            return next(n for n in self.nodes if n.name == name)
        except Exception as e:
            raise ValueError(
                f"Encountered error while searching in name list {[n.name for n in self.nodes]} for name {name}"
            )

    def update_node_value(
        self, _id: int, scenario: str, year: int, value: float | pd.DataFrame
    ) -> None:
        self.get_node_by_id(_id).append_to_scenario(scenario, year, value)

    def update_node_history(self, node_name: str, new_history) -> None:
        self.get_node_by_name(node_name)._history = new_history
        a = self.get_node_by_name(node_name).history

    def graph_from_nodes(self) -> nx.DiGraph:
        adjacency_dict: dict[int, list[int]] = {}
        for node in self.nodes:
            if node.function is not None:
                signature = inspect.signature(node.function)
                for argument in signature.parameters.keys():
                    if argument == "value":
                        continue
                    try:
                        matching_node = next(
                            n for n in self.nodes if to_snake_case(n.name) == argument
                        )
                    except StopIteration:
                        raise ValueError(
                            f"Could not find matching node for argument {argument} among names: {[to_snake_case(n.name) for n in self.nodes]}"
                        )

                    if node.id not in adjacency_dict:
                        adjacency_dict[node.id] = []
                    adjacency_dict[node.id].append(matching_node.id)

        # NOTE: directionlity of graph must be reversed because for each edge, source is input, not output
        networkx_graph = nx.from_dict_of_lists(
            adjacency_dict, create_using=nx.DiGraph()
        ).reverse()

        for attr, networkx_attr in {
            "name": "ekiden_name",
            "_id": "ekiden_id",
        }.items():
            nx.set_node_attributes(
                networkx_graph,
                {node.id: getattr(node, attr) for node in self.nodes},
                networkx_attr,
            )
        return networkx_graph

    def df_from_graph(self, layout_algorithm: str = "sfdp") -> pd.DataFrame:
        reversed_graph = self.networkx_graph.reverse(copy=True)
        total_ghg = self.get_node_by_name("Total GHG")
        graph_layout = nx.nx_pydot.graphviz_layout(
            self.networkx_graph,
            prog=layout_algorithm,
            root=total_ghg.id,
        )

        node_df = (
            pd.DataFrame.from_dict(
                dict(self.networkx_graph.nodes(data=True)), orient="index"
            )
            .set_index("ekiden_id")
            .sort_index()
        )

        node_df["x"] = [graph_layout[i][0] for i in node_df.index]
        node_df["y"] = [graph_layout[i][1] for i in node_df.index]
        node_df["node_type"] = [
            str(self.get_node_by_id(i).node_type()) for i in node_df.index
        ]
        node_df["tag"] = [
            str(self.get_node_by_id(i).node_tag()) for i in node_df.index
        ]
        node_df["notes"] = [
            str(self.get_node_by_id(i).node_notes()) for i in node_df.index
        ]
        self._node_df = node_df
        return node_df
