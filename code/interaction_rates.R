library(lme4)
library(lsmeans)
library(plyr)

# header
#dataset,sheets_strategy,task,total_columns,total_dimensions,total_interactions,total_measures,total_minutes,total_new_columns,total_new_columns_prompt_only,total_sheets,userid
#birdstrikes1,,t4,9,5,39,4,8.833483333333334,5,1,25
#birdstrikes1,,t4,6,4,21,2,9.131166666666667,4,5,13
data <- read.csv("open_ended_inputs.csv")
# average interactions performed per minute
data$interaction_rate <- data$total_interactions / data$total_minutes

cat("################ TASK(interaction_rate): Linear Mixed Effects Model ################","\n",sep="")
m0 <- lmer(interaction_rate ~ (task|userid) + (1|dataset), data=data)
m1 <- lmer(interaction_rate ~ task + (task|userid) + (1|dataset), data=data)
print(anova(m0, m1))
print(lsmeans(m1, list(pairwise ~ task), adjust = "tukey"))
