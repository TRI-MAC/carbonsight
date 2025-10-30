library(dplyr)
library(reshape2)
library(ggplot2)
library(stringr)


current_year <- 2024
current_fleet_n <- 280*10^6

file_path <- "~/repos/tri_mac/counterfactual_calculator/ekiden/data//veh_specs_merged.csv"
veh_specs_merged_df <- read.csv(file_path, header = TRUE) 

file_path <- "~/repos/tri_mac/counterfactual_calculator/ekiden/data/vmt_by_age.csv"
vmt_by_age <- read.csv(file_path, header = TRUE) 

file_path <- "~/repos/tri_mac/counterfactual_calculator/ekiden/data/survival_function_greene.csv"
survival_df <- read.csv(file_path, header = TRUE)  %>% rename(age = "ages")
survival_df$n_year <- current_fleet_n*survival_df$survival/sum(survival_df$survival)
plot(survival_df$age, survival_df$n)

current_veh_t0 <- veh_specs_merged_df

current_veh_t0$age <- 2024 - current_veh_t0$year
current_veh_t0 <- current_veh_t0 %>% select(-n_year) %>% merge(survival_df %>% select(age, n_year), by = "age")
current_veh_t0$n <- current_veh_t0$n_year*current_veh_t0$proportion

current_veh_t0 %>% ggplot(aes(x = age, y = n, color = powertrain)) +
  geom_line()

current_veh_t0 %>% ggplot(aes(x = age, y = mpg, color = powertrain)) +
  geom_line()
                             
# add VMT
current_veh_t0 <- current_veh_t0 %>% merge(vmt_by_age, by = "age")

current_veh_t0_VMT_high <- current_veh_t0 %>% select(-low, -vmt, high_VMT_prop) %>% rename(vmt = "high")
current_veh_t0_VMT_high$vmt_bucket <- "high"


current_veh_t0_VMT_low <- current_veh_t0 %>% select(-high, -vmt, high_VMT_prop) %>% rename(vmt = "low")
current_veh_t0_VMT_low$vmt_bucket <- "low"

current_veh_t0_VMT <- rbind(current_veh_t0_VMT_high, current_veh_t0_VMT_low)
current_veh_t0_VMT$n <- current_veh_t0_VMT$n/2

current_veh_t0_VMT <- current_veh_t0_VMT %>% rename(production_year = "year")

file_path <- "~/repos/tri_mac/counterfactual_calculator/ekiden/data/current_veh_t0_VMT.csv"
write.csv(current_veh_t0_VMT, file_path, row.names = FALSE) 
