library(MASS)
library(dplyr)
library(lme4)
library(lsmeans)
set.seed(101)

ttdata <- read.csv('think_time.csv', sep=',')

############### think time distribution ###############

# tried to use the glm function but it just didn't work properly?
if(FALSE){
print("######  [OLD] think time distribution ######");
res <- ttdata %>% filter(currThinkTime <= 120) %>% with(hist(currThinkTime,breaks=seq(0,120,250)))
#print(res)
x <- head(res$breaks, -1)
pow.x <- x^2
logx <- log(x)
y <- res$counts
n1<-glm( y~x+pow.x, family = poisson (link = "log") )
y2 <- predict(n1, data.frame(x = x,pow.x=pow.x),type="response")
plot(x,y)
#lines(x,n1$fit, col = "red")
lines(x,y2, col = "red")
#plot(logx,y)
#lines(logx,y2)
}

if(FALSE) {
# using MLE to fit
#data <- ttdata %>% filter(currThinkTime <= 120 & dataset=="birdstrikes1")
print("######  think time distribution ######");
data <- ttdata %>% filter(currThinkTime <= 120)
fit <- fitdistr(data$currThinkTime*1000,densfun="Poisson")
hist(data$currThinkTime*1000,breaks=seq(0,120*1000,0.5*1000), prob=TRUE)
curve(dnorm(x, mean=fit$estimate, sd=sqrt(fit$estimate)), col="red", lwd=2, add=T)
print(fit$estimate)
}

############### think time  model -- task and dataset ###############
if(FALSE) {
print("######  think time model -- task and dataset ######");
ttdata$timebin <- floor(ttdata$currThinkTime*2)
data2 <- ttdata %>% filter(!is.na(currThinkTime)) %>% group_by(dataset,task,userid,timebin) %>% summarise(rowCount = n())

# effect of task and dataset
# Note: fails to converge for random slope+intercept (1+task|userid). using intercepts only for userid.
m0 = glmer(rowCount ~ 1 + (1|userid), family=poisson(link=log), data=data2)
m1 = glmer(rowCount ~ 1 + task + (1|userid), family=poisson(link=log), data=data2)
m2 = glmer(rowCount ~ 1 + task + dataset + (1|userid), family=poisson(link=log), data=data2)
#print("######  think time -- task and dataset:  m0 ######");
#print(summary(m0))
#print("######  think time -- task and dataset: m1 ######");
#print(summary(m1))
#print("######  think time -- task and dataset: m2 ######");
#print(summary(m2))
print("######  think time -- task and dataset: anova(m0,m1,m2) ######");
print(anova(m0, m1, m2));
}

############### total queries  model -- task and dataset ###############
if(FALSE) {
print("######  total queries model -- task and dataset ######");
m0 = glmer(totalQueries ~ 1 + (1|userid), family=poisson(link=log), data=ttdata)
m1 = glmer(totalQueries ~ 1 + task + (1|userid), family=poisson(link=log), data=ttdata)
m2 = glmer(totalQueries ~ 1 + task + dataset + (1|userid), family=poisson(link=log), data=ttdata)
#print("######  total queries -- task and dataset:  m0 ######");
#print(summary(m0))
#print("######  total queries -- task and dataset: m1 ######");
#print(summary(m1))
#print("######  total queries -- task and dataset: m2 ######");
#print(summary(m2))
print("######  total queries -- task and dataset: anova(m0, m1,m2) ######");
print(anova(m0, m1, m2));
}

############### next total queries  model -- task and dataset ###############
if(FALSE) {
print("######  next total queries model -- task and dataset ######");
m0 = glmer(nextTotalQueries ~ 1 + (1|userid), family=poisson(link=log), data=ttdata)
m1 = glmer(nextTotalQueries ~ 1 + task + (1|userid), family=poisson(link=log), data=ttdata)
m2 = glmer(nextTotalQueries ~ 1 + task + dataset + (1|userid), family=poisson(link=log), data=ttdata)
#print("######  next total queries:  m0 -- task and dataset ######");
#print(summary(m0))
#print("######  next total queries: m1 -- task and dataset ######");
#print(summary(m1))
#print("######  next total queries: m2 -- task and dataset ######");
#print(summary(m2))
print("######  next total queries -- task and dataset: anova(m0, m1,m2) ######");
print(anova(m0, m1, m2));
}

############### next total queries model -- other variables ###############
# Note: seems that state size and interaction type do not affect the model, however the current think time does affect the next think time
if(FALSE) {
print("######  next total queries model -- other variables ######");
m0 = lmer(nextTotalQueries ~ 1 + (1+totalQueries|task) + (1+totalQueries|dataset) + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ttdata)
m1 = lmer(nextTotalQueries ~ 1 + totalQueries + (1+totalQueries|task) + (1+totalQueries|dataset) + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ttdata)
m2 = lmer(nextTotalQueries ~ 1+ totalQueries  + currThinkTime + (1+totalQueries|task) + (1+totalQueries|dataset) + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ttdata)
m3 = lmer(nextTotalQueries ~ 1 + totalQueries + stateSize + currThinkTime + (1+totalQueries|task) + (1+totalQueries|dataset) + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ttdata)
m4 = lmer(nextTotalQueries ~ 1 + totalQueries + interactionTypeHighlevel + stateSize + currThinkTime + (1+totalQueries|task) + (1+totalQueries|dataset) + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ttdata)
print("######  next total queries -- other variables: anova(m0, m1, m2, m3, m4) ######");
print(anova(m0, m1, m2, m3, m4));
}

############### interactions before queries model -- task and dataset ###############
if(FALSE) {
print("######  interactions before queries model -- task and dataset ######");
ibqdata <- ttdata %>%  filter(totalQueries > 0)
m0 = glmer(interactionsBeforeQueries ~ 1 + (1|userid), family=poisson(link=log), data=ibqdata)
m1 = glmer(interactionsBeforeQueries ~ 1 + task + (1|userid), family=poisson(link=log), data=ibqdata)
m2 = glmer(interactionsBeforeQueries ~ 1 + task + dataset + (1|userid), family=poisson(link=log), data=ibqdata)
#print("######  interactions before queries -- task and dataset:  m0 ######");
#print(summary(m0))
#print("######  interactions before queries -- task and dataset: m1 ######");
#print(summary(m1))
#print("######  interactions before queries -- task and dataset: m2 ######");
#print(summary(m2))
print("######  interactions before queries -- task and dataset: anova(m0, m1,m2) ######");
print(anova(m0, m1, m2));
}

############### interactions before queries model -- other variables ###############
if(FALSE) {
print("######  interactions before queries model -- other variables ######");
ibqdata <- ttdata %>%  filter(totalQueries > 0)
m0 = lmer(interactionsBeforeQueries ~ 1 + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ibqdata)
m1 = lmer(interactionsBeforeQueries ~ 1 + currThinkTime + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ibqdata)
m2 = lmer(interactionsBeforeQueries ~ 1 + stateSize + currThinkTime + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ibqdata)
m3 = lmer(interactionsBeforeQueries ~ 1 + interactionTypeHighlevel + stateSize + currThinkTime + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ibqdata)

print("######  interactions before queries -- other variables: anova(m0, m1, m2, m3) ######");
print(anova(m0, m1, m2, m3));
}
# [1] "######  interactions before queries model -- other variables ######"
# [1] "######  interactions before queries -- other variables: anova(m0, m1, m2, m3) ######"
# refitting model(s) with ML (instead of REML)
# Data: ttdata
# Models:
# m0: interactionsBeforeQueries ~ 1 + (1 + stateSize | task) + (1 + 
# m0:     stateSize | dataset) + (1 + currThinkTime | task) + (1 + 
# m0:     currThinkTime | dataset) + (1 | userid)
# m1: interactionsBeforeQueries ~ 1 + currThinkTime + (1 + stateSize | 
# m1:     task) + (1 + stateSize | dataset) + (1 + currThinkTime | 
# m1:     task) + (1 + currThinkTime | dataset) + (1 | userid)
# m2: interactionsBeforeQueries ~ 1 + stateSize + currThinkTime + (1 + 
# m2:     stateSize | task) + (1 + stateSize | dataset) + (1 + currThinkTime | 
# m2:     task) + (1 + currThinkTime | dataset) + (1 | userid)
# m3: interactionsBeforeQueries ~ 1 + interactionTypeHighlevel + stateSize + 
# m3:     currThinkTime + (1 + stateSize | task) + (1 + stateSize | 
# m3:     dataset) + (1 + currThinkTime | task) + (1 + currThinkTime | 
# m3:     dataset) + (1 | userid)
#    Df   AIC   BIC logLik deviance   Chisq Chi Df Pr(>Chisq)    
# m0 15 22276 22370 -11123    22246                              
# m1 16 22239 22339 -11104    22207  38.734      1  4.856e-10 ***
# m2 17 22290 22396 -11128    22256   0.000      1          1    
# m3 23 22122 22266 -11038    22076 180.273      6  < 2.2e-16 ***
# ---
# Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1
# There were 16 warnings (use warnings() to see them)


############### curr think time duration model -- task and dataset ###############
if(FALSE) {
print("######  curr think time duration model -- task and dataset ######");
m0 = lmer(currThinkTime ~ 1 + (1|userid), data=ttdata)
m1 = lmer(currThinkTime ~ 1 + task + (1|userid), data=ttdata)
m2 = lmer(currThinkTime ~ 1 + task + dataset + (1|userid), data=ttdata)
#print("######  curr think time duration -- task and dataset:  m0 ######");
#print(summary(m0))
#print("######  curr think time duration -- task and dataset: m1 ######");
#print(summary(m1))
#print("######  curr think time duration -- task and dataset: m2 ######");
#print(summary(m2))
print("######  curr think time duration -- task and dataset: anova(m0, m1,m2) ######");
print(anova(m0, m1, m2));
}

############### curr think time duration model -- other variables ###############
if(FALSE) {
print("######  curr think time duration model -- other variables ######");
m0 = lmer(currThinkTime ~ 1 + (1+stateSize|task) + (1+stateSize|dataset) + (1|userid), data=ttdata)
m1 = lmer(currThinkTime ~ 1 + stateSize + (1+stateSize|task) + (1+stateSize|dataset) + (1|userid), data=ttdata)
m2 = lmer(currThinkTime ~ 1 + interactionTypeHighlevel + stateSize + (1+stateSize|task) + (1+stateSize|dataset) + (1|userid), data=ttdata)
print("######  curr think time duration -- other variables: anova(m0, m1, m2) ######");
print(anova(m0, m1, m2));
print(lsmeans(m2, list(pairwise ~ interactionTypeHighlevel), adjust = "tukey"))
}

############### next think time duration model -- task and dataset ###############
if(TRUE) {
print("######  next think time duration model -- task and dataset ######");
m0 = lmer(nextThinkTime ~ 1 + (1|userid), data=ttdata)
m1 = lmer(nextThinkTime ~ 1 + task + (1|userid), data=ttdata)
m2 = lmer(nextThinkTime ~ 1 + task + dataset + (1|userid), data=ttdata)
#print("######  next think time duration -- task and dataset:  m0 ######");
#print(summary(m0))
#print("######  next think time duration -- task and dataset: m1 ######");
#print(summary(m1))
#print("######  next think time duration -- task and dataset: m2 ######");
#print(summary(m2))
print("######  next think time duration -- task and dataset: anova(m0, m1,m2) ######");
print(anova(m0, m1, m2));
print(lsmeans(m2, list(pairwise ~ task), adjust = "tukey"))
}

############### next think time duration model -- other variables ###############
# Note: seems that state size and interaction type do not affect the model, however the current think time does affect the next think time
if(FALSE) {
print("######  next think time duration model -- other variables ######");
m0 = lmer(nextThinkTime ~ 1 + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ttdata)
m1 = lmer(nextThinkTime ~ 1 + currThinkTime + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ttdata)
m2 = lmer(nextThinkTime ~ 1 + stateSize + currThinkTime + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ttdata)
m3 = lmer(nextThinkTime ~ 1 + interactionTypeHighlevel + stateSize + currThinkTime + (1+stateSize|task) + (1+stateSize|dataset) + (1+currThinkTime|task) + (1+currThinkTime|dataset) + (1|userid), data=ttdata)
print("######  next think time duration -- other variables: anova(m0, m1, m2, m3) ######");
print(anova(m0, m1, m2, m3));
}
