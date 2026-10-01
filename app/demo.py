"""A hand-written reply function. No model, API key, or network calls."""


def reply(message: str) -> str:
    text = message.casefold()
    if "token" in text:
        return "A token is a piece of text. It might be a whole word, part of a word, or punctuation. Try L04's text puzzle to see the difference. This reply comes from a Python rule, not an AI model."
    if "train" in text or "learn" in text:
        return "Training changes what a model has learned. Inference uses it to produce a reply. Saving a chat is a third thing: app memory. L02 lets you try all three ideas with a tiny count table."
    if "memory" in text or "remember" in text or "context" in text:
        return "Think of context as a backpack: the app selects what goes into the next request. Stored messages on the shelf are not automatically in that backpack. Explore this in L06."
    if "hello" in text or "hi" == text or "hey" in text:
        return "Hello, builder! I am a demo made from a few Python rules. Ask me about tokens, training, or context. In M2, you will replace these rules with a real Google model call."
    return "I do not have a rule for that yet. Try asking about tokens, training, or context. This honest fallback is one of the first things you can change in app/demo.py."
