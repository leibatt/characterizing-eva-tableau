library(lme4)
library(lsmeans)

## LOAD DATA, REMOVE ZERO NODE TREES
data <- read.csv('graph_analysis_per_tree.csv', sep='|')
data <- data[data$totalNodes > 0,]
data$ratio <- data$leaves / data$maxDepth

## NORMALIZED MAX DEPTH (Depth)
m0 <- lmer(maxDepth ~ (task|userid) + (task|dataset), data=data)
m1 <- lmer(maxDepth ~ task + (task|userid) + (task|dataset), data=data)
print(anova(m0, m1))
#lsmeans(m1, list(pairwise ~ task), adjust = "tukey")
# Models:
# m0: maxDepth ~ (task | userid) + (task | dataset)
# m1: maxDepth ~ task + (task | userid) + (task | dataset)
#    Df     AIC     BIC logLik deviance  Chisq Chi Df Pr(>Chisq)
# m0 22 -97.063 -25.513 70.532  -141.06
# m1 25 -95.941 -14.634 72.970  -145.94 4.8779      3      0.181
# No significant effect!

## ASPECT RATIO (Breadth / Depth)
data2 <-data[is.finite(data$ratio),]
m0 <- lmer(ratio ~ (task|userid) + (task|dataset), data=data2)
m1 <- lmer(ratio ~ task + (task|userid) + (task|dataset), data=data2)
print(anova(m0, m1))
#lsmeans(m1, list(pairwise ~ task), adjust = "tukey")
# Models:
# m0: ratio ~ (task | userid) + (task | dataset)
# m1: ratio ~ task + (task | userid) + (task | dataset)
#    Df    AIC    BIC  logLik deviance  Chisq Chi Df Pr(>Chisq)
# m0 22 285.52 357.07 -120.76   241.53
# m1 25 289.36 370.66 -119.68   239.35 2.1693      3      0.538

## NORMALIZED MAX BREADTH (Depth)
m0 <- lmer(maxBranchingFactor ~ (task|userid) + (task|dataset), data=data)
m1 <- lmer(maxBranchingFactor ~ task + (task|userid) + (task|dataset), data=data)
print(anova(m0, m1))



