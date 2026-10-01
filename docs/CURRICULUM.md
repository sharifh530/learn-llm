# Curriculum: learn by building

Each zone contains three lessons and a short boss challenge. Bosses reinforce ideas; they are not blockers. L01–L06 are fully authored in `content/lessons/`. L07–L24 and all bosses are outlines until a later prompt expands them.

## Python warmup if needed

Check you can read a list, look up a dictionary key, follow a loop, and call a function. Optional warmup: build `reply = {"hi": "hello"}` and use `.get()`. Later explain `Counter`, imports, environment variables, JSON, HTTP, and async exactly when needed. Never assume NumPy or deep learning knowledge.

## Lesson map

| ID | Topic and observable goal | Simple example / game | Build artifact |
| --- | --- | --- | --- |
| L01 | Explain next-token prediction without treating it as a truth guarantee | Finish “I drink a cup of…”; Next Word Detective | Hand-authored next-word lookup |
| L02 | Distinguish training, inference, and application memory | Count animal-food pairs; Training or Playing? | Learned counts from three sentences |
| L03 | Generate a sequence by repeating local predictions | Robot restaurant menu; Story Chain | Tiny bigram generator |
| L04 | Explain why tokens need not match words | Illustrative word pieces; Token Puzzle | Manual token-piece joiner, labeled a toy |
| L05 | Explain how temperature changes sampling probabilities | Snack raffle; Probability Arcade | Temperature transform over toy logits |
| L06 | Identify what fits in a conversation context | Backpack for chat; Memory Backpack | Bounded list of recent turns |
| L07 | Write a prompt with task, context, and output shape | Ask for a snack recipe; Prompt Kitchen | Reusable prompt builder |
| L08 | Separate system instructions from user text | Robot job description; Role Relay | Tutor and chatbot instructions |
| L09 | Explain an API request and make one hosted-model call | Ordering from a kitchen; API Courier | First live Vertex response and failure handler |
| L10 | Keep multi-turn conversations separate and reproducible | Name recall; Conversation Builder | Saved chats and bounded history |
| L11 | Display a reply as chunks and handle interruption | Postcards arriving one at a time; Stream Catcher | Streaming UI with stop and partial status |
| L12 | Compare useful responses against a rubric | Helpful versus vague replies; Response Judge | Basic chatbot acceptance set |
| L13 | Explain vectors and similarity as representations | Map of fruit features; Similarity Sort | Three-feature vector toy and cosine demo |
| L14 | Explain attention as context-dependent weighting | “The animal crossed because it was tired”; Attention Spotlight | Small manually weighted table |
| L15 | Distinguish a count model, neural weights, and a transformer | Guess then adjust; Training Gym | Optional tiny loss/weight update demo |
| L16 | Split notes into useful retrievable units | Notebook pages; Chunk Detective | Curated note chunker |
| L17 | Retrieve context before generating an answer | Library search; Retrieval Race | Keyword baseline, then optional embeddings |
| L18 | Ground claims and report insufficient evidence | Notes about a fictional club; Citation Quest | Note-grounded chat with checked source IDs |
| L19 | Explain that a tool call needs application execution | Calculator tickets; Tool or Text? | Allowlisted arithmetic tool with typed inputs |
| L20 | Recognize prompt injection in external content | A note says “ignore the teacher”; Instruction Shield | Untrusted-data handling and adversarial fixtures |
| L21 | Evaluate behavior over a repeatable set | Chatbot obstacle course; Reliability Arena | Evaluation report with failures and improvements |
| L22 | Budget input/output and handle limits | Pack a lunch under a budget; Token Budget Shop | Token counting, usage display, local limits |
| L23 | Prepare a private local app for optional hosting | Find leaked secrets; Launch Checklist | Backup, auth plan, deployment readiness report |
| L24 | Explain the complete system and choose one improvement | Teach a friend; Final Build Quest | Capstone demo and project retrospective |

## Zone progression

| Zone | Lessons | Boss outline | Reward / milestone |
| --- | --- | --- | --- |
| Prediction Playground | L01–L03 | Predict a toy story, then explain a nonsense output | Prediction Explorer; own toy generator |
| Token Arcade | L04–L06 | Choose context and sampling settings for a short chat | Context Keeper; M1 |
| Prompt Kitchen | L07–L09 | Write a clear instruction and obtain a live reply | First Live Reply; M2 |
| Chat Workshop | L10–L12 | Demonstrate name recall, streaming interruption, and one evaluation | Chat Builder; M3 |
| Model Observatory | L13–L15 | Explain similarity, attention, and one training update | Model Explorer; M4 |
| Knowledge Library | L16–L18 | Answer from notes and decline an unsupported claim | Source Detective; M5 |
| Reliability Arena | L19–L21 | Defeat an injection fixture and fix one evaluation failure | Careful Builder; M6 |
| Launch Quest | L22–L24 | Present the chatbot, its limitations, and recovery flow | Tiny Chat Graduate; M7 |

## Correctness guardrails

- Word guessing illustrates prediction; actual models operate on model-specific tokens.
- The bigram toy learns adjacent-word counts. It is not a transformer or a miniature Gemini.
- Changing a prompt or saving a chat does not retrain a hosted model.
- A higher temperature changes sampling; it does not ensure creativity or factuality. Settings vary by model.
- A context window limits the material supplied to a request. Persistent app memory and trained weights are different mechanisms.
- Embeddings represent learned patterns; distances can be useful without being universal semantic truth.
- Attention is a component of transformers. An attention display is not a full explanation of a model's answer.
- Retrieval adds source material; it does not eliminate hallucination or injection.
- Tool suggestions from a model are data until the application validates and executes them.
- Safety instructions help; prompt instructions alone are not an authorization boundary.

## Adaptive pacing

If a learner misses the same idea twice, offer a smaller example and a Python warmup before another attempt. If they explain it accurately, offer an optional challenge. Never silently raise difficulty based on elapsed time or number of AI messages.

Before a new lesson, offer one retrieval-practice question from an earlier lesson. The learner can skip it. Reviews never reset completed work.

## Optional depth track after L24

Build a tiny character-level neural language model on a small public-domain or self-authored text. Introduce arrays, gradients, train/validation splits, overfitting, and causal attention before training a tiny transformer. Run on CPU if practical, with realistic size/time constraints. Treat it as a learning experiment; the app continues to use the hosted model for useful chat.
