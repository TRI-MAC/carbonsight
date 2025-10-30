library(dplyr)
library(reshape2)
library(ggplot2)
library(stringr)


current_year <- 2024


# l_100km	l_100kme	uf	weight_lbs	ev_range	batt_kwh


# STEP 1. GET VEH  TECH SPECS FROM .GOV
veh_specs_df <- read.csv("~/Downloads/veh_spec_data/veh_specs_merged.csv") %>% filter(year >= 1980)

nrow(veh_specs_df)

drop_vec <- c("awd", "rwd", "fwd", "2wd", "4wd", "xdrive", "4matic", "wagon", "cabrio", 
              "quattro","hybrid", "coupe","convertible","pickup", "c15","k15", "2dr", "4dr", "5dr", 
              "luxury", "doors", "door")

drop_strings <- function(string_vec, drop_vec) {
  # replaces the sub_strings in drop_vec with empty spaces
  output_vec <- string_vec %>% tolower()
  for (item in drop_vec) {
    output_vec <- output_vec %>% str_replace_all(item, "")
  }
  output_vec <- output_vec %>% trimws()
  return(output_vec)
}

veh_specs_df$model <-  veh_specs_df$model %>%  drop_strings(drop_vec)

veh_specs_df <- veh_specs_df[!duplicated(veh_specs_df[c("year", "make", "model", "powertrain")]),]
nrow(veh_specs_df)


# STEP 2. GET SALES WEIGHTS FROM MARKETING COMPANY
da_look_up <- read.csv("~/repos/tri_mac/counterfactual_calculator/ekiden/data/da_look_up.csv") 

veh_specs_look_up <- veh_specs_df %>% group_by(make, model, powertrain, year) %>% 
  summarize(veh_specs_n = n(), mpg = mean(mpg, na.rm = TRUE), mpge = mean(mpge, na.rm = TRUE), uf = mean(uf, na.rm = TRUE), l_100km = mean(l_100km, na.rm = TRUE),
            l_100kme = mean(l_100kme, na.rm = TRUE), weight_lbs = mean(weight_lbs, na.rm = TRUE), ev_range = mean(ev_range, na.rm = TRUE), batt_kwh = mean(batt_kwh, na.rm = TRUE))

veh_specs_look_up$powertrain <- veh_specs_look_up$powertrain %>% recode(ev = "bev")

da_look_up$veh_specs_model <- NA
da_look_up$veh_specs_min_dist<- NA
da_look_up$veh_specs_matches<- NA
da_look_up$veh_specs_all_matches <- NA

for (i in 1:nrow(da_look_up)){
  if (i%%500 == 0) {print(i)}
  current_make <- da_look_up$make[i]
  current_year <- da_look_up$year[i]
  current_model <- da_look_up$model[i]
  current_powertrain <- da_look_up$powertrain[i]
  sub_veh_df <- veh_specs_look_up %>% filter(make == current_make, powertrain == current_powertrain, year == current_year)
  if(nrow(sub_veh_df) == 0) {
    next
  }
  
  ###
  veh_df_models <- unique(sub_veh_df$model)
  distances <- stringdist(current_model, veh_df_models, method = 'cosine')
  min_distances <- distances[distances == min(distances)]
  
  da_look_up$veh_specs_min_dist[i] <- min(distances)
  da_look_up$veh_specs_matches[i] <- length(min_distances)
  da_look_up$veh_specs_all_matches[i] <- veh_df_models[distances == min(distances)] %>% paste0(collapse ="; ")
  
  if(length(min_distances) > 1) {
    da_look_up$veh_specs_model[i] <- veh_df_models[distances == min(distances)][1]
    
  } else {
    da_look_up$veh_specs_model[i] <- veh_df_models[distances == min(distances)]
  }
  
  #ev_phev_df$model_modified[i] <- veh_df_models[which.min(distances)]
  #x <- c(x, (paste0(current_model, ": ",ev_phev_df$model_modified[i])))
}
buff_df <-  da_look_up 



da_look_up$n[da_look_up$veh_specs_matches == 1] %>% sum(na.rm = TRUE)
da_look_up <- da_look_up %>% filter(veh_specs_matches == 1)


# STEP 3. COMPUTE WEIGHTED VEH SPECS 


merged_data_axles_veh_specs_df <- merge(da_look_up, veh_specs_look_up,
                                        by.x = c("year", "make", "powertrain", "veh_specs_model"),
                                        by.y = c("year", "make", "powertrain", "model"), 
                                        all.x = TRUE, all.y = FALSE)

n_per_year_and_powertrain <- merged_data_axles_veh_specs_df %>% group_by(year, powertrain) %>% summarize(n_year_powertrain = sum(n))
n_per_year <- merged_data_axles_veh_specs_df %>% group_by(year) %>% summarize(n_year = sum(n))
n_per_year_and_powertrain <- n_per_year_and_powertrain %>% merge(n_per_year, by = "year")
n_per_year_and_powertrain$prop_powertrain <- (n_per_year_and_powertrain$n_year_powertrain/n_per_year_and_powertrain$n_year)

merged_data_axles_veh_specs_df <- merged_data_axles_veh_specs_df %>% merge(n_per_year_and_powertrain, by = c("year", "powertrain"))
merged_data_axles_veh_specs_df$weight <- merged_data_axles_veh_specs_df$n / merged_data_axles_veh_specs_df$n_year_powertrain

#merged_data_axles_veh_specs_df$mpg_weighted <- merged_data_axles_veh_specs_df$weight*merged_data_axles_veh_specs_df$mpg
#merged_data_axles_veh_specs_df$mpge_weighted <- merged_data_axles_veh_specs_df$weight*merged_data_axles_veh_specs_df$mpge

merged_data_axles_veh_specs_df$l_100km_weighted <- merged_data_axles_veh_specs_df$weight*merged_data_axles_veh_specs_df$l_100km
merged_data_axles_veh_specs_df$l_100kme_weighted <- merged_data_axles_veh_specs_df$weight*merged_data_axles_veh_specs_df$l_100kme



merged_data_axles_veh_specs_df$uf_weighted <- merged_data_axles_veh_specs_df$weight*merged_data_axles_veh_specs_df$uf
merged_data_axles_veh_specs_df$weight_lbs_weighted <- merged_data_axles_veh_specs_df$weight*merged_data_axles_veh_specs_df$weight_lbs
merged_data_axles_veh_specs_df$ev_range_weighted <- merged_data_axles_veh_specs_df$weight*merged_data_axles_veh_specs_df$ev_range
merged_data_axles_veh_specs_df$batt_kwh_weighted <- merged_data_axles_veh_specs_df$weight*merged_data_axles_veh_specs_df$batt_kwh

file_path <- "~/Downloads/fleet_mix_data/merged_data_axles_veh_specs_df.csv"
#write.csv(merged_data_axles_veh_specs_df, file_path, row.names = FALSE) 
#merged_data_axles_veh_specs_df <- read.csv(file_path, header = TRUE)

veh_specs_merged_df <- merged_data_axles_veh_specs_df %>% group_by(year, powertrain) %>% 
  summarise(l_100km = sum(l_100km_weighted, na.rm = TRUE),
            l_100kme = sum(l_100kme_weighted, na.rm = TRUE),
            uf = sum(uf_weighted, na.rm = TRUE),
            weight_lbs = sum(weight_lbs_weighted, na.rm = TRUE),
            ev_range = sum(ev_range_weighted, na.rm = TRUE),
            batt_kwh= sum(batt_kwh_weighted, na.rm = TRUE)) %>%
  merge(n_per_year_and_powertrain, by = c("year", "powertrain"))




buff_df <- expand.grid(powertrain = c("icev", "hev",  "bev",  "phev"), year = c(1974:2024))
veh_specs_merged_df <- veh_specs_merged_df %>%  merge(buff_df, by = c("year", "powertrain"), all = TRUE)

veh_specs_merged_df[(veh_specs_merged_df$year < 1984 & veh_specs_merged_df$powertrain == "icev"),3:10] <- veh_specs_merged_df[(veh_specs_merged_df$year == 1984 & veh_specs_merged_df$powertrain == "icev"),3:10] 

# compute mpgs from km_100km due to potential issues with weighting 
veh_specs_merged_df$mpg <- 235.21/veh_specs_merged_df$l_100km
veh_specs_merged_df$mpge<- 235.21/veh_specs_merged_df$l_100kme
veh_specs_merged_df$mpg[is.infinite(veh_specs_merged_df$mpg)] <- NA
veh_specs_merged_df$mpge[is.infinite(veh_specs_merged_df$mpge)] <- NA


veh_specs_merged_df %>% ggplot(aes(x = year, y=weight_lbs, group = powertrain)) +
  geom_line(aes(color=powertrain))



# STEP 4. GET POWERTRAIN PROPORTIONS FROM SALES DATA FROM *.GOV

# the current fleet mix is probably not accurate, use historic from government and assume similar life for different powertrains

# get historical sales
sales_df <- read.csv("~/Downloads/fleet_mix_data/vehicle_sales_merged.csv") %>% select(year, hev, phev, bev, total, icev)
sales_df$hev_prop <- sales_df$hev/sales_df$total
sales_df$phev_prop <- sales_df$phev/sales_df$total
sales_df$bev_prop <- sales_df$bev/sales_df$total
sales_df$icev_prop <- sales_df$icev/sales_df$total

# sales add 2024
# https://www.eia.gov/todayinenergy/detail.php?id=63904
sales_df <- dplyr::bind_rows(sales_df, data.frame(year = c(2024)))
sales_df[sales_df$year == 2024, c("hev_prop", "phev_prop", "bev_prop", "icev_prop")] <- c(0.1, 0.02, 0.09, 0.79)
# 

sales_df_casted <- sales_df %>% 
  select(year, hev_prop, phev_prop, bev_prop, icev_prop, bev_prop) %>% melt(id=c("year"), variable.name = "powertrain") %>% 
  rename(powertrain_prop = "value")

sales_df_casted$powertrain <- sales_df_casted$powertrain %>% str_replace_all("_prop", "")

veh_specs_merged_df <- veh_specs_merged_df %>% rename(prop_powertrain_da = "prop_powertrain")

veh_specs_merged_df <- veh_specs_merged_df %>% merge(sales_df_casted, by = c("year", "powertrain"), all = TRUE)

plot(veh_specs_merged_df$prop_powertrain_da, veh_specs_merged_df$powertrain_prop) # the correlation is quite strong, but I will use the sales porportions
veh_specs_merged_df <- veh_specs_merged_df %>% rename(proportion = "powertrain_prop") %>% select(-prop_powertrain_da)
veh_specs_merged_df$proportion[is.na(veh_specs_merged_df$proportion)] <- 0
veh_specs_merged_df$proportion[(veh_specs_merged_df$year < 1999 & veh_specs_merged_df$powertrain == "icev")] <- 1




file_path <- "~/repos/tri_mac/counterfactual_calculator/ekiden/data/veh_specs_merged.csv"
write.csv(veh_specs_merged_df, file_path, row.names = FALSE) 

