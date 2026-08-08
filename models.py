import random
from utils.traversal import traverse_obj

QUESTIONS_MAP = {
    'friends or family that work for amazon': random.choice(('Yes', 'No')),
    'how many paid jobs have you had': '5',
    'the last 5 years, have you': random.choice(('Laidoff', 'None')),
    'how much time have you spent not working but looking for work': random.choice(('1yr', '0')),
    '''In the jobs you've had the past 5 years, how many hours per week did you usually work''': random.choice(('LT10', 'DK')),
    '''In the jobs you've had the past 5 years, how long was a typical shift''': random.choice(('8Hrs', 'LT8', 'DK')),
    '''Were any of the jobs you've had the past 5 years in a warehouse or similar environment''': 'Yes',
    '''Did any of the jobs you've had the past 5 years require you to lift up to 15 kilograms''': random.choice(('Yes', 'DK')),
    'had the past 5 years require you to stand, walk, push, pull, squat, bend': random.choice(('Yes', 'No')),
}

def evaluate_question(question):
  question = question.lower()
  for que, answer in QUESTIONS_MAP.items():
    if que in question:
      return answer
    
  return 'Yes'

SCALE_QUESTIONS_MAP = {
    'Admitting mistakes is a strength': -2,
    'Career growth is important to me': -2,
    'Climbing the career ladder is not very important to me': -2,
    'I am always looking at the next step to advance my career': -2,
    'I appreciate all the good things that have come my way in life': -2,
    'I appreciate how others helped me get to where I am today': -2,
    'I can always be trusted to fulfill my obligations': -2,
    'I do my best, even on trivial tasks': -2,
    "I don't need to be promoted to be satisfied": -2,
    'I follow every safety rule to avoid risk to others': -2,
    'I follow safety rules no matter what': -2,
    'I follow through on my obligations': -2,
    'I frequently think about the next step in my career': -2,
    "I notice when I benefit from someone else's actions": -2,
    'I persist through challenging tasks': -2,
    'I prefer to work on high impact projects': -2,
    'I rarely miss deadlines': -2,
    'I usually can be counted on to get the job done': -2,
    'I usually speak up when I make a mistake': -2,
    "I'm always working to get to the next level": -2,
    "I'm known for getting work done": -2,
    "I'm proud of both my own and others' contributions": -2,
    "It's best to acknowledge mistakes as soon as possible": -2,
    'Not every rule has a good reason behind it': -2,
    'People should always be working toward the next step in their career': -2,
    'People who break rules should face consequences': -2,
    'Shortcuts are necessary for success': -2,
    "Some opportunities have been given to me, others I've earned": -2
}

def evaluate_scale_question(questions):
  for question in questions:
    question = question.lower()
    for que, ans in SCALE_QUESTIONS_MAP.items():
      if que.lower() in question:
        return ans

  return random.choice((-2, -1, 1, 2))

def evaluate_item_code(data: dict) -> dict:
  item_code = data.get('stimulusCode')
  code_len = len(item_code)
  rules = traverse_obj(data, ('rules', ..., {'rule_type': ('ruleType',), 'predicate': ('ruleInformation', 'predicate'), 'code_length': ('ruleInformation', 'codeLength'), 'arguments': ('ruleInformation', 'arguments', 0), 'response_label': ('responseLabel', {str})}))
  response_map = {r['label']: r for r in traverse_obj(data, ('responses', ..., {'label': ('label', {str}), 'text_i18n': ('textI18N', {str}), 'available_space': ('iconInformation', 'availableSpace')}))}

  for r in rules:
    pred, arg, target_len, label = r.get('predicate'), r.get('arguments'), r.get('code_length'), r.get('response_label')
    
    if pred == 'wrongCode' and code_len == target_len:
      return label

    if 5 <= code_len <= 7 and ((pred == 'startsWith' and item_code.startswith(arg)) or (pred == 'endsWith' and item_code.endswith(arg))):
      if response_map.get(label, {}).get('available_space', 0) == 0:
        return next((rule['response_label'] for rule in rules if rule.get('rule_type') == 'ruleIcon'), 'SLOTFULL')
      return label

  return 'NOSLOT'
