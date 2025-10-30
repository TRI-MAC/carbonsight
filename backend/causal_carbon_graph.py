
import numpy as np
import os
import pickle

from scipy import optimize
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

import itertools

from enum import Enum

from loguru import logger

from ekiden_graph import EkidenGraph
from ekiden_graph import EkidenNode
from ekiden_graph import ScalarEkidenNode
from ekiden_graph import TensorEkidenNode

import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
pd.set_option('future.no_silent_downcasting', True)

import pandera as pa

from pandera import DataFrameModel
from pandera import Field
from pandera.typing import DataFrame
from pandera.typing import Series


import global_vars
import initial_values

from functools import reduce

##### constants

###### Utililty Functions ######
def get_uf_from_ev_range(x: float) -> float:
    coef_list = [10.52, -7.28, -26.37, 79.08, -77.36, 26.07, 0, 0, 0, 0]
    norm_dist = 400
    return 1 - np.exp(
        -(
            coef_list[0] * np.power(x / norm_dist, 1)
            + coef_list[1] * np.power(x / norm_dist, 2)
            + coef_list[2] * np.power(x / norm_dist, 3)
            + coef_list[3] * np.power(x / norm_dist, 4)
            + coef_list[4] * np.power(x / norm_dist, 5)
            + coef_list[5] * np.power(x / norm_dist, 6)
            + coef_list[6] * np.power(x / norm_dist, 7)
            + coef_list[7] * np.power(x / norm_dist, 8)
            + coef_list[8] * np.power(x / norm_dist, 9)
            + coef_list[9] * np.power(x / norm_dist, 10)
        )
    )


def get_ev_range_from_batt_kwh(batt_kwh, mpge, powertrain):
    if powertrain == "phev":
        result = -14.21 + 1.346 * batt_kwh + 0.3205 * mpge + 0.0003 * batt_kwh * mpge
    elif powertrain == "bev":
        result = (
            13.518727
            + 0.047706 * batt_kwh
            + 0.291313 * mpge
            + 0.025649 * batt_kwh * mpge
        )
    else:
        result = None
    return result

def update_value_from_LR(input_values, trained_model):
    # the linear regression assumes all interactions and the slope are included in the trained model
    poly = PolynomialFeatures(interaction_only=True,include_bias = False)
    X_hat = poly.fit_transform(np.array(input_values).reshape(1, -1))
    output_value = trained_model.predict(X_hat).item()
    return(output_value)

# filename = 'data/models/veh_EV_range_model_evs.pkl'
# with open(filename, 'rb') as pickleFile:
#     veh_EV_range_model_evs = pickle.load(pickleFile)
# filename = 'data/models/veh_EV_range_model_phevs.pkl'
# with open(filename, 'rb') as pickleFile:
#     veh_EV_range_model_phevs = pickle.load(pickleFile)



# def get_ev_range_from_batt_kwh1(batt_kwh, mpge, powertrain, models = {
#     "bev":veh_EV_range_model_evs, "phev":veh_EV_range_model_phevs}):
#     if((not np.isnan(batt_kwh)) & (not np.isnan(mpge)) & (powertrain in ["bev", "phev"])):
#          result = update_value_from_LR([batt_kwh,mpge], models[powertrain])
#     else:
#         result = None
#     return result






def reshuffle_used(current_veh_t1_use, reshufle_prob = 0.15):
    #reshuffles vehicles between buckets to simulate natural change of ownership
    #used car market is ~15% of vehicles
    
    ages = np.unique(current_veh_t1_use["age"])

    current_veh_t1_use["reshuffled_n"] = current_veh_t1_use["n"]
    for age in ages:
        for powertrain in global_vars.POWERTRAIN_LIST:
                for vmt_bucket in ["low", "high"]:
                    n_low = current_veh_t1_use.loc[(current_veh_t1_use["powertrain"] == powertrain) & (current_veh_t1_use["vmt_bucket"] == "low") & (current_veh_t1_use["age"] == age),"n"].values
                    if isinstance(n_low, list):
                        n_low = n_low[0]   


                    n_high = current_veh_t1_use.loc[(current_veh_t1_use["powertrain"] == powertrain) & (current_veh_t1_use["vmt_bucket"] == "high") & (current_veh_t1_use["age"] == age),"n"].values
                    
                    if isinstance(n_high, list):
                        n_high = n_high[0]               
                    
                    if not(any(np.isnan(n_low)) or any(np.isnan(n_high))):
                        current_veh_t1_use.loc[(current_veh_t1_use["powertrain"] == powertrain) & (current_veh_t1_use["vmt_bucket"] == "low") & (current_veh_t1_use["age"] == age) ,"reshuffled_n"] = n_low - reshufle_prob*.5*(n_low - n_high)
                        current_veh_t1_use.loc[(current_veh_t1_use["powertrain"] == powertrain) & (current_veh_t1_use["vmt_bucket"] == "high") & (current_veh_t1_use["age"] == age),"reshuffled_n"] = n_high - reshufle_prob*.5*(n_high - n_low)
    current_veh_t1_use["n"] = current_veh_t1_use["reshuffled_n"]
    current_veh_t1_use.drop(columns=['reshuffled_n'], inplace = True)
    
    return(current_veh_t1_use)


def optimize_used(year_current_df, used_market_target_perc):
    # use linear programming to recompute bucket sizes in order to minimize total ghg for the year
    year_current_df_orig = year_current_df.rename(columns={"n": "optimal_n"})

    input_n = year_current_df["n"].sum()

    min_bucket_size = 0# if it is 0, it gets
    max_change = np.sum(year_current_df["n"]) * used_market_target_perc
    ordered_df = pd.DataFrame(
        {
            "powertrain": np.repeat(global_vars.POWERTRAIN_LIST, 2, axis=0),
            "vmt_bucket": ["low", "high"] * 4,
        }
    )

    ordered_df = pd.merge(
        ordered_df,
        year_current_df[
            [
                "powertrain",
                "vmt_bucket",
                "n",
                "vmt",
                "ghg_mile_combined",
                "production_year",
                "age",
            ]
        ],
        on=["powertrain", "vmt_bucket"],
    )


    # replace nans with 0s; as far as the 0 counts are correct, and there are no missing data for non-zero
    # counts, this should work

    if any(ordered_df["vmt"].isna()|ordered_df["n"].isna()|ordered_df["ghg_mile_combined"].isna()):
        return(year_current_df_orig)

    ordered_df["old_n"] = ordered_df["n"]


    current_n = ordered_df["n"].to_numpy()
    vmt = ordered_df["vmt"].to_numpy()
    ghg_mile = ordered_df["ghg_mile_combined"].to_numpy()

    bounds = []
    for i in range(len(current_n)):
        current_bound = (
            np.max([min_bucket_size, current_n[i] - max_change]),
            current_n[i] + max_change,
        )
        bounds.append(current_bound)

    c = np.array([1, 1, 1, 1, 1, 1, 1, 1]) * vmt * ghg_mile

    A_eq = np.array(
        [
            [1, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 1],
            [1, 0, 1, 0, 1, 0, 1, 0],
        ]
    )

    b_eq = np.array(
        [
            current_n[0] + current_n[1],
            current_n[2] + current_n[3],
            current_n[4] + current_n[5],
            current_n[6] + current_n[7],
            current_n[0] + current_n[2] + current_n[4] + current_n[6],
        ]
    )

    A_ub = np.array(
        [
            [1, 0, 1, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 1, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1, 0, 1, 0],

            [0, 1, 0, 1, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 1, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 1, 0, 1],
        ]
    )

    b_ub = np.array(
        [
            current_n[0] + current_n[2] + max_change,
            current_n[0] + current_n[4] + max_change,
            current_n[0] + current_n[6] + max_change,
            current_n[2] + current_n[4] + max_change,
            current_n[2] + current_n[6] + max_change,
            current_n[4] + current_n[6] + max_change,

            current_n[1] + current_n[3] + max_change,
            current_n[1] + current_n[5] + max_change,
            current_n[1] + current_n[7] + max_change,
            current_n[3] + current_n[5] + max_change,
            current_n[3] + current_n[7] + max_change,
            current_n[5] + current_n[7] + max_change,
        ]
    )

    res = optimize.linprog(
        # https://www.educative.io/answers/what-is-optimizelinprog-in-scipy
        c=c,
        A_eq=A_eq,
        b_eq=b_eq,
        A_ub=A_ub,
        b_ub=b_ub,
        bounds=bounds,
        method="highs",
    )
    ordered_df["optimal_n"] = res["x"]

    input_n = year_current_df["n"].sum()
    output_n = ordered_df["optimal_n"].sum()
    diff = np.absolute(input_n - output_n)
    if (diff>1):
        # if there is an error in ns return the original data frame
        logger.info(f"difference: {diff}, input_n: {input_n}, output_n: {output_n}")
        logger.info(f"{ordered_df}")
        return(year_current_df_orig)



    return ordered_df


###### Node Functions ######


def compute_total_ghg(
    # move to a dataframe from scalar
    value: float,
    current_veh_t1_used_market: DataFrame,
    disposed_veh_t1: DataFrame,
) -> float:
    updated_value = value.copy()

    return_value = np.sum(current_veh_t1_used_market["use_ghg"]) + np.sum(current_veh_t1_used_market["production_ghg"]) + np.sum(disposed_veh_t1["ghg_cost_x_n"])

    return return_value
 


def compute_electricity_ghg_gallon(
    value: float,
    electricity_ghg_kwh: float,
) -> float:
    # source: https://en.wikipedia.org/wiki/Gasoline_gallon_equivalent
    return 33.7 * (electricity_ghg_kwh/1000)


def compute_current_veh_t1(
    value: DataFrame,
    inventory_update: DataFrame,
    vmt_function: DataFrame,
) -> DataFrame:
    current_df = inventory_update[inventory_update["current_or_disposed"] == "current"]
    current_df["vmt_old"] = current_df["vmt"]
    current_df = current_df.drop(["current_or_disposed", "vmt"], axis=1) #"vmt"
    current_df = current_df.merge(vmt_function[["age", "vmt_bucket", "vmt"]], how = "left", on = ["age", "vmt_bucket"])
    return current_df

def compute_disposed_veh_t1(
    value: DataFrame,
    inventory_update: DataFrame,
    disposal_ghg_cost: float,
) -> DataFrame:
    disposed_df = inventory_update[
        inventory_update["current_or_disposed"] == "disposed"
    ]
    disposed_df = disposed_df.drop(["current_or_disposed"], axis=1)
    disposed_df["ghg_cost_x_n"] = disposed_df["n"] * disposal_ghg_cost
    return disposed_df


def compute_current_veh_t1_use(
    value: DataFrame,
    current_veh_t1: DataFrame,
    use_vmt: float,
    charging: float,
    eco_driving: float,
    gas_ghg_gallon: float,
    production_ghg_cost_body: float,
    production_ghg_cost_ice: float,
    production_ghg_cost_kwh: float,
    electricity_ghg_gallon: float,
) -> DataFrame:
    
    buff_df = current_veh_t1.copy()
    buff_df["vmt"] = buff_df["vmt"]*(use_vmt/global_vars.VMT_YEAR)


    buff_df["production_ghg"] = buff_df["n"] * production_ghg_cost_body
    
    buff_df["production_ghg"] = buff_df["production_ghg"] + buff_df["n"]*buff_df["batt_kwh"]*production_ghg_cost_kwh
    
    if "has_ice" in buff_df.columns:
        buff_df = buff_df.drop("has_ice", axis = 1) #there is a weird duplication of columns, replace with fresh version

    buff_df = buff_df.merge(pd.DataFrame({"powertrain":global_vars.POWERTRAIN_LIST, "has_ice": [1,1,1,0]}), on = "powertrain")

    buff_df["production_ghg"] = buff_df["production_ghg"] + buff_df["n"]*buff_df["has_ice"]*production_ghg_cost_ice

    buff_df.loc[buff_df["age"] > 0, "production_ghg"] = 0


    buff_df["ev_range_estim"] = None
    for i in range(buff_df.shape[0]):
        if buff_df.loc[i, "powertrain"] == "bev":
            buff_df.loc[i, "ev_range_estim"] = get_ev_range_from_batt_kwh(
                buff_df["batt_kwh"][i], buff_df["mpge"][i], "bev"
            )
        elif buff_df.loc[i, "powertrain"] == "phev":
            buff_df.loc[i, "ev_range_estim"] = get_ev_range_from_batt_kwh(
                buff_df["batt_kwh"][i], buff_df["mpge"][i], "phev"
            )


    buff_df.loc[buff_df["ev_range"].isnull(), "ev_range"] = buff_df.loc[buff_df["ev_range"].isnull(), "ev_range_estim"]

    # uf_from_range
    buff_df["uf_from_range"] = None
    for i in range(buff_df.shape[0]):
        if buff_df.loc[i, "powertrain"] == "phev":
            buff_df.loc[i, "uf_from_range"] = get_uf_from_ev_range(
                buff_df.loc[i, "ev_range"]
            )
        elif buff_df.loc[i, "powertrain"] == "bev":
            buff_df.loc[i, "uf_from_range"] = 1
        else:
            buff_df.loc[i, "uf_from_range"] = 0

    buff_df["uf_real"] = buff_df["uf_from_range"] * (charging/100)
    buff_df.loc[buff_df["powertrain"] == "bev", "uf_real"] = 1
    buff_df.loc[buff_df["powertrain"] == "icev", "uf_real"] = 0
    buff_df.loc[buff_df["powertrain"] == "hev", "uf_real"]= 0

    buff_df["ghg_mile_gas"] = gas_ghg_gallon * (1 - buff_df["uf_real"]) * (1 / buff_df["mpg"])
    buff_df["ghg_mile_electric"] = electricity_ghg_gallon * buff_df["uf_real"] * (1 / buff_df["mpge"])
    buff_df["ghg_mile_combined"] = (buff_df.fillna(0)['ghg_mile_gas'] + buff_df.fillna(0)['ghg_mile_electric'])*(1-eco_driving/100)

    buff_df["use_ghg"] = buff_df["vmt"]*buff_df["n"]* buff_df["ghg_mile_combined"]


    return buff_df


def compute_current_veh_t1_used_market(
    value: DataFrame,
    current_veh_t1_use: DataFrame,
    used_market_target_perc: float,
) -> DataFrame:
    current_veh_t1_used_market = current_veh_t1_use.copy()
    if "optimal_n" in current_veh_t1_used_market.columns:
        current_veh_t1_used_market = current_veh_t1_used_market.drop(["optimal_n"], axis = 1)
    current_veh_t1_used_market = reshuffle_used(current_veh_t1_used_market
                                                , reshufle_prob = 0.15)
 
    if used_market_target_perc == 0:
        return current_veh_t1_used_market
    ages = np.unique(current_veh_t1_used_market["age"])
    post_df = pd.DataFrame()
    for age in ages:

        buff_df = optimize_used(
            current_veh_t1_used_market[current_veh_t1_used_market["age"] == age],
            used_market_target_perc / 100,
        )
        post_df = pd.concat([post_df, buff_df])
    current_veh_t1_used_market = pd.merge(
        current_veh_t1_used_market,
        post_df[["optimal_n", "vmt_bucket", "age", "powertrain"]],
        on=["vmt_bucket", "age", "powertrain"],
    )

    current_veh_t1_used_market["n"] = current_veh_t1_used_market["optimal_n"]

    current_veh_t1_used_market.drop(["optimal_n"], axis=1)

    current_veh_t1_used_market["use_ghg"] = (
        current_veh_t1_used_market["n"]
        * current_veh_t1_used_market["vmt"]
        * current_veh_t1_used_market["ghg_mile_combined"]
    )
    
    return current_veh_t1_used_market


def compute_new_veh_t0(
    value: DataFrame,
    veh_mpg: DataFrame,
    veh_mpge: DataFrame,
    veh_battery_size: DataFrame,
) -> DataFrame:
    buff_df = reduce(
        lambda left, right: pd.merge(
            left, right, on=["powertrain", "year"], how="inner"
        ),
        [veh_mpg, veh_mpge, veh_battery_size],
    )
    
    buff_df["age"] = 0
    buff_df["production_year"] = global_vars.CALENDAR_YEAR + 1
    buff_df["ev_range"] = None


    if buff_df[buff_df["powertrain"] == "bev"]["batt_kwh"].count() > 0:
        buff_df.loc[buff_df["powertrain"] == "bev", "ev_range"] = get_ev_range_from_batt_kwh(
            buff_df[buff_df["powertrain"] == "bev"]["batt_kwh"].values[0],
            buff_df[buff_df["powertrain"] == "bev"]["mpge"].values[0],
            "bev",
        )
    if buff_df[buff_df["powertrain"] == "phev"]["batt_kwh"].count() > 0:
        buff_df.loc[buff_df["powertrain"] == "phev", "ev_range"] = get_ev_range_from_batt_kwh(
            buff_df[buff_df["powertrain"] == "phev"]["batt_kwh"].values[0],
            buff_df[buff_df["powertrain"] == "phev"]["mpge"].values[0],
            "phev",
        )
    

    return buff_df


def compute_inventory_update(
    value: dict,
    new_veh_t0: DataFrame,
    current_veh_t0: DataFrame,
    surv_funct: DataFrame,
    new_powertrain_prop: DataFrame,
) -> DataFrame:

    

    max_veh_age = 50  # this should also be coordinated with the survival function
    year = global_vars.YEAR

 
    current_veh_t0["mpg"] = np.where(
        (current_veh_t0["mpg"].isna()) & (current_veh_t0["l_100km"].notna()),
        global_vars.l_100km_to_mpg(current_veh_t0["l_100km"]),
        current_veh_t0["mpg"],
    )
    current_veh_t0["mpge"] = np.where(
        (current_veh_t0["mpge"].isna()) & (current_veh_t0["l_100kme"].notna()),
        global_vars.l_100km_to_mpg(current_veh_t0["l_100kme"]),
        current_veh_t0["mpge"],
    )
    current_veh_t0["l_100km"] = np.where(
        (current_veh_t0["l_100km"].isna()) & (current_veh_t0["mpg"].notna()),
        global_vars.mpg_to_l_100km(current_veh_t0["mpg"]),
        current_veh_t0["l_100km"],
    )
    current_veh_t0["l_100kme"] = np.where(
        (current_veh_t0["l_100kme"].isna()) & (current_veh_t0["mpge"].notna()),
        global_vars.mpg_to_l_100km(current_veh_t0["mpge"]),
        current_veh_t0["l_100kme"],
    )


    total_n_t0 = np.sum(current_veh_t0["n"])
    

    current_veh_t1 = current_veh_t0.copy()
    current_veh_t1["age"] = current_veh_t1["age"] + 1
    
    older_than_max_df = current_veh_t1[current_veh_t1["age"] > max_veh_age]

    current_veh_t1 = current_veh_t1[current_veh_t1["age"] <= max_veh_age]
    
    current_veh_t1 = current_veh_t1.merge(surv_funct[["age", "lag1_scrappage"]], on = "age")


    current_veh_t1["n_orig"] = current_veh_t1["n"]
    
    current_veh_t1["n_drop"] = current_veh_t1["n"]*current_veh_t1["lag1_scrappage"]
 

    current_veh_t1["n_keep"] =current_veh_t1["n"] - current_veh_t1["n_drop"]
    current_veh_t1.loc[current_veh_t1["n_keep"] < 0, "n_keep"] = 0

    current_veh_t1 = current_veh_t1.drop(["n", "n_orig"], axis=1)
    current_veh_t1 = current_veh_t1.rename(columns={"n_keep": "n"})

    disposed_veh_t1 = current_veh_t1.copy()
    disposed_veh_t1 = disposed_veh_t1[
        [
            "year",
            "powertrain",
            "vmt_bucket",
            "n_drop",
            "production_year",
            "age",
        ]
    ]
    disposed_veh_t1 = disposed_veh_t1.rename(columns={"n_drop": "n"})
    disposed_veh_t1 = pd.concat([disposed_veh_t1, older_than_max_df])

    total_disposed = disposed_veh_t1["n"].sum()


    n_new = total_n_t0 * global_vars.RENEWAL_RATE

    # normalize proportions, treat inputs as frequencies, in case they don't end up to 100
    new_powertrain_prop["proportion"] = new_powertrain_prop["freq"]/np.sum(new_powertrain_prop["freq"])

    # add new vehicles to current t0
    if global_vars.YEAR < global_vars.N_YEARS:
        new_veh_t0_buff = pd.merge(
            new_veh_t0, new_powertrain_prop[["powertrain", "proportion"]], on=["powertrain"]
        )
        new_veh_t0_buff["n"] = new_veh_t0_buff["proportion"] * n_new
        new_veh_t0_buff["age"] = 0
        new_veh_t0_buff["vmt_bucket"] = "high"
        new_veh_t0_buff_low = new_veh_t0_buff.copy()
        new_veh_t0_buff_low["vmt_bucket"] = "low"
        new_veh_t0_buff = pd.concat([new_veh_t0_buff, new_veh_t0_buff_low])
        new_veh_t0_buff["n"] = (
            new_veh_t0_buff["n"] / 2
        )  # we need this because we have two groups, high and low miles

        current_veh_t1 = pd.concat([current_veh_t1, new_veh_t0_buff])

    #####

    current_veh_t1 = current_veh_t1[
        [
            "year",
            "powertrain",
            "age",
            "n",
            "production_year",
            "vmt_bucket",
            "mpg",
            "mpge",
            "l_100km",
            "l_100kme",
            "ev_range",
            "batt_kwh",
            "vmt",
        ]
    ]



    current_veh_t1["current_or_disposed"] = "current"
    disposed_veh_t1["current_or_disposed"] = "disposed"

    output_df = pd.concat([current_veh_t1, disposed_veh_t1])


    return output_df

def compute_vmt_function(
    value: dict,
    age_vmt: DataFrame,
    high_vmt: DataFrame,
) -> DataFrame:
    age_vmt = age_vmt.rename(columns={"age_vmt": "vmt_pre"})
    merged_df = age_vmt.merge(high_vmt, on = "age")
    df_high = merged_df.copy()
    df_high["vmt_bucket"] = "high"
    df_high["vmt"] = df_high["vmt_pre"]*(df_high["high_vmt"]/100)*2 # high = proportion_high*2*average_vmt
    
    df_low = merged_df.copy()
    df_low["vmt_bucket"] = "low"
    df_low["vmt"] = df_low["vmt_pre"]*((1-df_low["high_vmt"]/100))*2
    df_out = pd.concat([df_low, df_high])
    df_out = df_out[["age", "vmt", "vmt_bucket",]]
    return(df_out)

def compute_n_vehicles(
    value: DataFrame,
    inventory_update: DataFrame,
) -> DataFrame:
    return(np.sum(inventory_update.loc[inventory_update["current_or_disposed"] == "current", "n"]))


###### Graph Definition ######


def causal_carbon_nodes() -> list[EkidenNode]:
    powertrain = pd.Series( global_vars.POWERTRAIN_LIST, dtype="string",)
    current_veh_t0_init_df = pd.read_csv("data/current_veh_t0_VMT.csv")
    current_veh_t0 = TensorEkidenNode(
        "current_veh_t0",
        None,
        current_veh_t0_init_df,
        None,
        "process",
        "This node represent the state of the current vehicles at the end of the previous year cycle. Non-adjustable.",
    )

    current_veh_t1 = TensorEkidenNode(
        "current_veh_t1",
        compute_current_veh_t1,
        None,
        None,
        "process",
        "This node represent the state of the current vehicles when they enter the year cycle. Non-adjustable.",
    )

    disposed_veh_t1 = TensorEkidenNode(
        "disposed_veh_t1",
        compute_disposed_veh_t1,
        None,
        None,
        "process",
        "This nodes repersents the set of disposed vehicles. Non-adjustable.",
    )

    current_veh_t1_use = TensorEkidenNode(
        "current_veh_t1_use",
        compute_current_veh_t1_use,
        None,
        None,
        "process",
        "This node represent the state of the current vehicles when vehicle use parameters are included. Non-adjustable.",
    )

    current_veh_t1_used_market = TensorEkidenNode(
        "current_veh_t1_used_market",
        compute_current_veh_t1_used_market,
        None,
        None,
        "process",
        "This node represents the state of the current vehicles fleet after any ownership changes associated with the used vehicle market are included. Non-adjustable.",
    )

    veh_mpg = TensorEkidenNode(  # source: the frequency weighted data from the current_fleet_mix_VMT.csv
        "veh_mpg",
        None,
        initial_values.veh_mpg["default"], # Based on RAV4, RAV4 HEV, RAV4 Prime
        # DataFrame({"powertrain": powertrain, "mpg": [21.82, 33.32, 25.29, None]}), # based on most recent values in sales data
        initial_values.veh_mpg["progress"],
        "tech",
        "This node represents the fuel economy of a given powertrain. The default values are based on four comparable crossover models.",
    )

    veh_mpge = TensorEkidenNode(  # source: the frequency weighted data from the current_fleet_mix_VMT.csv
        "veh_mpge",
        None,
        initial_values.veh_mpge["default"], # based on prius Prime and bz4x
        # DataFrame({"powertrain": powertrain, "mpge": [None, None, 61.9, 110.43]}), # based on most recent values in sales data
        initial_values.veh_mpge["progress"],
        "tech",
        "This node represents the fuel economy equivalent of a given powertrain in [mpge](https://www.epa.gov/greenvehicles/fuel-economy-and-ev-range-testing) when a vehicle is driven in an electric mode. The default values are based on four comparable crossover models.",
    )

    veh_battery_size = TensorEkidenNode(  # source: the frequency weighted data from the current_fleet_mix_VMT.csv
        "veh_battery_size",
        None,
        initial_values.veh_battery_size["default"], # based on RAV4 family
        None,
        "tech",
        "This node represents the vehicle powertrain battery size in kWh. The default values are based are based on four comparable crossover models.",
    )
    new_veh_t0 = TensorEkidenNode(
        "new_veh_t0",
        compute_new_veh_t0,
        None,
        None,
        "process",
        "In this node we create the stock of new vehicles which will be added to the current fleet. Non-adjustable.",
    )
    

    new_powertrain_prop = TensorEkidenNode(
        "new_powertrain_prop",
        None,
        initial_values.new_powertrain_prop["default"],       
        initial_values.new_powertrain_prop["progress"],
        "tech",
        "This node represents hypothetical frequencies of the four powertrains. Instead of precentages, the numbers represent counts to help the user to avoid\
         sum conflicts. If the counts add up exactly to 100, wihin each year, they can be treated as relative percentages, \
        if they don't they are normalized to represent relative proportions. \
        For example, if the four dirvetrains are all set at the same frequency [25,25,25,25] or at [100,100,100,100], these corresponds to a \
        quarter of of the marketshare for each powertrain. The default values are based on 2024 sales [www.eia.gov](https://www.eia.gov/todayinenergy/detail.php?id=62063) \
        while progress values are based on averages from the EPA's 2024 targets [www.epa.gov](https://www.epa.gov/newsreleases/biden-harris-administration-finalizes-strongest-ever-pollution-standards-cars-position)   ",
    )
    # phev market share projection https://teem.ornl.gov/pev-market-share.shtml

    used_market_target_perc = ScalarEkidenNode(
        "used_market_target_perc",
        None, 
        initial_values.used_market_target_perc["default"],
        initial_values.used_market_target_perc["progress"], 
        0.0, 
        5.0, 
        "beh", 
        "This node represents a hypothetical intervention where incentives targetting the used car market shift VMT towards more efficient vehicles. (see [Nunnes et al., 2022](https://www.nature.com/articles/s41893-022-00862-3)). The used vehicle market is about three times larger than the new vehicles market, and can reach about 15% of the existing stock. (see [BTT data](https://www.bts.gov/content/new-and-used-passenger-car-sales-and-leases-thousands-vehicles))",
    )

    

    electricity_ghg_kwh = ScalarEkidenNode(
        "electricity_ghg_kwh", 
        None, 
        initial_values.electricity_ghg_kwh["default"], 
        initial_values.electricity_ghg_kwh["progress"], 
        0, 
        500, 
        "tech", 
        "GHG cost in grams/kWh. The linear trend is extrapolated from [here](https://ourworldindata.org/grapher/carbon-intensity-electricity?tab=chart&country=USA). As a reference, the esimated value for 2023 was 369g/kWh.",
    ) 
    # 0.369 - 2023 value
  
    electricity_ghg_gallon = ScalarEkidenNode(
        "electricity_ghg_gallon", 
        compute_electricity_ghg_gallon, 
        None, 
        None, 
        0, 
        100, 
        "process", 
        "This node creates GHG equivallence between electricity and fuel. Non-adjustable.",
    )

    gas_ghg_gallon = ScalarEkidenNode(
        "gas_ghg_gallon", 
        None, 
        initial_values.gas_ghg_gallon["default"], 
        initial_values.gas_ghg_gallon["progress"],  
        5, 
        10, 
        "tech", 
        "We assume 8.89kg/gallon [source](https://www.epa.gov/greenvehicles/greenhouse-gas-emissions-typical-passenger-vehicle)",
     )

    production_ghg_cost_body = ScalarEkidenNode(
        "production_ghg_cost_body", 
        None, 
        initial_values.production_ghg_cost_body["default"], 
        initial_values.production_ghg_cost_body["progress"],  
        2000, 
        8000, 
        "tech", 
        "We assume about 4200kg of carbon for producing the body of a vehicle. [source](https://www.autoexpress.co.uk/sustainability/358628/car-pollution-production-disposal-what-impact-do-our-cars-have-planet)",
    )

    production_ghg_cost_kwh = ScalarEkidenNode(
        "production_ghg_cost_kwh", 
        None, 
        initial_values.production_ghg_cost_kwh["default"], 
        initial_values.production_ghg_cost_kwh["progress"],  
        10, 
        300, 
        "tech", 
        "We assume 100kg/kWh [source](https://www.mckinsey.com/industries/automotive-and-assembly/our-insights/the-race-to-decarbonize-electric-vehicle-batteries), but there is a broader range of estimates which can depend on multiple factors [source](https://climate.mit.edu/ask-mit/how-much-co2-emitted-manufacturing-batteries) ",
    )
    # https://climate.mit.edu/ask-mit/how-much-co2-emitted-manufacturing-batteries - range is 30 to 200kg per kwh
 
    production_ghg_cost_ice = ScalarEkidenNode(
        "production_ghg_cost_ice", 
        None, 
        initial_values.production_ghg_cost_ice["default"], 
        initial_values.production_ghg_cost_ice["progress"], 
        500, 
        2000, 
        "tech", 
        "We assume about 1400kg of carbon for producing the ICE. [source](https://www.autoexpress.co.uk/sustainability/358628/car-pollution-production-disposal-what-impact-do-our-cars-have-planet",
    )

    disposal_ghg_cost = ScalarEkidenNode(
        "disposal_ghg_cost", 
        None, 
        initial_values.disposal_ghg_cost["default"], 
        initial_values.disposal_ghg_cost["progress"], 
        1000, 
        3000, 
        "tech", 
        "We assume about 2800kg of carbon for disposing a vehicle. [source](https://www.autoexpress.co.uk/sustainability/358628/car-pollution-production-disposal-what-impact-do-our-cars-have-planet)",
    )

    inventory_update = TensorEkidenNode(
        "inventory_update",
        compute_inventory_update,
        None,
        None,
        "process", 
        "In this node we add new stock vehicles to the current stock and we remove the disposed vehicles. Non-adjustable.",
    )

    total_ghg = ScalarEkidenNode(
        "Total GHG", 
        compute_total_ghg, 
        None, 
        None, 
        0, 
        10**15, 
        "outcome", 
        "This is the main dependent variable of the model. It combines the three main source of GHG: production, usage and disposal. Non-adjustable.",
    )
    
    use_vmt = ScalarEkidenNode(
        "use_vmt", 
        None, 
        initial_values.use_vmt["default"], 
        initial_values.use_vmt["progress"],  
        9000, 
        12000, 
        "beh", 
        "We use 10,252 miles as default average, derived from combining [NHTS 2017](https://nhts.ornl.gov/downloads) VMT by age and [Greene & Leard](https://baker.utk.edu/wp-content/uploads/2022/07/A-Statistical-Analysis-of-Trends-in-Light-duty-Vehicle-Scrappage-and-Survival-2003–2020.Report.pdf) survivability model. VMT can naturally decrease up to 5% as a function of changes in gas prices [energy.gov](https://www.energy.gov/eere/vehicles/articles/fotw-1313-october-23-2023-relationship-between-vehicle-miles-traveled-and) ",
    )
    

    age_vmt_df = pd.read_csv('data/vmt_by_age.csv')
    age_vmt_df = age_vmt_df.rename(columns={"vmt": "age_vmt"})
    age_vmt_df = age_vmt_df[["age", "age_vmt"]]
    age_vmt = TensorEkidenNode(
        "age_vmt",
        None,
        age_vmt_df,
        None,
        "process", 
        "VMT varies as a function of vehicle age [pdf](https://nhts.ornl.gov/assets/2017_nhts_summary_travel_trends.pdf). Non-adjustable.",
    )

    high_vmt_df = pd.read_csv('data/vmt_by_age.csv')
    high_vmt_df = high_vmt_df.rename(columns={"high_VMT_prop": "high_vmt"})
    high_vmt_df["high_vmt"] = high_vmt_df["high_vmt"]*100
    high_vmt_df = high_vmt_df[["age", "high_vmt"]]
    high_vmt = TensorEkidenNode(
        "high_vmt",
        None,
        high_vmt_df,
        None,
        "process", 
        "High- and low-VMT buckets from NHTS 2017 data.[pdf](https://nhts.ornl.gov/assets/2017_nhts_summary_travel_trends.pdf). Non-adjustable.",
    )

    vmt_function = TensorEkidenNode(
        "vmt_function",
        compute_vmt_function,
        None,
        None,
        "process", 
        "This node adds high- and low-VMT buckets. Non-adjustable.",
    )


    charging = ScalarEkidenNode(
        "charging", 
        None, 
        initial_values.charging["default"], 
        initial_values.charging["progress"],
        0, 
        100, 
        "beh", 
        "The utility factor is computed based on the assumption that PHEVs are charged before every driving day. In reality drivers can charge less frequently, with estimates of overnight charging varying broadly (from less than 60% to more than 90%). For more details see [pdf](https://iopscience.iop.org/article/10.1088/1748-9326/ac94e8/pdf), and [pdf](https://publica.fraunhofer.de/bitstreams/f654ee98-18d1-40bf-ab7e-c5d1a76bd71a/download).",
    )
    
    eco_driving = ScalarEkidenNode(
        "eco_driving", 
        None, 
        initial_values.eco_driving["default"], 
        initial_values.eco_driving["progress"], 
        0, 
        10, 
        "beh", 
        "Various interventions can lead to reduction in fuel consumption to 25% or more [pdf](https://www.mdpi.com/2071-1050/13/1/226). ",
    )

    survival_function_df = pd.read_csv("data/averaged_survival_v2.csv", index_col=[0])
    surv_funct = TensorEkidenNode(
        "surv_funct",
        None,
        survival_function_df,
        None,
        "process", 
        "The survival and scrappage values are based on combined trucks and cars estimates from Greene & Leard (2024)  [pdf](https://baker.utk.edu/wp-content/uploads/2022/07/A-Statistical-Analysis-of-Trends-in-Light-duty-Vehicle-Scrappage-and-Survival-2003–2020.Report.pdf).",
    )

    return [
        age_vmt,
        charging,
        current_veh_t0,
        current_veh_t1_use,
        current_veh_t1_used_market,
        current_veh_t1,
        disposal_ghg_cost,
        disposed_veh_t1,
        eco_driving,
        electricity_ghg_gallon,
        electricity_ghg_kwh,
        gas_ghg_gallon,
        high_vmt,
        inventory_update,
        new_powertrain_prop,
        new_veh_t0,
        production_ghg_cost_body,
        production_ghg_cost_ice,
        production_ghg_cost_kwh,
        surv_funct,
        total_ghg,
        use_vmt,
        used_market_target_perc,
        veh_battery_size,
        veh_mpg,
        veh_mpge,
        vmt_function,
    ]
