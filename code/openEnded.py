import csv
import numpy as np
import json
from core import datasets,tasks,columnInfo, baseColumns, usersPerDataset, writeResults,getColumnType

def massageStats(res):
  allUniqueSheets = res['allUniqueSheets']
  #allUniqueSheets = json.load(open('all_unique_sheets.json'))
  orderings = res['orderings']
  #orderings = json.load(open('column_orderings.json'))
  interactions = res['interactions']
  #interactions = json.load(open('total_interactions.json'))

  #dataset,offCampus,task,toolExpertise,trimmedTaskDuration,userid
  durations = {}
  with open('user_task_subtask_info_withtiming.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
      dataset = row['dataset']
      task = row['task']
      user = row['userid']
      duration = row['trimmedTaskDuration']
      if dataset not in durations:
        durations[dataset] = {}
      if task not in durations[dataset]:
        durations[dataset][task] = {}
      durations[dataset][task][user] = duration
  
  totalUsers = {}
  for dataset in usersPerDataset:
    for user in usersPerDataset[dataset]:
      expertise = 'N/A'
      if dataset not in totalUsers:
        totalUsers[dataset] = {'all':[]}
      if expertise not in totalUsers[dataset]:
        totalUsers[dataset][expertise] = []
      totalUsers[dataset][expertise].append(user)
      totalUsers[dataset]['all'].append(user)
  
  users = {}
  
  # to track different stats per user
  userObj = {'total_sheets':None,'total_columns':None,'total_measures':None,'total_dimensions':None,'total_new_columns':None,
    'total_new_columns_prompt_only':None,'total_interactions':None,'total_minutes':None,'sheets_strategy':None}
  # the set of unique columns that appear in first in the order of appearance sequences
  uniqueStarters = {}
  
  for dataset in datasets:
    uniqueStarters[dataset] = {}
    for task in tasks:
      uniqueStartingCols = []
      # all columns analyzed for this task
      all_cols_task = []
      for te in ['N/A']:

        # compute stats for the total sheets used per users
        for obj in allUniqueSheets[dataset][task][te]:
          user = obj['user']
          if dataset not in users:
            users[dataset] = {}
          if task not in users[dataset]:
            users[dataset][task] = {}
          if user not in users[dataset][task]:
            users[dataset][task][user] = dict(userObj)
            users[dataset][task][user]['userid'] = user
            users[dataset][task][user]['dataset'] = dataset
            users[dataset][task][user]['task'] = task
          # total sheets used
          users[dataset][task][user]['total_sheets'] = len(obj['uniqueSheets'])
        # compute stats for the order of appearance sequences per user
        for obj in orderings[dataset][task][te]:
          user = obj['user']
          if dataset not in users:
            users[dataset] = {}
          if task not in users[dataset]:
            users[dataset][task] = {}
          if user not in users[dataset][task]:
            users[dataset][task][user] = dict(userObj)
            users[dataset][task][user]['userid'] = user
            users[dataset][task][user]['dataset'] = dataset
            users[dataset][task][user]['task'] = task
          # all columns analyzed for this user
          all_cols = []
          for c in obj['order']:
            if '+' in c:
              temp = c.split('+')
              for t in temp:
                if t not in all_cols:
                  all_cols.append(t)
                if t not in all_cols_task:
                  all_cols_task.append(t)
            else:
              if c not in all_cols:
                all_cols.append(c)
              if c not in all_cols_task:
                all_cols_task.append(c)
          if all_cols[0] not in uniqueStartingCols:
            uniqueStartingCols.append(all_cols[0])
          # total columns selected
          users[dataset][task][user]['total_columns'] = len(all_cols)
          # total measures selected
          users[dataset][task][user]['total_measures'] = len([1 for c in all_cols if columnInfo[dataset][c]['type'] == 'measure'])
          # total dimensions selected
          users[dataset][task][user]['total_dimensions'] = len([1 for c in all_cols if columnInfo[dataset][c]['type'] == 'dimension'])
          # previou columns analyzed
          prevCols = []
          # new columns not explored previously or in task prompt
          nCols = []
          # new columns not in task prompt
          nColsPromptOnly = []
          for prev in tasks[:tasks.index(task)]:
            prevUserList = orderings[dataset][prev][te]
            prevObj = prevUserList[[p['user'] for p in prevUserList].index(user)]
            prevOrder = prevObj['order']
            for c in prevOrder:
              toCheck = []
              if '+' in c:
                toCheck = c.split('+')
              else:
                toCheck.append(c)
              for tc in toCheck:
                if tc not in prevCols:
                  prevCols.append(tc)
          for c in all_cols:
            if c not in prevCols and c not in baseColumns[dataset][task]:
              nCols.append(c)
            if c not in baseColumns[dataset][task]:
              nColsPromptOnly.append(c)
          # total new columns that do not appear in task prompt or earlier tasks
          users[dataset][task][user]['total_new_columns'] = len(nCols)
          # total new columns that do not appear in task
          users[dataset][task][user]['total_new_columns_prompt_only'] = len(nColsPromptOnly)
        for obj in interactions[dataset][task][te]:
          user = obj['user']
          if dataset not in users:
            users[dataset] = {}
          if task not in users[dataset]:
            users[dataset][task] = {}
          if user not in users[dataset][task]:
            users[dataset][task][user] = dict(userObj)
            users[dataset][task][user]['userid'] = user
            users[dataset][task][user]['dataset'] = dataset
            users[dataset][task][user]['task'] = task
          # total interactions
          users[dataset][task][user]['total_interactions'] = obj['interactions']
          # total time in minutes
          users[dataset][task][user]['total_minutes'] = float(durations[dataset][task][user]) / 60.0
      uniqueStarters[dataset][task] = len(uniqueStartingCols)
      # calculate how many columns were analyzed for each task,
      # what fraction were measures, and what fraction were dimensions
      print dataset, task, "total cols analyzed across users:",len(all_cols_task),"fraction measures:",1.0*len([1 for c in all_cols_task if columnInfo[dataset][c]['type'] == 'measure'])/len(all_cols_task),"fraction dimensions:",1.0*len([1 for c in all_cols_task if columnInfo[dataset][c]['type'] == 'dimension'])/len(all_cols_task)
  
  # create csv file for open ended anlyses in R
  rows = []
  for dataset in datasets:
    for task in tasks:
      rows.append({'dataset':dataset,'task':task,'unique_starters':uniqueStarters[dataset][task]})
  writeResults('open_ended_starters_inputs.csv',rows)
  
  # create csv file for open ended analyses in R
  rows = []
  for dataset in users:
    for task in users[dataset]:
      for user in users[dataset][task]:
        rows.append(users[dataset][task][user])
  writeResults('open_ended_inputs.csv',rows)
  
# identifies the set of sheets used by this user for task and dataset
def calculateMultipleSheets(data,dataset,task,user):
  uniqueSheets = {}
  for row in data:
    if row['dataset'] == dataset and row['task'] == task and row['userid'] == user:
      cols = row['state']
      #cleanState = [state for state in row['state'] if state in columnInfo[dataset]]
      #if len(row['state']) > 0:
      if len(cols) > 0:
        uniqueSheets[row['sheet']] = True
  return sorted(uniqueSheets.keys())

# get the set of columns explored in order
def getOrderOfAppearance(data,dataset,task,user):
  order = []
  used = {}
  interactions = 0
  for row in data:
    if row['dataset'] == dataset and row['task'] == task and row['userid'] == user:
      interactions += 1
      toAdd = []
      for state in row['state']:
        if state not in order and state not in used and state in columnInfo[dataset]:
          toAdd.append(state)
          used[state] = True
      final = "+".join(toAdd)
      if len(final) > 0 and final not in order:
        order.append(final)
  #print ",".join([dataset,task,user])+":",order
  return order, interactions

def computeOpenEndedStats(data):
  # to track positions in order of appearance, for different data column types
  positionsMeasures = []
  positionsDimensions = []
  positionsDimensionsSpatiotemporal = []
  positionsDimensionsSpatial = []
  positionsDimensionsTemporal = []

  # to track edit distances between order of appearance between user and the task prompt
  editDistances = {}
  # to track the new columns that appear that are not in the task prompt
  newCols = {}
  # to count how many sheets people use, when more than one sheet is used
  uniqueSheets = {}
  # to count how many sheets people use for everyone
  allUniqueSheets = {}
  # to track order of appearance of columns
  orderings = {}
  # to track total interactions performed
  interactions = {}
  for dataset in usersPerDataset:
    for user in usersPerDataset[dataset]:
      # setup tracking objects
      if dataset not in editDistances:
        editDistances[dataset] = {}
        newCols[dataset] = {}
        uniqueSheets[dataset] = {}
        allUniqueSheets[dataset] = {}
        orderings[dataset] = {}
        interactions[dataset] = {}
      for task in tasks:
        if task not in editDistances[dataset]:
          editDistances[dataset][task] = {
            'N/A':[]
          }
          newCols[dataset][task] = {
            'N/A':[]
          }
          uniqueSheets[dataset][task] = {
            'N/A':[]
          }
          allUniqueSheets[dataset][task] = {
            'N/A':[]
          }
          orderings[dataset][task] = {
            'N/A':[]
          }
          interactions[dataset][task] = {
            'N/A':[]
          }
        # order of appearance of columns for this task, and total interactions done during this task
        order, tinteractions = getOrderOfAppearance(data, dataset,task,user)
        orderings[dataset][task]['N/A'].append({'user':user,'order':order})
        interactions[dataset][task]['N/A'].append({'user':user,'interactions':tinteractions})
        # get a list of the sheets the user seemed to use for this task
        uSheets = calculateMultipleSheets(data,dataset,task,user)
        if len(uSheets) > 1:
          uniqueSheets[dataset][task]['N/A'].append({'user':user,'uniqueSheets':uSheets})
        allUniqueSheets[dataset][task]['N/A'].append({'user':user,'uniqueSheets':uSheets})
        # number of columns in order of appearance that do not appear in task prompt
        nCols = getNewColumns(dataset,task,order)
        if len(nCols) > 0:
          newCols[dataset][task]['N/A'].append({'user':user,'newCols':nCols})

        #calculate edit distances
        if dataset == 'weather1' and task in ['t2','t3','t4']:
          d1 =levenshtein(baseColumns[dataset][task],order)
          d2 =levenshtein(baseColumns[dataset][task+'-2'],order)
          d3 = levenshtein(baseColumns[dataset][task+'-3'],order)
          editDistances[dataset][task]['N/A'].append({'user':user,'levenshtein':min(d1,d2,d3)})
        else:
          editDistances[dataset][task]['N/A'].append({'user':user,'levenshtein':levenshtein(baseColumns[dataset][task],order)})

        # compute the positions of the columns in the order of appearance, based on their characteristics
        positions = calculatePositions(dataset,order,
          lambda d,c: columnInfo[d][c]['type'] == 'dimension' 
            and (columnInfo[d][c]['temporal'] or columnInfo[d][c]['spatial']))
        positions = [{'dataset':dataset,'task':task,'userid':user,'position':p,'columnType':'dimension-temporal-spatial','toolExpertise':'N/A'} for p in positions]
        positionsDimensionsSpatiotemporal.extend(positions)
        positions = calculatePositions(dataset,order,
          lambda d,c: columnInfo[d][c]['type'] == 'dimension' 
            and columnInfo[d][c]['temporal'])
        positions = [{'dataset':dataset,'task':task,'userid':user,'position':p,'columnType':'dimension-temporal','toolExpertise':'N/A'} for p in positions]
        positionsDimensionsTemporal.extend(positions)
        positions = calculatePositions(dataset,order,
          lambda d,c: columnInfo[d][c]['type'] == 'dimension' 
            and columnInfo[d][c]['spatial'])
        positions = [{'dataset':dataset,'task':task,'userid':user,'position':p,'columnType':'dimension-spatial','toolExpertise':'N/A'} for p in positions]
        positionsDimensionsSpatial.extend(positions)
        positions = calculatePositions(dataset,order,
          lambda d,c: columnInfo[d][c]['type'] == 'dimension' 
            and not (columnInfo[d][c]['temporal'] or columnInfo[d][c]['spatial']))
        positions = [{'dataset':dataset,'task':task,'userid':user,'position':p,'columnType':'dimension-other','toolExpertise':'N/A'} for p in positions]
        positionsDimensions.extend(positions)
        positions = calculatePositions(dataset,order,
          lambda d,c: columnInfo[d][c]['type'] == 'measure' 
            and not (columnInfo[d][c]['temporal'] or columnInfo[d][c]['spatial']))
        positions = [{'dataset':dataset,'task':task,'userid':user,'position':p,'columnType':'measure','toolExpertise':'N/A'} for p in positions]
        positionsMeasures.extend(positions)

  # average position in order of appearance, for different data column types
  print 'mean positions measures:',np.mean([p['position'] for p in positionsMeasures])
  print 'mean positions dimensions-temporal:',np.mean([p['position'] for p in positionsDimensionsTemporal])
  print 'mean positions dimensions-spatial:',np.mean([p['position'] for p in positionsDimensionsSpatial])
  print 'mean positions dimensions-non-spatiotemporal:',np.mean([p['position'] for p in positionsDimensions])
  print 'mean positions dimensions-spatiotemporal:',np.mean([p['position'] for p in positionsDimensionsSpatiotemporal])
  
  # create the csv file needed to do ANOVA for column positions
  rows = []
  for p in positionsMeasures:
    #rows.append({'columnType':'measure','position':p})
    rows.append(p)
  for p in positionsDimensions:
    #rows.append({'columnType':'dimension-other','position':p})
    rows.append(p)
  for p in positionsDimensionsTemporal:
    #rows.append({'columnType':'dimension-temporal','position':p})
    rows.append(p)
  for p in positionsDimensionsSpatial:
    #rows.append({'columnType':'dimension-spatial','position':p})
    rows.append(p)
  writeResults('column_positions.csv',rows)
  
  # return tracking objects
  return {
    'editDistances':editDistances,
    'newCols':newCols,
    'uniqueSheets':uniqueSheets,
    'allUniqueSheets':allUniqueSheets,
    'orderings':orderings,
    'interactions':interactions,
  }

# for each column in the order of appearance data, compute its position
# columns added simultaneously are given the same position value
# criteria is a filter saying what should be included
def calculatePositions(dataset,order,criteria):
  positions = []
  for i,final in enumerate(order):
    posList = []
    if "+" in final:
      posList = final.split("+")
    else:
      posList.append(final)
    for p in posList:
      if criteria(dataset,p):
        positions.append(i)
  return positions

# for an order of appearance sequence, get the "new" columns that do not appear in the prompt
def getNewColumns(dataset,task,ordering):
  newCols = []
  for c in ordering:
    toCheck = []
    if "+" in c:
      toCheck = c.split("+")
    else:
      toCheck.append(c)
    for c2 in toCheck:
      if c2 not in baseColumns[dataset][task] and c2 not in newCols:
        newCols.append(c2)
  return newCols

# compare edit distances
def levenshtein(s1, s2):
  if len(s1) < len(s2):
    return levenshtein(s2, s1)
  # len(s1) >= len(s2)
  if len(s2) == 0:
    return len(s1)
  previous_row = range(len(s2) + 1)
  for i, c1 in enumerate(s1):
    current_row = [i + 1]
    for j, c2 in enumerate(s2):
      insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
      deletions = current_row[j] + 1       # than s2
      substitutions = previous_row[j] + (c1 != c2)
      current_row.append(min(insertions, deletions, substitutions))
    previous_row = current_row
  return previous_row[-1]

if __name__ == "__main__":
  data = json.load(open('master_file.json'))
  res = computeOpenEndedStats(data)
  massageStats(res)
