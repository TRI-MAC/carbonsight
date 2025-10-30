import global_vars
import pandas as pd
import numpy as np

n_years = 10#global_vars.N_YEARS

eco_driving = {"default": np.repeat(0, n_years).tolist(),
	"progress": np.repeat(3, n_years).tolist(),}

charging = {"default": np.repeat(60, n_years).tolist(),
	"progress": np.repeat(100, n_years).tolist(),}


use_vmt = {"default": np.repeat(global_vars.VMT_YEAR, n_years).tolist(),
	"progress": np.repeat(global_vars.VMT_YEAR*0.95, n_years).tolist(),} #5% decrease, uniform


used_market_target_perc = {"default": np.repeat(0, n_years).tolist(),
	"progress": np.repeat(2, n_years).tolist(),} #2% vehicles within year aim; in reality much less


########### NO CHANGE  VARS #####
start_df = pd.DataFrame({
    "batt_kwh":[0, 1.8, 18.81, 71.4], # based on RAV4 family; 0, 2, 7.71, 85.8]}), # based on sales and recent models
    "powertrain": global_vars.POWERTRAIN_LIST,
})
default_df = pd.DataFrame()
for i in range(n_years):
    start_df["year"] = i
    default_df = pd.concat([default_df, start_df])
default_df = default_df[["year", "powertrain", "batt_kwh"]]
default_df = default_df.reset_index().drop("index", axis = 1)
veh_battery_size = {"default": default_df} 





######### ELECTRICITY BASED PROGRESS #####
# general decarbonization trend taken from here: https://ourworldindata.org/grapher/carbon-intensity-electricity?tab=chart&country=USA
ghg_2014 = 498
ghg_2023 = 369
decrease_10_years = ghg_2023/ghg_2014



start_value = 369
electricity_ghg_kwh = {"default": np.repeat(start_value,n_years).tolist(),
	"progress": np.linspace(start_value, start_value*decrease_10_years, n_years).tolist(),} 



start_value = 5600*(1/2)
disposal_ghg_cost = {"default": np.repeat(start_value,n_years).tolist(),
	"progress": np.linspace(start_value, start_value*decrease_10_years, n_years).tolist(),} 

start_value = 5600*(1/4)
production_ghg_cost_ice = {"default": np.repeat(start_value,n_years).tolist(),
	"progress": np.linspace(start_value, start_value*decrease_10_years, n_years).tolist(),} 

start_value = 5600*(3/4)
production_ghg_cost_body = {"default": np.repeat(start_value,n_years).tolist(),
	"progress": np.linspace(start_value, start_value*decrease_10_years, n_years).tolist(),} 


# https://climate.mit.edu/ask-mit/how-much-co2-emitted-manufacturing-batteries - range is 30 to 200kg per kwh
start_value = 100
production_ghg_cost_kwh = {"default": np.repeat(start_value,n_years).tolist(),
	"progress": np.linspace(start_value, start_value*decrease_10_years, n_years).tolist(),} 

 

######### FUEL BASED PROGRESS #####
# fuel ghg reduction 
# https://www.decision-innovation.com/news/ethanol-biodiesel-and-renewable-diesel-contribution-to-oregons-clean-fuels-program/

ghg_2016 = 99.4
ghg_2025 = 88.9
decrease_10_years = ghg_2025/ghg_2016

start_value = 8.89
# source: https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator-calculations-and-references

gas_ghg_gallon = {"default": np.repeat(start_value,n_years).tolist(),
	"progress": np.linspace(start_value, start_value*decrease_10_years, n_years).tolist(),} 


######### EFFICENCY BASED PROGRESS #####
# new https://www.energy.gov/eere/vehicles/articles/fotw-1330-february-19-2024-epa-data-show-average-fuel-economy-new-light-duty
# previous https://www.energy.gov/eere/vehicles/articles/fotw-1237-may-9-2022-fuel-economy-all-vehicle-classes-has-improved
mpg_2014 = 24.1
mpg_2023 = 26.9
l_100_km_2014 = global_vars.mpg_to_l_100km(mpg_2014)
l_100_km_2023 = global_vars.mpg_to_l_100km(mpg_2023)
decrease_10_years_l_100_km = l_100_km_2023/l_100_km_2014 # if I don't use l_100km the end point is the same, but the trend is not linear

trend_mpg = np.linspace(
    global_vars.mpg_to_l_100km(start_value), 
    global_vars.mpg_to_l_100km(start_value)*decrease_10_years_l_100_km,
    n_years).tolist()
trend_mpg = [global_vars.mpg_to_l_100km(x) for x in trend_mpg]

start_df = pd.DataFrame({
    "mpg":[30, 39, 38, None],
    "powertrain": global_vars.POWERTRAIN_LIST,
})
default_df = pd.DataFrame()
for i in range(n_years):
	start_df_x = start_df.copy()
	start_df_x["year"] = i
	default_df = pd.concat([default_df, start_df_x])

progress_df = pd.DataFrame()
for i in range(start_df.shape[0]):
	current_df = pd.DataFrame({
			"year" : np.arange(n_years).tolist(),
			"powertrain" : [start_df.powertrain[i]]*n_years
		})
	start_value = start_df.loc[i, "mpg"]
	if not (start_value == None):
		trend_mpg = np.linspace(
		    global_vars.mpg_to_l_100km(start_value), 
		    global_vars.mpg_to_l_100km(start_value)*decrease_10_years_l_100_km,
		    n_years).tolist()
		trend_mpg = [global_vars.mpg_to_l_100km(x) for x in trend_mpg]
	else:
		trend_mpg = [None]*n_years
	current_df["mpg"] = trend_mpg
	progress_df = pd.concat([progress_df, current_df])

veh_mpg = {"default": default_df, 
		   "progress": progress_df, 
}



#veh_mpge


decrease_10_years_l_100_km = .66 # based on # https://www.epri.com/research/products/000000003002030215 # cut energy consumption per mile in half over the next 30 years.

trend_mpg = np.linspace(
    global_vars.mpg_to_l_100km(start_value), 
    global_vars.mpg_to_l_100km(start_value)*decrease_10_years_l_100_km,
    n_years).tolist()
trend_mpg = [global_vars.mpg_to_l_100km(x) for x in trend_mpg]

start_df = pd.DataFrame({
    "mpge":[None, None, 94, 119], #based on prius Prime and bz4x
    "powertrain": global_vars.POWERTRAIN_LIST,
})
default_df = pd.DataFrame()
for i in range(n_years):
	start_df_x = start_df.copy()
	start_df_x["year"] = i
	default_df = pd.concat([default_df, start_df_x])

progress_df = pd.DataFrame()
for i in range(start_df.shape[0]):
	current_df = pd.DataFrame({
			"year" : np.arange(n_years).tolist(),
			"powertrain" : [start_df.powertrain[i]]*n_years
		})
	start_value = start_df.loc[i, "mpge"]
	if not (start_value == None):
		trend_mpg = np.linspace(
		    global_vars.mpg_to_l_100km(start_value), 
		    global_vars.mpg_to_l_100km(start_value)*decrease_10_years_l_100_km,
		    n_years).tolist()
		trend_mpg = [global_vars.mpg_to_l_100km(x) for x in trend_mpg]
	else:
		trend_mpg = [None]*n_years
	current_df["mpge"] = trend_mpg
	progress_df = pd.concat([progress_df, current_df])

veh_mpge = {"default": default_df, 
		   "progress": progress_df, 
}









######### POWERTRAINS #####

#https://www.govinfo.gov/content/pkg/FR-2024-04-18/pdf/2024-06214.pdf
progress_df = pd.read_csv('data/epa_table3.csv')
progress_df = progress_df[(progress_df["pathway"] == "average") &( progress_df["year"] < n_years)] # the file has up to 12 years projection
progress_df = progress_df[["year", "powertrain", "proportion"]]
progress_df = progress_df.rename(columns={"proportion": "freq"})# treat this as frequency, later it will be normalized as proportion
progress_df = progress_df[["year", "powertrain", "freq"]]
progress_df["freq"] = progress_df["freq"].round(2) 
progress_df = progress_df.reset_index().drop("index", axis = 1)


start_df = pd.DataFrame({
    "freq":[82, 9, 2, 7],
    "powertrain": global_vars.POWERTRAIN_LIST,
})
default_df = pd.DataFrame()
for i in range(n_years):
    start_df["year"] = i
    default_df = pd.concat([default_df, start_df])
default_df = default_df[["year", "powertrain", "freq"]]
default_df = default_df.reset_index().drop("index", axis = 1)
new_powertrain_prop = {"default": default_df ,
	"progress": progress_df,} 

