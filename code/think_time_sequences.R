library(dplyr)

sequences <- read.csv("think_time_sequences.csv")

sequenceStats <- sequences %>% group_by (task,userid) %>%
  summarize(mean_sl = mean(sequenceLength), min_sl = min(sequenceLength), max_sl = max(sequenceLength), med_sl = median(sequenceLength)) 

print(sequenceStats %>% group_by(task) %>% summarize(med_mean = median(mean_sl),
  mean_mean = mean(mean_sl),
  mean_med = mean(med_sl), med_med = median(med_sl),
  med_max = median(max_sl), med_min = median(min_sl),
  max_max = max(max_sl), min_min = min(min_sl)))
