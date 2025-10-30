# survival model: https://baker.utk.edu/wp-content/uploads/2022/07/A-Statistical-Analysis-of-Trends-in-Light-duty-Vehicle-Scrappage-and-Survival-2003–2020.Report.pdf

library(dplyr)
library(reshape2)
library(ggplot2)
library(stringr)

max_age <- 50

# this equation is modified based on author's communication
g17a <- function(x,m,sigma,K,A){
  out = K/(sigma*(exp((x-m)/2*sigma)+exp(-(x-m)/2*sigma))^2+A)
  return(out)
}

#compute scrappage for three classes of vehicles, year 2020 
ages = 0:max_age
output_cars = c()
output_trucks = c()
for (age in ages){
  output_cars = c(output_cars, g17a(x = age, m = 23.51246, sigma = .1693117, K = 0.06978, A = -0.3252457))
  output_trucks = c(output_trucks, g17a(x = age, m = 23.67686, sigma = -0.24794, K = -0.21376, A = -0.39929))
}
output <- (output_trucks+output_cars)/2

df = data.frame(ages = ages, scrappage = output)
# put a hard stop after 50
df$scrappage[nrow(df)] <- 1

# set age 0 to survive for sure
df$lag1_scrappage <- lag(df$scrappage, 1)
df$lag1_scrappage[1] <- 0
df$survival =  cumprod(1-df$lag1_scrappage)
plot(df$survival)


base_disposal_rate <- sum(df$survival*df$scrappage)/sum(df$survival)

start_n <- 100
df$freq <- df$survival*start_n/sum(df$survival)
df$year <- 0

advance_1y <- function(df, renewal_rate, diposal_rate){
  base_disposal_rate <- sum(df$freq*df$scrappage)/sum(df$freq)
  #df$scrappage <- ((diposal_rate/base_disposal_rate)*df$scrappage*df$freq)/sum(df$scrappage)

  renewal_n <- sum(df$freq)*renewal_rate
  disposal_n <- sum(df$freq)*diposal_rate
  
  print(disposal_n)
  df$base_disposed_freq <- df$freq*df$scrappage
  scaler <- (disposal_n - df$freq[nrow(df)])/sum(df$base_disposed_freq[1:(nrow(df)-1)]) # correct for the last row
  df$scaled_disposed_freq <- df$base_disposed_freq*scaler
  df$scaled_disposed_freq[nrow(df)] <- df$freq[nrow(df)]
  df$scaled_scrappage <- df$scaled_disposed_freq/df$freq
  
  df_new <- df[,c("ages", "scaled_disposed_freq", "freq")] 
  df_new$freq <- df_new$freq - df_new$scaled_disposed_freq
  df_new$ages <- df_new$ages + 1
  df_new <- rbind(df_new[1,],df_new )
  df_new$ages[1] <- 0
  df_new$freq[1] <- renewal_n
  df_new <- df_new[1:(nrow(df_new)-1),]
  
  df$year <- df$year + 1
  df_out <- merge(df[,c("scrappage","scaled_scrappage", "ages", "survival", "year")], df_new[,c("ages", "freq")], by = "ages")
  return(df_out)
}

renewal_rate = base_disposal_rate

df_new <- df
df_all <- data.frame()
for (year in 1:10) {
  print(year)
  df_new <- advance_1y(df_new, renewal_rate, base_disposal_rate)
  df_all <- rbind(df_all, df_new)
  
  total_survived <- sum(df_new$freq*(1-df_new$scrappage), na.rm = TRUE)/sum(df_new$freq)
  total_disposed <- sum(df_new$freq*df_new$scaled_scrappage)/sum(df_new$freq)
  first_entry <- df_new$freq[1]/sum(df_new$freq)
  print(paste0("total_disposed:", total_disposed, "; first_entry:",  first_entry))
  
}

df_all %>% group_by(year) %>%
  summarise(total_freq = sum(freq),
            mean_age = sum(freq*ages)/sum(freq))

df_all %>% ggplot(aes(x = ages, y = freq, color = as.factor(year))) +
  geom_line()


# save survival function
folder_path <- "~/repos/tri_mac/counterfactual_calculator/ekiden/data/"
file_path <- paste0(folder_path, "survival_function_greene.csv")
#write.csv(df, file_path, row.names = FALSE)
