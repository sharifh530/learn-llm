# Authored lessons: Tiny Chat Lab

Start with L01. Predict before running code or revealing answers. The first six examples use only Python's standard library and run locally without Google credentials. Later authored lessons may introduce dependencies or live model calls explicitly.

These are complete reading activities, also available as clickable games and quizzes in the M1 web app. Try two of three questions correctly, then complete the small build mission. The app saves lesson progress and journal entries locally.

This reading copy is generated from `content/lessons/*.json`. Edit the JSON, then run `python tools/render_lessons.py`. Some Markdown viewers show the answer panels expanded; pause before looking at them.

## L01: The next-word detective

Prediction Playground · about 20 minutes · version 1

### Your goal

- Explain next-token prediction using a familiar sentence.
- Distinguish a likely continuation from a verified fact.

### Predict first

Finish this sentence before reading further: I drink a cup of ___. Would tea, socks, or moon be a more ordinary continuation?

### Learn

You probably picked tea. You have seen many examples of cups and drinks, so that continuation fits. A language model also uses patterns learned from examples to assign probabilities to possible next pieces of text.

LLM means large language model. In many text-generation systems, the model predicts a next token, the application selects one, and the process repeats. A token is a text piece; for now we use whole words to keep the idea visible.

A model can assign high probability to a familiar claim even when the claim is false. Likely wording is not a fact check. We will later add source notes and evaluations to make our chatbot more dependable.

Start with a Python dictionary. A dictionary stores key-value pairs. Our hand-written table can map a sentence prefix to one next word. This is a rule table, not a trained LLM, but you can inspect its entire behavior.

**Where the analogy stops:** The detective analogy describes finding a plausible continuation. Real LLMs do not consult our tiny dictionary and do not guarantee truth. Their token choices depend on learned numerical parameters and the supplied context.

### Run a tiny Python example

```python
next_word = {
    'I drink a cup of': 'tea',
    'The cat says': 'meow',
}
prompt = 'I drink a cup of'
print(next_word.get(prompt, 'I do not know yet'))
print(next_word.get('The rocket likes', 'I do not know yet'))
```

Expected output:

```text
tea
I do not know yet
```

- The dictionary key is a known prefix; its value is our chosen next word.
- get(key, default) returns the value when the key exists, otherwise the default.
- The second prefix is missing, so the fallback is printed rather than inventing an entry.

### Play: Next Word Detective

Choose the most ordinary continuation for each scene. These answers describe common language patterns, not laws about the world. Get two of three right to pass.

#### Round 1

The sky is full of dark clouds. It might ___ soon.

1. rain
2. keyboard
3. sandwich

<details>
<summary>Reveal answer and feedback</summary>

Correct: **rain**.

- **rain**: Rain is a familiar continuation. It is a prediction, not a weather report.
- **keyboard**: Keyboard does not describe the ordinary event suggested by the clouds.
- **sandwich**: Sandwich is a noun that does not fit this ordinary verb slot.

</details>

#### Round 2

I used a spoon to eat the ___.

1. soup
2. thunder
3. bicycle

<details>
<summary>Reveal answer and feedback</summary>

Correct: **soup**.

- **soup**: Soup fits the spoon-and-food pattern.
- **thunder**: Thunder is a sound, so it is not an ordinary thing to eat.
- **bicycle**: A bicycle is not an ordinary food. A silly story could use it, but that is not this task.

</details>

#### Round 3

A fluent chatbot says our fictional town was founded in 1620. No source was provided. What have we established?

1. The date is certainly true
2. It produced a plausible sentence; we still need evidence
3. The model looked at the town archives

<details>
<summary>Reveal answer and feedback</summary>

Correct: **It produced a plausible sentence; we still need evidence**.

- **The date is certainly true**: Fluency cannot prove the date.
- **It produced a plausible sentence; we still need evidence**: Exactly. The sentence may sound right without being supported.
- **The model looked at the town archives**: We have no evidence of an archive lookup or tool call.

</details>

### Quick quiz

Try at least two of three correctly. If you reveal a solution, study it and try again later.

#### Question 1

What is the simplified repeating step in text generation?

1. Search every website
2. Retrain the model after every word
3. Predict and select another token

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Predict and select another token**.

- **Search every website**: Web search requires a separate connected tool; generation alone does not imply it.
- **Retrain the model after every word**: Normal inference does not retrain the model after each token.
- **Predict and select another token**: The selected token becomes part of the context for the next step.

</details>

#### Question 2

Is the example dictionary a trained LLM?

1. No, it is a hand-authored lookup toy
2. Yes, because it uses Python
3. Yes, because it prints text

<details>
<summary>Reveal answer and feedback</summary>

Correct: **No, it is a hand-authored lookup toy**.

- **No, it is a hand-authored lookup toy**: You wrote the entries directly. Nothing learned parameters from data here.
- **Yes, because it uses Python**: A programming language does not determine whether a model learned from data.
- **Yes, because it prints text**: Printing text is not enough to make a system an LLM.

</details>

#### Question 3

Why should an important factual answer be checked?

1. Because Python cannot store facts
2. Because short replies are always wrong
3. Because plausible wording can be unsupported

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Because plausible wording can be unsupported**.

- **Because Python cannot store facts**: Python can store factual data; that is unrelated to the model's claim.
- **Because short replies are always wrong**: Length does not determine truth.
- **Because plausible wording can be unsupported**: Prediction can produce an unsupported claim. Evidence and evaluation help.

</details>

### Build mission: Add one prediction and one honest fallback

Copy the example into a local Python file. Add the prefix 'My robot likes' with the continuation 'puzzles'. Print that result and the result for one prefix you did not add.

You are done when:

- The new known prefix prints puzzles.
- The unknown prefix prints the fallback rather than raising an error.

<details>
<summary>Hints</summary>

1. Add another key-value pair inside the dictionary.
2. Use .get() with the same fallback for both lookups.

</details>

<details>
<summary>Reference solution or solution notes</summary>

```text
next_word = {'My robot likes': 'puzzles'}
print(next_word.get('My robot likes', 'I do not know yet'))
print(next_word.get('My robot sleeps on', 'I do not know yet'))
```

</details>

### Explain it back

Explain to a friend why a chatbot can sound confident without proving its answer is true.

**Ask AI when connected:** Give me a hint, use a simpler example, explain this Python, or quiz me with a fresh example.

## L02: Learning versus replying

Prediction Playground · about 25 minutes · version 1

### Your goal

- Separate training, inference, and saved conversation state.
- Learn a simple next-word preference by counting examples.

### Predict first

Your toy sees 'cats eat fish' twice and 'cats eat rice' once. Which word should a most-common-word rule select after eat? Decide before running the code.

### Learn

Training is the stage where examples change a model's learned parameters. Inference is using those learned parameters to produce an output. Think of learning recipes versus cooking one meal with a recipe you already know.

Our toy learns counts. Every training sentence contributes an observation: what word followed eat? Two fish observations and one rice observation make fish the most common in this small dataset.

collections.Counter is a Python dictionary-like counter. Counter(['fish', 'fish', 'rice']) records how many times each item occurs. most_common(1) asks for the single most frequent item and its count.

A saved chat is different again. The application stores messages and can supply them as context on a later request. Saving a message or changing a prompt does not, by itself, retrain the hosted model.

**Where the analogy stops:** Recipe learning is an analogy. Our count table has no neural weights, gradient optimization, or transformer layers. Real LLM training is far more complex than counting a few words.

### Run a tiny Python example

```python
from collections import Counter

training_sentences = ['cats eat fish', 'dogs eat fish', 'birds eat rice']
following_eat = Counter()
for sentence in training_sentences:
    words = sentence.split()
    if words[1] == 'eat':
        following_eat[words[2]] += 1
print(dict(following_eat))
prediction = following_eat.most_common(1)[0][0]
print(prediction)
```

Expected output:

```text
{'fish': 2, 'rice': 1}
fish
```

- split() creates a list of words. This dataset always has three words, so its fixed indexes are safe only for these examples.
- The loop learns counts from the training sentences.
- most_common(1) returns a list containing a (word, count) pair. The first [0] selects that pair; the second selects its word.
- Selecting fish uses the counts; it does not add another observation.

### Play: Training or Playing?

Sort each action into training, inference, or app memory. Two of three correct passes.

#### Round 1

You scan three example sentences and update the word counts.

1. Training our count toy
2. Inference only
3. Saving a chat

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Training our count toy**.

- **Training our count toy**: The examples changed the toy's learned counts.
- **Inference only**: Here the stored counts change, so this is the learning stage.
- **Saving a chat**: You are fitting counts from examples, not storing a conversation record.

</details>

#### Round 2

You use the existing count table to select fish.

1. Cloud backup
2. Training
3. Inference

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Inference**.

- **Cloud backup**: No backup was created by selecting a word.
- **Training**: No training observation was added.
- **Inference**: You are using what the toy already learned.

</details>

#### Round 3

Your app saves 'My name is Mira' to SQLite for later context.

1. The hosted model was retrained
2. The app stored conversation state
3. The model gained a new neural layer

<details>
<summary>Reveal answer and feedback</summary>

Correct: **The app stored conversation state**.

- **The hosted model was retrained**: Saving chat history does not update the hosted model's parameters.
- **The app stored conversation state**: The app can later send this message as context; that is separate from training.
- **The model gained a new neural layer**: A database write does not alter model architecture.

</details>

### Quick quiz

Try at least two of three correctly. If you reveal a solution, study it and try again later.

#### Question 1

What made fish the toy's preferred prediction?

1. Fish appeared most often after eat in the examples
2. Fish is universally the correct food
3. Python likes short words

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Fish appeared most often after eat in the examples**.

- **Fish appeared most often after eat in the examples**: The preference came from this dataset's counts.
- **Fish is universally the correct food**: The data does not prove a universal fact about animals.
- **Python likes short words**: The code counts observations; word length does not choose the result.

</details>

#### Question 2

Which action would change this toy's learned preference toward rice?

1. Print fish more times
2. Rename the output variable
3. Add enough rice training examples and rebuild counts

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Add enough rice training examples and rebuild counts**.

- **Print fish more times**: Printing does not feed observations back into this toy.
- **Rename the output variable**: A variable name does not change the counts.
- **Add enough rice training examples and rebuild counts**: Changing training data and recomputing counts changes the learned preference.

</details>

#### Question 3

A hosted chatbot uses your name from a previous message. What might explain it?

1. The app included that message in the request context
2. It must have read your computer files
3. Every reply permanently retrains the model

<details>
<summary>Reveal answer and feedback</summary>

Correct: **The app included that message in the request context**.

- **The app included that message in the request context**: Conversation context can supply the name without updating the model.
- **It must have read your computer files**: Name recall alone is not evidence of file access.
- **Every reply permanently retrains the model**: Normal chat generation does not imply retraining.

</details>

### Build mission: Change what the toy learns

Add two more three-word training sentences ending in rice. Rebuild the counts and predict again. Before running it, calculate the new fish and rice counts yourself.

You are done when:

- The new counts contain fish: 2 and rice: 3.
- The new most-common prediction is rice, and you can explain why.

<details>
<summary>Hints</summary>

1. For example, 'robots eat rice' has the required three-word shape.
2. Run the counting loop from an empty Counter after changing the dataset.

</details>

<details>
<summary>Reference solution or solution notes</summary>

```text
from collections import Counter
sentences = ['cats eat fish', 'dogs eat fish', 'birds eat rice', 'robots eat rice', 'mice eat rice']
counts = Counter(sentence.split()[2] for sentence in sentences)
print(dict(counts))
print(counts.most_common(1)[0][0])
```

</details>

### Explain it back

Describe one example each of training, inference, and application memory using your chatbot project.

**Ask AI when connected:** Give me a hint, use a simpler example, explain this Python, or quiz me with a fresh example.

## L03: Build a tiny story machine

Prediction Playground · about 30 minutes · version 1

### Your goal

- Generate text by repeatedly selecting a next word.
- Explain a bigram toy's limited context and stopping condition.

### Predict first

If your toy remembers only the previous word, can it reliably keep a character's name from ten sentences ago? Why or why not?

### Learn

A bigram is a pair of adjacent items. Our toy reads word pairs such as robots → like and like → puzzles. It learns how often each next word followed the current word.

To generate, start with robots, select its most common next word, append that word, and repeat. Each new word creates the next step's context. Here the model's context is only one word.

An end marker tells the toy when a sentence ends. A maximum-step limit prevents endless loops when the learned transitions cycle. Useful chat apps also need output limits and interruption handling.

This small machine can repeat a trained phrase but struggles to combine ideas sensibly. A bigger context and a different model architecture are needed for richer behavior; scaling a dictionary alone does not reproduce an LLM.

**Where the analogy stops:** The story chain demonstrates repeated prediction. It only uses adjacent-word counts and deterministic most-common selection, not transformer attention or an actual hosted model's tokenizer.

### Run a tiny Python example

```python
from collections import Counter, defaultdict

data = ['robots like puzzles', 'robots like puzzles', 'robots eat rice']
transitions = defaultdict(Counter)
for sentence in data:
    words = sentence.split() + ['<END>']
    for current, following in zip(words, words[1:]):
        transitions[current][following] += 1

word = 'robots'
output = [word]
for _ in range(8):
    options = transitions.get(word)
    if not options:
        break
    word = options.most_common(1)[0][0]
    if word == '<END>':
        break
    output.append(word)
print(' '.join(output))
```

Expected output:

```text
robots like puzzles
```

- defaultdict(Counter) creates an empty counter when a new current word is observed during learning.
- zip(words, words[1:]) pairs each word with the next one. The end marker becomes a learned next item.
- The generation loop chooses the most frequent next word and appends it to a list.
- The loop stops at END, an unknown transition, or eight steps. join() converts the list into text.

### Play: Story Chain

Use the toy's transition counts to predict a chain. Do not choose the funniest story unless the counts support it. Two correct rounds passes.

#### Round 1

After robots, the counts are like: 2 and eat: 1. What does our most-common rule choose?

1. like
2. eat
3. dance

<details>
<summary>Reveal answer and feedback</summary>

Correct: **like**.

- **like**: Like has the highest observed count.
- **eat**: Eat is observed but less common under this deterministic rule.
- **dance**: Dance was not observed after robots in this training data.

</details>

#### Round 2

The toy selects <END> after puzzles. What happens?

1. The app invents another word
2. Generation stops without printing the marker
3. The model retrains

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Generation stops without printing the marker**.

- **The app invents another word**: The stopping check exits the loop instead of guessing more.
- **Generation stops without printing the marker**: The code checks the marker before appending it.
- **The model retrains**: The marker is a generation stopping signal, not a training action.

</details>

#### Round 3

Training contains robots like robots. Why keep a maximum-step limit?

1. To bound generation if transitions keep cycling
2. To make facts true
3. To improve spelling

<details>
<summary>Reveal answer and feedback</summary>

Correct: **To bound generation if transitions keep cycling**.

- **To bound generation if transitions keep cycling**: Cycles can repeat. A limit prevents unbounded generation.
- **To make facts true**: A step limit does not verify factual claims.
- **To improve spelling**: The limit controls work, not spelling.

</details>

### Quick quiz

Try at least two of three correctly. If you reveal a solution, study it and try again later.

#### Question 1

How much text does this toy use to choose the next word?

1. Every page on the internet
2. All chats in the database
3. The immediately previous word

<details>
<summary>Reveal answer and feedback</summary>

Correct: **The immediately previous word**.

- **Every page on the internet**: No network lookup appears in the code.
- **All chats in the database**: The generator never reads chat storage.
- **The immediately previous word**: Its transitions are indexed by one current word.

</details>

#### Question 2

What does zip(words, words[1:]) produce?

1. Adjacent word pairs
2. A compressed archive
3. A trained neural network

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Adjacent word pairs**.

- **Adjacent word pairs**: The second list starts one position later, so each pair links neighbors.
- **A compressed archive**: Python's zip pairs items from iterables; it is not a file compressor here.
- **A trained neural network**: It pairs values; it does not train a neural network.

</details>

#### Question 3

Does a readable output prove this toy understands every sentence?

1. Yes, because END was reached
2. Yes, one good sentence proves general understanding
3. No, the toy may just repeat local patterns

<details>
<summary>Reveal answer and feedback</summary>

Correct: **No, the toy may just repeat local patterns**.

- **Yes, because END was reached**: Stopping correctly does not establish general understanding.
- **Yes, one good sentence proves general understanding**: One output is weak evidence about broader behavior.
- **No, the toy may just repeat local patterns**: Local patterns can create readable text without broad capability.

</details>

### Build mission: Give the robot a new menu

Change the training data to two copies of 'robots cook noodles' and one copy of 'robots eat rice'. Keep robots as the starting word. Predict the output, then run it. Try an unknown start word afterward.

You are done when:

- The most-common chain prints robots cook noodles.
- An unknown starting word ends safely instead of throwing an exception.

<details>
<summary>Hints</summary>

1. Keep the end marker and the step limit.
2. transitions.get(word) returns no options for an unseen start; the existing guard handles it.

</details>

<details>
<summary>Reference solution or solution notes</summary>

```text
Use the example generator with data = ['robots cook noodles', 'robots cook noodles', 'robots eat rice']. With word = 'robots', it prints 'robots cook noodles'. With word = 'spaceships', it prints only 'spaceships' and exits safely.
```

</details>

### Explain it back

Which two stopping rules would you keep in a real chatbot, and what extra context would it need beyond one word?

**Ask AI when connected:** Give me a hint, use a simpler example, explain this Python, or quiz me with a fresh example.

## L04: Tokens are text pieces

Token Arcade · about 20 minutes · version 1

### Your goal

- Explain why tokens are not necessarily whole words.
- Distinguish an illustrative token split from a model-specific tokenizer.

### Predict first

Imagine text building blocks ['play', 'ful', ' robot', '!']. How many pieces are there, and what text do they form?

### Learn

Models process text through a tokenizer, which maps text into token IDs. Tokens can correspond to a word, part of a word, punctuation, or another text piece. The exact mapping depends on the model's tokenizer.

In our illustrative split, play and ful are separate pieces, while the leading space belongs to ' robot'. Four pieces reconstruct 'playful robot!'. A different real tokenizer may split that text differently.

Text length, word count, and token count are different measures. Python split() makes whitespace-separated words; it is not a universal LLM tokenizer. Even different languages and punctuation patterns can affect token counts.

Your chatbot will budget context and output in tokens. When accuracy matters, ask the configured model's token-counting interface rather than presenting a word-count guess as exact. For this lesson, our list is deliberately hand-written.

**Where the analogy stops:** Building blocks show that text can be assembled from pieces. These four pieces are illustrative and are not asserted to be Gemini's actual encoding. The code is a joiner, not a tokenizer implementation.

### Run a tiny Python example

```python
pieces = ['play', 'ful', ' robot', '!']
text = ''.join(pieces)
print(text)
print('pieces:', len(pieces))
print('whitespace words:', len(text.split()))
```

Expected output:

```text
playful robot!
pieces: 4
whitespace words: 2
```

- The space before robot is inside that piece.
- ''.join(pieces) concatenates without inserting extra spaces.
- len(pieces) counts our manual pieces, while split() counts whitespace-separated words.
- Neither measurement proves the token count for an actual hosted model.

### Play: Token Puzzle

Work with the manual pieces shown in each round. Do not assume these are actual model tokens. Get two of three right.

#### Round 1

Join ['sun', 'shine', '!'] without adding separators.

1. sunsh ine
2. sunshine!
3. sun shine !

<details>
<summary>Reveal answer and feedback</summary>

Correct: **sunshine!**.

- **sunsh ine**: That changes the supplied pieces.
- **sunshine!**: No piece contains a space, so none is inserted.
- **sun shine !**: That would require adding spaces between pieces.

</details>

#### Round 2

How many manual pieces are in ['un', 'happy', ' cat', '.']?

1. Four, because the list has four items
2. One, because it is one sentence
3. Two, because there are two words

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Four, because the list has four items**.

- **Four, because the list has four items**: Four entries form the illustrative text pieces.
- **One, because it is one sentence**: Sentence boundaries do not determine the number of pieces.
- **Two, because there are two words**: Word count and piece count are different.

</details>

#### Round 3

You need the actual token count for your configured Google model. What should you do?

1. Use this manual split for every model
2. Count spaces and call it exact
3. Use the model's supported counting interface

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Use the model's supported counting interface**.

- **Use this manual split for every model**: Tokenizers vary, and our pieces were invented for teaching.
- **Count spaces and call it exact**: Space counting is an estimate of words, not exact model tokens.
- **Use the model's supported counting interface**: Use the appropriate model interface and label any fallback estimate.

</details>

### Quick quiz

Try at least two of three correctly. If you reveal a solution, study it and try again later.

#### Question 1

Must one token always equal one whole word?

1. No, it may represent a smaller or different text piece
2. Yes, unless the code uses a dictionary
3. Yes, in every model

<details>
<summary>Reveal answer and feedback</summary>

Correct: **No, it may represent a smaller or different text piece**.

- **No, it may represent a smaller or different text piece**: Tokenization is model-specific and need not match word boundaries.
- **Yes, unless the code uses a dictionary**: A Python container does not determine the model's token boundaries.
- **Yes, in every model**: That confuses words with tokens.

</details>

#### Question 2

What is this lesson's Python code actually doing?

1. Calling Gemini's tokenizer
2. Training a vocabulary
3. Joining hand-written pieces

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Joining hand-written pieces**.

- **Calling Gemini's tokenizer**: No Google SDK or tokenizer is called.
- **Training a vocabulary**: There is no learning step or vocabulary fitting.
- **Joining hand-written pieces**: The pieces are already supplied, and join reconstructs the text.

</details>

#### Question 3

Why do we care about tokens in a chatbot?

1. They make every answer factual
2. They replace the need for prompts
3. They help measure model input/output limits and usage

<details>
<summary>Reveal answer and feedback</summary>

Correct: **They help measure model input/output limits and usage**.

- **They make every answer factual**: Tokenization does not guarantee truth.
- **They replace the need for prompts**: Prompts are still input text that gets encoded.
- **They help measure model input/output limits and usage**: Token budgets are useful for context, generation, and usage management.

</details>

### Build mission: Assemble a text puzzle

Create pieces ['chat', 'bot', ' builder', '!']. Join them, count the list entries, and count whitespace words. Add a comment saying this is a manual illustration, not a real model tokenizer.

You are done when:

- Output includes chatbot builder!, four manual pieces, and two whitespace words.
- A code comment clearly identifies the manual illustration.

<details>
<summary>Hints</summary>

1. Use an empty string as the join separator.
2. len(pieces) counts pieces; len(text.split()) counts whitespace-separated words.

</details>

<details>
<summary>Reference solution or solution notes</summary>

```text
# Manual illustration, not a model tokenizer.
pieces = ['chat', 'bot', ' builder', '!']
text = ''.join(pieces)
print(text)
print(len(pieces))
print(len(text.split()))
```

</details>

### Explain it back

Explain why 'ten words' does not mean 'exactly ten tokens' for your chatbot.

**Ask AI when connected:** Give me a hint, use a simpler example, explain this Python, or quiz me with a fresh example.

## L05: The probability arcade

Token Arcade · about 30 minutes · version 1

### Your goal

- Explain how temperature reshapes a toy probability distribution.
- Distinguish sampling settings from factual verification.

### Predict first

A snack raffle favors tea over juice and water. If we make the odds more even, is water now guaranteed to win?

### Learn

A text model produces scores for possible next tokens. Sampling converts scores into probabilities and picks from those probabilities. The top choice can be common without being the only possible choice.

Temperature is one way to reshape probabilities. In this toy, divide each score by a positive temperature, apply exp, and normalize so probabilities add to one. Lower temperature makes the highest score dominate more; higher temperature flattens the distribution.

exp is a mathematical function that turns these scores into positive values. You do not need to memorize its formula today. Inspect how the final probabilities change when the temperature changes.

Temperature is not a truth knob. A lower value can repeat a false claim more consistently. A higher value does not guarantee creativity. Actual models may recommend specific defaults or restrict which settings are supported. We will check the configured model before offering a live control.

**Where the analogy stops:** The raffle helps explain sampling probabilities. Our fixed snack scores are invented, and the code displays probabilities rather than sampling. It is not a factuality experiment or a guarantee about a particular hosted model.

### Run a tiny Python example

```python
import math

scores = {'tea': 2.0, 'juice': 1.0, 'water': 0.0}
def probabilities(temperature):
    if temperature <= 0:
        raise ValueError('Use a positive temperature in this toy')
    peak = max(scores.values())
    weights = {name: math.exp((score - peak) / temperature)
               for name, score in scores.items()}
    total = sum(weights.values())
    return {name: weight / total for name, weight in weights.items()}

for temperature in [0.5, 2.0]:
    odds = probabilities(temperature)
    print('T =', temperature)
    print(', '.join(f'{name}: {chance:.2f}' for name, chance in odds.items()))
```

Expected output:

```text
T = 0.5
tea: 0.87, juice: 0.12, water: 0.02
T = 2.0
tea: 0.51, juice: 0.31, water: 0.19
```

- The toy scores are inputs, not observed truth ratings.
- Subtracting the maximum score helps numerical stability without changing the normalized probabilities.
- The dictionary comprehension builds one weight per snack; division by total normalizes them.
- Two-decimal display rounding can make the printed values add to 1.01. The unrounded values sum to approximately one.
- Temperature zero is excluded here to avoid division by zero; this toy does not implement greedy decoding.

### Play: Snack Raffle

Predict what the two displayed distributions imply. Remember that likelihood and correctness are different. Get two of three right.

#### Round 1

At T=0.5, tea has about 87% probability. What does that mean for sampling?

1. Tea must be the healthiest drink
2. Water is impossible
3. Tea is likely, but not guaranteed in one draw

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Tea is likely, but not guaranteed in one draw**.

- **Tea must be the healthiest drink**: The probabilities do not measure health or truth.
- **Water is impossible**: Water still has positive probability in this toy.
- **Tea is likely, but not guaranteed in one draw**: Sampling can still select a lower-probability option.

</details>

#### Round 2

What happened when the toy temperature rose from 0.5 to 2.0?

1. The most likely snack became certain
2. The training data grew
3. The probabilities became more even

<details>
<summary>Reveal answer and feedback</summary>

Correct: **The probabilities became more even**.

- **The most likely snack became certain**: The highest probability decreased, rather than becoming certain.
- **The training data grew**: Only the sampling transform changed; no data was added.
- **The probabilities became more even**: The distribution flattened, increasing relative chances for lower-score options.

</details>

#### Round 3

Your chatbot repeats a wrong date. Should lowering temperature count as verification?

1. Yes, consistent dates are always true
2. No, the claim still needs evidence
3. Yes, because probabilities become sharper

<details>
<summary>Reveal answer and feedback</summary>

Correct: **No, the claim still needs evidence**.

- **Yes, consistent dates are always true**: Repeated error is still error.
- **No, the claim still needs evidence**: Use source evidence and evaluations to check the date.
- **Yes, because probabilities become sharper**: Sharper probability is not factual support.

</details>

### Quick quiz

Try at least two of three correctly. If you reveal a solution, study it and try again later.

#### Question 1

Why divide each weight by the total weight?

1. To normalize the probabilities
2. To change the words into source citations
3. To retrain the model

<details>
<summary>Reveal answer and feedback</summary>

Correct: **To normalize the probabilities**.

- **To normalize the probabilities**: Normalized probabilities sum to approximately one before display rounding.
- **To change the words into source citations**: Normalization has nothing to do with citations.
- **To retrain the model**: This transform changes sampling probabilities, not learned scores.

</details>

#### Question 2

Does the example code actually draw a random snack?

1. No, it only computes and prints probabilities
2. Yes, print randomly chooses a dictionary key
3. Yes, exp picks one

<details>
<summary>Reveal answer and feedback</summary>

Correct: **No, it only computes and prints probabilities**.

- **No, it only computes and prints probabilities**: No random selection function is called.
- **Yes, print randomly chooses a dictionary key**: print only displays the constructed text.
- **Yes, exp picks one**: exp produces weights; a separate sampling step would choose an option.

</details>

#### Question 3

What should we verify before adding a live temperature slider?

1. The configured model's supported settings and recommendations
2. That all models have identical controls
3. That higher values guarantee truth

<details>
<summary>Reveal answer and feedback</summary>

Correct: **The configured model's supported settings and recommendations**.

- **The configured model's supported settings and recommendations**: Build the live control around actual provider support.
- **That all models have identical controls**: Generation controls can differ across models.
- **That higher values guarantee truth**: Temperature cannot guarantee truth.

</details>

### Build mission: Test a flatter distribution

Add T=1.0 to the example. Before running it, predict whether tea's probability will lie between the T=0.5 and T=2.0 values. Check the unrounded sum of probabilities.

You are done when:

- Tea's probability at T=1.0 is approximately 0.665 and lies between the two earlier values.
- The unrounded probabilities sum to approximately one; you do not mistake display rounding for extra probability.

<details>
<summary>Hints</summary>

1. Call probabilities(1.0).
2. Use abs(sum(odds.values()) - 1) < 1e-9 to check the sum with a small numerical tolerance.

</details>

<details>
<summary>Reference solution or solution notes</summary>

```text
With the example function defined:
odds = probabilities(1.0)
print(round(odds['tea'], 3))  # 0.665
print(abs(sum(odds.values()) - 1) < 1e-9)  # True
```

</details>

### Explain it back

How would you explain to someone why a consistent chatbot answer can still be wrong?

**Ask AI when connected:** Give me a hint, use a simpler example, explain this Python, or quiz me with a fresh example.

## L06: The conversation backpack

Token Arcade · about 25 minutes · version 1

### Your goal

- Separate stored history from the messages sent to a model.
- Explain why a context budget can omit an earlier fact.

### Predict first

Your app saves four messages but only sends the newest two. Can the model see an earlier name just because it is saved in the database?

### Learn

Imagine a conversation backpack with limited space. Your app has a shelf containing all saved messages, but only the messages packed for this request are available through that request's conversation context.

A context window is a model-specific limit on tokenized request material, with output limits that also need planning. The app must choose which instructions, prior turns, notes, and current question fit. Stored history is not automatically the same as selected context.

Our Python toy keeps two recent messages using a list slice. A slice such as messages[-2:] returns the last two list items. It makes the selection visible, but counts messages rather than tokens.

If an earlier personal name is omitted and not supplied elsewhere, the model cannot use that stored message through this request. It might guess, so an application should not treat a lucky answer as proof that context selection worked. In the real app, preserve instructions, valid role ordering, and an output budget.

**Where the analogy stops:** A backpack is a selection analogy, not a model memory architecture. The last-two-message toy is not a production context policy. Real requests must account for tokens, roles, instructions, notes, and output reserve.

### Run a tiny Python example

```python
messages = [
    {'role': 'user', 'text': 'My name is Mira.'},
    {'role': 'assistant', 'text': 'Hello Mira.'},
    {'role': 'user', 'text': 'I like puzzles.'},
    {'role': 'assistant', 'text': 'Let us try a puzzle.'},
]
selected = messages[-2:]
print('saved:', len(messages))
print('selected:', len(selected))
for message in selected:
    print(message['role'] + ': ' + message['text'])
```

Expected output:

```text
saved: 4
selected: 2
user: I like puzzles.
assistant: Let us try a puzzle.
```

- The list represents stored history.
- The slice creates the request's selected-history toy, without deleting the original list.
- The name appears in the saved messages but not in selected.
- A real current user question would be added after valid selected history; this example only inspects the selection.

### Play: Memory Backpack

Decide what the model can use from the packed context. Separate saved storage from request content. Get two of three right.

#### Round 1

Four messages are saved, but selected contains only the last two. How many messages did our toy pack?

1. Four
2. Two
3. All messages ever written

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Two**.

- **Four**: Four were saved, but saving and selecting are different.
- **Two**: The slice selected two list entries.
- **All messages ever written**: This code only uses the list shown and its slice.

</details>

#### Round 2

The name Mira was in an omitted message. What does this reveal?

1. The name is absent from this selected request context
2. The name was erased from the database
3. The model was retrained to forget

<details>
<summary>Reveal answer and feedback</summary>

Correct: **The name is absent from this selected request context**.

- **The name is absent from this selected request context**: The packed messages do not include that name.
- **The name was erased from the database**: The original list remains; selection does not delete saved history.
- **The model was retrained to forget**: Context selection does not retrain model parameters.

</details>

#### Round 3

Which is the better future app policy?

1. Keep valid roles/instructions and select history under a token budget
2. Always take two messages and call it exact token budgeting
3. Always send unlimited history

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Keep valid roles/instructions and select history under a token budget**.

- **Keep valid roles/instructions and select history under a token budget**: A real policy accounts for structure and size while preserving necessary context.
- **Always take two messages and call it exact token budgeting**: Two messages may have very different token counts.
- **Always send unlimited history**: Models and apps have input/output limits.

</details>

### Quick quiz

Try at least two of three correctly. If you reveal a solution, study it and try again later.

#### Question 1

What does messages[-2:] do?

1. Counts exact model tokens
2. Returns the last two items
3. Deletes the first two saved items

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Returns the last two items**.

- **Counts exact model tokens**: It selects messages, not tokenizes them.
- **Returns the last two items**: Negative indexes count backward from the end.
- **Deletes the first two saved items**: This slice returns a new list; it does not delete the original history.

</details>

#### Question 2

What makes saved history useful to a stateless model request?

1. The app including relevant saved content in the request
2. Changing a CSS color
3. Merely keeping a SQLite file on disk

<details>
<summary>Reveal answer and feedback</summary>

Correct: **The app including relevant saved content in the request**.

- **The app including relevant saved content in the request**: The app chooses and supplies relevant context.
- **Changing a CSS color**: Presentation does not alter the request content.
- **Merely keeping a SQLite file on disk**: The provider does not automatically read your local database.

</details>

#### Question 3

Which three mechanisms should stay distinct?

1. Fonts, colors, and margins
2. Trained parameters, stored app history, and selected request context
3. Tea, juice, and water

<details>
<summary>Reveal answer and feedback</summary>

Correct: **Trained parameters, stored app history, and selected request context**.

- **Fonts, colors, and margins**: Those are UI concerns, not the three model/app memory mechanisms.
- **Trained parameters, stored app history, and selected request context**: They can affect behavior in different ways; saving is not training or automatic selection.
- **Tea, juice, and water**: Those are our sampling examples.

</details>

### Build mission: Inspect the backpack

Change the example to select the last three messages. Print which messages are selected and whether any contains Mira. Compare this to selecting only the last two. Keep the full saved list unchanged.

You are done when:

- The three-message selection includes 'Hello Mira.' while the two-message selection does not.
- The saved list still contains four messages after both selections.

<details>
<summary>Hints</summary>

1. Use messages[-3:] and messages[-2:].
2. any('Mira' in m['text'] for m in selected) tests whether at least one selected message contains the name.

</details>

<details>
<summary>Reference solution or solution notes</summary>

```text
With messages from the example:
for count in [3, 2]:
    selected = messages[-count:]
    print(count, any('Mira' in m['text'] for m in selected))
print('saved:', len(messages))
Expected: 3 True; 2 False; saved: 4.
```

</details>

### Explain it back

Explain how your future chatbot will keep saved history separate from the messages sent to Google.

**Ask AI when connected:** Give me a hint, use a simpler example, explain this Python, or quiz me with a fresh example.
