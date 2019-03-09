import csv

#all datasets
datasets = ['birdstrikes1','faa1','weather1']
#all tasks
tasks = ['t1','t2','t3','t4']
#expertise levels
expertiseLevels = ['novice','expert']

aggregationTypes = {'pcdf-sum':'pcdf-sum','pcto-cnt':'pcto-cnt','diff-sum':'diff-sum','pcto-sum':'pcto-sum','md':'md','std':'standard-deviation','ctd':'count-distinct','sum':'sum','cnt':'count','max':'max','min':'min','avg':'avg','med':'med'}
dateGroupTypes = {'yr':'year','mn':'month','qr':'quarter','wk':'week',
  'dy':'day','tyr':'year','tmn':'month','tqr':'quarter','twk':'week','tdy':'day'}

#which users analyzed which datasets
usersPerDataset = {'birdstrikes1': ['01', '05', '09', '109', '13', '25', '29', '33', '37', '53', '57', '61', '73', '77', '81', '85', '97'], 'weather1': ['01', '05', '113', '117', '21', '25', '29', '41', '45', '53', '65', '69', '73', '77', '93', '97'], 'faa1': ['09', '109', '13', '21', '33', '37', '41', '45', '57', '65', '69', '81', '85', '89', '93']}

# The columns associated with each task prompt (in order of the prompt text).
# number of records is included in every set of columns, as it was a core component of the tasks.
# Some of the weather tasks have variants, which are used for edit distance calculations.
# Did not want to make a distinction between TMAX and TMAX_F, for example.
baseColumns = {
  'birdstrikes1':{
    't1':['dam_eng1','dam_eng2','dam_windshld','dam_wing_rot','number of records'],
    't2':['ac_class','damage','number of records'],
    't3':['precip','sky','incident_date','number of records'],
    't4':['number of records','precip','sky']
  },
  'faa1':{
    't1':['cancelled','diverted','arrdelay','depdelay','number of records'],
    't2':['number of records','flightdate','uniquecarrier'],
    't3':['distance','arrdelay','number of records'],
    't4':['uniquecarrier','origin','dest','number of records']
  },
  'weather1':{
    't1':['heavyfog','mist','drizzle','groundfog','number of records'],
    't2':['tmax','tmax_f','tmin','tmin_f','date','number of records'],
    't2-2':['tmax','tmin','date','number of records'],
    't2-3':['tmax_f','tmin_f','date','number of records'],
    't3':['highwinds','state','lat','latitude (generated)','lng','longitude (generated)','number of records'],
    't3-2':['highwinds','state','lat','lng','number of records'],
    't3-3':['highwinds','state','latitude (generated)','longitude (generated)','number of records'],
    't4':['date','state','lat','latitude (generated)','lng','longitude (generated)','name','number of records'],
    't4-2':['date','state','lat','lng','name','number of records'],
    't4-3':['date','state','latitude (generated)','longitude (generated)','name','number of records']
  }
}

def mergeDuplicateLabels(oldState):
  state = list(oldState)
  for i,s in enumerate(state):
    if s == 'tmax_f':
      state[i] = 'tmax'
    elif s == 'tmin_f':
      state[i] = 'tmin'
  for i,s in enumerate(state):
    if s == 'latitude (generated)':
      state[i] = 'lat'
    elif s == 'longitude (generated)':
      state[i] = 'lng'
  return state

#made this file to tell myself which columns are dimensions, which are measures, which are spatial and which are temporal
columnInfo = {}
with open('column_info.csv') as f:
  reader = csv.DictReader(f)
  #dataset, colname, measure_dim,temporal,spatial
  for row in reader:
    dataset = row['dataset']
    colname = row['column_name']
    md = row['measure_dimension']
    temporal = row['is_temporal'] == 'true'
    spatial = row['is_spatial'] == 'true'
    if dataset not in columnInfo:
      columnInfo[dataset] = {'number of records':{'type':'measure', 'temporal':False,'spatial':False},
        'latitude (generated)':{'type':'dimension', 'temporal':False,'spatial':True},
        'longitude (generated)':{'type':'dimension', 'temporal':False,'spatial':True}}
    columnInfo[dataset][colname] = {'type':md, 'temporal':temporal,'spatial':spatial}

answerTypes = {}
for row in csv.DictReader(open('answer_types.csv'),delimiter='|'):
  dataset = row['dataset']
  task = row['task']
  if dataset not in answerTypes:
    answerTypes[dataset] = {}
  if task not in answerTypes[dataset]:
    answerTypes[dataset][task] = {}
  answerTypes[dataset][task][row['answerType']] = {'answer':row['answer'],'correct':row['answerCorrect']=='True','thoroughness':row['answerThoroughness']}

#TODO get better cols
def getStatesForSubtask(data,user,dataset,task):
  states = {}
  for row in data:
    if row['dataset'] == dataset and row['userid'] == user and row['task'] == task:
      states[tuple(row['state'])] = True
  return states

#TODO get better cols
def getStates(data,user,dataset):
  states = {}
  for row in data:
    if row['dataset'] == dataset and row['userid'] == user:
      states[tuple(row['state'])] = True
  return states

# used to export results as a csv file
def writeResults(filename,results,delim=',',header=None,quoteLevel=csv.QUOTE_MINIMAL):
  if header is None:
    header = sorted(results[0].keys())
  with open(filename,'w') as f:
    csvWriter = csv.DictWriter(f, delimiter=delim,fieldnames=header,quoting=quoteLevel)
    csvWriter.writeheader()
    for row in results:
      csvWriter.writerow(row)

def isValidColumn(dataset,colName):
  return colName in columnInfo[dataset] or colName in calculationInfo[dataset]

def getColumnType(dataset,colName):
  source = None
  if colName in calculationInfo[dataset]: # is calculation
    source = calculationInfo[dataset][colName]
  else:
    source = columnInfo[dataset][colName]
    
  if source['type'] == 'dimension': 
    if source['temporal']:
      return 'dimension-temporal'
    elif source['spatial']:
      return 'dimension-spatial'
    else:
      return 'dimension-other'
  else:
    return 'measure'

def extractRawName(column):
  returnval = None
  if 'TEMP(' not in column:
    col = None
    if '.' in column:
      col = column.split('.')[-1]
    else:
      col = column
    returnval = col.replace('[','').replace(']','')
  else:
    col = None
    name = None
    m = re.search(r'TEMP\(([^\(\)]+)\)',column)
    if m is not None:
      col = m.group(1)
    returnval = name.replace('[','').replace(']','')
  if returnval not in ['Multiple Values',':Measure Names','Measure Names']:
    return returnval
  return None

def extractNameModified(colname):
  n = extractName(colname)
  n = n.replace(" (bin)","").replace(" (group)","").replace(" (copy)","")
  # ignore these
  if n in ["Measure Names", "Multiple Values"]:
    return None
  return n.lower()

def extractName(column):
  if 'TEMP(' not in column:
    col = None
    if '.' in column:
      col = column.split('.')[-1]
    else:
      col = column
    name = None
    if ':' in col:
      #name = col.split(':')[1]
      name = col.split(':',3)[-2]
    else:
      #name =re.sub(r'\[|\]','',col) 
      name = (col.replace("[","")).replace("]","")
    return (name.replace("[","")).replace("]","")
  else:
    col = None
    name = None
    m = re.search(r'TEMP\(([^\(\)]+)\)',column)
    if m is not None:
      col = m.group(1)
      if ':' in col:
        #name = col.split(':')[1]
        name = col.split(':',3)[-2]
      else:
        name =re.sub(r' (upper|lower)$','',col) 
    return (name.replace("[","")).replace("]","")
