
library(dplyr)
library(reshape2)
library(ggplot2)

library(stringdist)
library(stringr)
library(rapport)


# The fleet will have variable size (total n can increase or decrease ) and variable VMT/vehicle (it can increase or decrease).
# The total VMT will be constant, so if total n increases, then VMT/vehicle will have to decrease.
# VMT will be allowed to differ from year to year.
# Compute low and high VMT (median split) for each year


current_year <- 2024



# 40 by 4 takes about 1 hour to run ; 46mln rows
all_df <- data.frame()
for (k in 0:2) {
  for (j in 0:3){
    print(c(k, j))
    file_name <- paste0("~/Downloads/data_axle/clean/file_", k,"_",j,".csv")
    current_df <- read.csv(file_name)
    current_df <- current_df %>% lapply(function(x) as.character(x)) %>% as.data.frame()
    #print(colnames(current_df))
    all_df <- bind_rows(all_df, current_df)
  }
}
nrow(all_df)

all_df$vehicles.X.odometer <- all_df$vehicles.X.odometer %>% as.numeric()
all_df$vehicles.X.model_year <- all_df$vehicles.X.model_year %>% as.numeric()
all_df$vehicles.X.age <- 2024 - all_df$vehicles.X.model_year
data_axle_df <- all_df %>% filter(vehicles.X.age <= 50)

#buff_df_total_n <- data_axle_df %>% group_by(family.id) %>% summarise(vehicle_count = n())

drop_strings <- function(string_vec, drop_vec) {
  # replaces the sub_strings in drop_vec with empty spaces
  output_vec <- string_vec %>% tolower()
  for (item in drop_vec) {
    output_vec <- output_vec %>% str_replace_all(item, "")
  }
  output_vec <- output_vec %>% trimws()
  return(output_vec)
}


data_axle_df$make <-  data_axle_df$vehicles.X.make %>% 
  tolower() %>% 
  #str_replace_all("\\s{1,}", "")  %>%
  str_replace_all(",,", ",")

drop_vec <- c("awd", "rwd", "fwd", "2wd", "4wd", "xdrive", "4matic", "wagon", "cabrio", 
              "quattro","hybrid", "coupe","convertible","pickup", "c15","k15", "2dr", "4dr", "5dr", 
              "luxury", "doors", "door")

data_axle_df$model <-  data_axle_df$vehicles.X.model %>%  drop_strings(drop_vec)

data_axle_df$year <- data_axle_df$vehicles.X.model_year
data_axle_df$powertrain <- data_axle_df$vehicles.X.fuel_type

data_axle_df$powertrain <- data_axle_df$powertrain %>% recode(bio_diesel = "other", bev = "electric", diesel = "other", electric = "bev",
                                                              flex_fuel = "icev", gas_electric_hybrid = "hev", gasoline = "icev",
                                                              hydrogen_fuel_cell = "other", natural_gas = "other", propane = "other", plug_in_hybrid = "phev")


data_axle_df <- data_axle_df %>% filter(powertrain %in% c("hev", "icev", "bev", "phev"))

data_axle_df$model <- data_axle_df$model %>% dplyr::na_if("")
data_axle_df <- data_axle_df %>% filter(!is.na(model))

# create look up dictionaries ... 
da_look_up <- data_axle_df %>% group_by(make, model, powertrain, year) %>% summarize(n = n())


folder_path <- "~/repos/tri_mac/counterfactual_calculator/ekiden/data/"
file_path <- paste0(folder_path, "da_look_up.csv")
write.csv(da_look_up, file_path, row.names = FALSE)


