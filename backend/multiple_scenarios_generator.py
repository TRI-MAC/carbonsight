import numpy as np
import pandas as pd
import sys
from numpy import nan
sys.path.append('..')

import initial_values
import global_vars

from itertools import product


# you have to manually adjust the level of embedding, and change the code 

powertrain_list = ["icev", "hev", "phev",  "bev"]

# scalars
vars = {"renewal_rate": np.linspace(2, 8, 3).round(2) , 
        "disposal_rate":  np.linspace(2, 8, 3).round(2)}

vars_keys = [x for x in vars.keys()]
with open("multiple_scenarios/multiple_scenarios_two_scalars.txt", "w") as text_file:
    
    for var0 in vars[vars_keys[0]]:
        for var1 in vars[vars_keys[1]]:
            text_file.write(f'"{vars_keys[0]}:{var0:.2};{vars_keys[1]}:{var1:.2}": {{')
            text_file.write(f'"{vars_keys[0]}": {var0:.2}, "{vars_keys[1]}": {var1:.2}')
            text_file.write('},\n')


# long scalars
var0_space = np.linspace(2, 10, 7).round(2)
var1_space = np.linspace(2, 10, 7).round(2)
var0_list = [[x]*global_vars.N_YEARS + [0]*global_vars.N_YEARS_TAIL for x in var0_space]
var1_list = [[x]*global_vars.N_YEARS + np.linspace(6, 15, global_vars.N_YEARS_TAIL).round(2).tolist() for x in var1_space]


vars = {"renewal_rate":  var0_space, 
        "disposal_rate": var1_space}

vars_list = {"renewal_rate":  var0_list,
            "disposal_rate": var1_list}

vars_keys = [x for x in vars.keys()]
with open("multiple_scenarios/multiple_scenarios_two_scalars_long.txt", "w") as text_file:
    
    # for var0 in vars[vars_keys[0]]:
    #     for var1 in vars[vars_keys[1]]:
    #         text_file.write(f'"{vars_keys[0]}:{var0:.2};{vars_keys[1]}:{var1:.2}": {{')
    #         text_file.write(f'"{vars_keys[0]}": {var0:.2}, "{vars_keys[1]}": {var1:.2}')
    #         text_file.write('},\n')

    for i0 in range(len(vars[vars_keys[0]])):
            for i1 in range(len(vars[vars_keys[1]])):
                text_file.write(f'"{vars_keys[0]}:{vars[vars_keys[0]][i0]:.2};{vars_keys[1]}:{vars[vars_keys[1]][i1]:.2}": {{')
                text_file.write(f'"{vars_keys[0]}": {vars_list[vars_keys[0]][i0]}, "{vars_keys[1]}": {vars_list[vars_keys[1]][i1]}')
                text_file.write('},\n')




#data frame and scalar
# example
df_string = 'pd.DataFrame({"powertrain": ["'+ '", "'.join(powertrain_list) + '"], "batt_kwh": [0, 2, @x, 85.8]})'

vars = {"veh_battery_size": np.linspace(10, 65, 10) , 
        "charging":  np.linspace(50, 100, 5)}
with open("multiple_scenarios/multiple_scenarios_data_frame_and_scalar.txt", "w") as text_file:
    
    for var0 in vars["veh_battery_size"]:
        for var1 in vars["charging"]:
            new_df_string = df_string.replace("@x", f"{var0:.1f}")
            text_file.write(f'"veh_battery_size_phev:{var0:.1f};charging:{var1:.1f}": {{')
            text_file.write(f'"veh_battery_size": {new_df_string}, "charging": {var1:.1f}')
            text_file.write('},\n')


# complex embeded

# example
df_string = 'pd.DataFrame({"powertrain": ["'+ '", "'.join(powertrain_list) + '"], "batt_kwh": [0, 2, @x, 85.8]})'




#progress and default
# example

##### paper interventionss
interventions = {
    "eco_driving" : initial_values.eco_driving,
    "charging" : initial_values.charging, 
    "use_vmt" : initial_values.use_vmt, 
    "used_market_target_perc" : initial_values.used_market_target_perc, 
    "production_ghg_cost_ice" : initial_values.production_ghg_cost_ice, 
    "production_ghg_cost_body" : initial_values.production_ghg_cost_body, 
    "production_ghg_cost_kwh" : initial_values.production_ghg_cost_kwh,
    "veh_mpg" : initial_values.veh_mpg,
    "veh_mpge" : initial_values.veh_mpge, 
    "new_powertrain_prop" : initial_values.new_powertrain_prop,
    "electricity_ghg_kwh" : initial_values.electricity_ghg_kwh,
    "gas_ghg_gallon" : initial_values.gas_ghg_gallon,
}
#####  end paper interventions #####



##### local intervention
# initial_values.veh_battery_size = dict()
# initial_values.charging = dict()

# for x in np.linspace(50, 100, 5):
#     initial_values.charging .update({str(int(x)): np.repeat(x, global_vars.N_YEARS).tolist()})

# initial_df = pd.DataFrame({"powertrain": powertrain_list, "batt_kwh": [0, 2, -1, 85.8]})
# for x in np.linspace(10, 65, 5).round():
#     new_df = initial_df.copy()
#     new_df.loc[new_df["batt_kwh"] == -1, "batt_kwh"] = x
#     initial_values.veh_battery_size.update({str(int(x)): new_df})



# interventions = {
#     "production_ghg_cost_kwh" : initial_values.production_ghg_cost_kwh,
#     "veh_mpg" : initial_values.veh_mpg,
#     "veh_mpge" : initial_values.veh_mpge, 
#     "electricity_ghg_kwh" : initial_values.electricity_ghg_kwh,
#     "gas_ghg_gallon" : initial_values.gas_ghg_gallon,
#     "charging" : initial_values.charging, 
#     "veh_battery_size" : initial_values.veh_battery_size, 
# }
##### end local interventions ####


def expand_grid(dictionary):
   return pd.DataFrame([row for row in product(*dictionary.values())], 
                       columns=dictionary.keys())



expanded_df= expand_grid(interventions)
print(expanded_df)
print(initial_values.veh_mpg)


with open("multiple_scenarios/multiple_scenarios_progress_default.txt", "w") as text_file:
    for row_i in range(expanded_df.shape[0]):
        #print(row_i)
        scenario_name = '"'
        var_values = ''
        for col_i in expanded_df.columns:
            #print(col_i)
            scenario_name = scenario_name + col_i + '=' + str(expanded_df.loc[row_i,col_i]) +';'
            code = 'data_object = initial_values.'+ col_i + '["'+ expanded_df.loc[row_i,col_i]+'"]'
            #print(code)
            exec(code)
            #print(code)
            #print(data_object)
            if isinstance(data_object, pd.DataFrame):
                data_string = 'pd.DataFrame(' + str(data_object.to_dict("list")) + ')'
            elif isinstance(data_object, list):
                data_string = '[' + ','.join([str(x) for x in data_object]) + ']'
            else:
                data_string = None
            var_values =  var_values + ' "' + col_i + '":'  + data_string  + ','
        scenario_name = scenario_name[:-1] + '"'
        full_line = scenario_name + ': {' + var_values + '},\n'
        text_file.write(full_line)
