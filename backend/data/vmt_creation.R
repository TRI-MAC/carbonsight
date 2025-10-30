library(dplyr)
library(reshape2)
library(ggplot2)
library(stringr)


current_year <- 2024

# compute low and high mileage driver groups
folder_path <- "~/Downloads/NHTS_data/2017/survey_data_csv/"
vehpub_df <- read.csv(paste0(folder_path, 'vehpub.csv'))
vehpub_df <- vehpub_df %>% filter(VEHAGE >= 0)
vehpub_df <- vehpub_df %>% filter(BESTMILE >= 0)

vehpub_df <- vehpub_df[!is.na(vehpub_df$VEHAGE),]
vehpub_df <- vehpub_df[!is.na(vehpub_df$BESTMILE),]

#plot(vehpub_df$VEHAGE, vehpub_df$VEHYEAR)

vehpub_df_by_age <- vehpub_df %>% group_by(VEHAGE) %>%
  summarise(mean_VMT = mean(BESTMILE, na.rm = TRUE), 
            median_VMT = median(BESTMILE, na.rm = TRUE))

vehpub_df <- merge(vehpub_df, vehpub_df_by_age, by = "VEHAGE")

vehpub_df$VMT_group <- NA
vehpub_df$VMT_group <- ifelse(vehpub_df$BESTMILE < median(vehpub_df$median_VMT, na.rm = TRUE), "low", vehpub_df$VMT_group)
vehpub_df$VMT_group <- ifelse(vehpub_df$BESTMILE >= median(vehpub_df$median_VMT, na.rm = TRUE), "high", vehpub_df$VMT_group)

vehpub_df_by_age_group <- vehpub_df %>% group_by(VEHAGE, VMT_group) %>%
  summarise(mean_VMT = mean(BESTMILE, na.rm = TRUE)) %>% dcast(VEHAGE~VMT_group, value.var = "mean_VMT")

vmt_by_age <- merge(vehpub_df_by_age_group, vehpub_df_by_age, by = "VEHAGE") %>% 
  rename("high_VMT" = "high", "low_VMT" = "low")

vmt_by_age$high_VMT_ratio <- vmt_by_age$high_VMT/(vmt_by_age$high_VMT + vmt_by_age$low_VMT)
missing_years_df <- data.frame(VEHAGE = c(0, 33:39, 41:50))
missing_years_df$low_VMT <- NA
missing_years_df$high_VMT <- NA
missing_years_df$mean_VMT <- NA
missing_years_df$median_VMT <- NA
missing_years_df$high_VMT_ratio <- NA

vmt_by_age <- rbind(vmt_by_age, missing_years_df)

plot(vmt_by_age$VEHAGE ,vmt_by_age$high_VMT_ratio)

plot(vmt_by_age$VEHAGE ,vmt_by_age$high_VMT)
plot(vmt_by_age$VEHAGE ,vmt_by_age$low_VMT)
plot(vmt_by_age$VEHAGE ,vmt_by_age$mean_VMT)

cor.test(vmt_by_age$VEHAGE ,vmt_by_age$high_VMT)
cor.test(vmt_by_age$VEHAGE ,vmt_by_age$low_VMT)


lm_mean <- lm(mean_VMT ~ VEHAGE, data = vmt_by_age)
vmt_by_age$mean_VMT_est <-  predict(lm_mean, vmt_by_age)
summary(lm_mean)

lm_ratio <- lm(high_VMT_ratio ~ VEHAGE, data = vmt_by_age)
vmt_by_age$high_VMT_ratio_est <-  predict(lm_ratio, vmt_by_age)
summary(lm_ratio)
vmt_by_age$high_VMT_est <- vmt_by_age$mean_VMT_est*vmt_by_age$high_VMT_ratio_est*2
vmt_by_age$low_VMT_est <- vmt_by_age$mean_VMT_est*(1-vmt_by_age$high_VMT_ratio_est)*2


plot(vmt_by_age$VEHAGE, vmt_by_age$high_VMT_ratio)
plot(vmt_by_age$VEHAGE, vmt_by_age$mean_VMT_est)

vmt_by_age <- vmt_by_age %>% select(VEHAGE, low_VMT_est, high_VMT_est, mean_VMT_est, high_VMT_ratio_est) %>%
  rename(age = "VEHAGE", low = "low_VMT_est", high = "high_VMT_est", vmt = "mean_VMT_est", high_VMT_prop = "high_VMT_ratio_est")

# save survival function
folder_path <- "~/repos/tri_mac/counterfactual_calculator/backend/data/"
file_path <- paste0(folder_path, "vmt_by_age.csv")
#write.csv(vmt_by_age, file_path, row.names = FALSE)

# compute VMT for fleet which is not being renewed
# survival function 
surv_df <- read.csv(paste0(folder_path, "survival_function_greene.csv")) %>% rename("age" = "ages")

merged_df <- merge(surv_df[c("survival", "age")], vmt_by_age, by = "age")
merged_df <- merged_df %>% arrange(age)
merged_df$vmt_partial <- NA
n = nrow(merged_df)
for (i in 1:n){
  merged_df$vmt_partial[i] = sum(merged_df[i:n,"vmt"]*merged_df[i:n,"survival"])/sum(merged_df[i:n,"survival"])
}

# add vmt_partial 
vmt_by_age <- merge(vmt_by_age, merged_df[c("age", "vmt_partial")], on = "age") %>% arrange(age)
file_path <- paste0(folder_path, "vmt_by_age.csv")
#write.csv(vmt_by_age, file_path, row.names = FALSE)



