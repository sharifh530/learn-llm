"""Educational numeric toys. No Google calls, learned embeddings, or model introspection."""
import math

FRUITS = [
    {'name':'Apple','emoji':'🍎','vector':[7,8,3]},
    {'name':'Banana','emoji':'🍌','vector':[9,2,1]},
    {'name':'Lemon','emoji':'🍋','vector':[2,1,10]},
]
WORDS = ['The','animal','crossed','because','it','was','tired']
VALUES = [.1,.9,.3,.1,.4,.2,.5]


def cosine(left, right):
    """Direction similarity; undefined for a zero vector, never invented as zero."""
    norm = math.sqrt(sum(value*value for value in left)) * math.sqrt(sum(value*value for value in right))
    if not norm:
        return None
    return max(-1.0,min(1.0,sum(a*b for a,b in zip(left,right))/norm))


def similarity(vector):
    matches = [{**fruit,'similarity':cosine(vector,fruit['vector'])} for fruit in FRUITS]
    if any(vector):
        matches.sort(key=lambda item:item['similarity'],reverse=True)
    return {'query':vector,'features':['Sweetness','Crunch','Sourness'], 'matches':matches,
            'defined':any(vector),'kind':'hand-made feature vectors; not learned embeddings'}


def attention(scores, query_index, causal, temperature):
    allowed = [not causal or index<=query_index for index in range(len(WORDS))]
    peak = max(score/temperature for score,keep in zip(scores,allowed) if keep)
    exponentials = [math.exp(score/temperature-peak) if keep else 0.0 for score,keep in zip(scores,allowed)]
    total = sum(exponentials)
    weights = [value/total for value in exponentials]
    rows = [{'word':word,'index':index,'score':scores[index],'value':VALUES[index],
             'masked':not allowed[index],'weight':weights[index]} for index,word in enumerate(WORDS)]
    return {'query':WORDS[query_index],'query_index':query_index,'causal':causal,'rows':rows,
            'sum':sum(weights),'weighted_value':sum(weight*value for weight,value in zip(weights,VALUES)),
            'kind':'manual scores and scalar values; not model attention or reasoning'}


def model_state(weight):
    # Train example (x=1,y=3), held-out check (x=2,y=4).
    return {'weight':weight,'prediction':weight,'train_target':3,'train_loss':(weight-3)**2,
            'check_prediction':2*weight,'check_target':4,'check_loss':(2*weight-4)**2}


def training(weight, learning_rate, steps, operation):
    before = model_state(weight)
    history = []
    if operation=='train':
        for _ in range(steps):
            gradient = 2*(weight-3)
            previous = weight
            weight -= learning_rate*gradient
            history.append({**model_state(weight),'before_weight':previous,'gradient':gradient})
    return {'before':before,'after':model_state(weight),'steps':history,'operation':operation,
            'learning_rate':learning_rate,'kind':'one-weight numeric predictor; not a language model'}
