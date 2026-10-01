# M1: your first working learning app

M1 is implemented. Open the running local app at [Tiny Chat Lab](http://127.0.0.1:8001). Learn, Build, My chatbot, and Settings are available. Real Google calls arrive in M2.

## Your first ten minutes

1. On Home, try the tea / socks / moon prediction.
2. Start L01. Write your guess, read the explanation, and copy the Python example.
3. Run the example locally. Use “I read it” to save reading progress and open the game.
4. Play three rounds and read feedback. Try the quiz; two correct answers passes.
5. Open Build, add the robot prediction in your local Python file, and mark “I tried the build mission.” This is self-reported practice.
6. Save what changed and what you learned in the journal. Return to the learning path to see your progress.

Hints and retries are part of learning. Revealed game/quiz answers are recorded as studied, with no XP until you pass a practice attempt. Replaying passed activities never duplicates XP.

## The Python pieces you now own

| File | Plain-language job |
| --- | --- |
| [main.py](../app/main.py) | A route is a Python function connected to a URL. It reads a request and sends a response. |
| [content.py](../app/content.py) | Loads JSON and checks it before making the course available. |
| [progress.py](../app/progress.py) | Checks answers, records attempts, and awards XP once. |
| [db.py](../app/db.py) | Opens SQLite and uses transactions so related writes succeed together. |
| [demo.py](../app/demo.py) | Chooses a hand-written reply from a few conditions. |
| [lesson.html](../app/templates/lesson.html) | A Jinja template inserts lesson data into a reusable page. |
| [activities.js](../app/static/js/activities.js) | Shows the same choice-round interface for games and quizzes. |

The backend has Python; the browser has HTML/CSS and small JavaScript modules. Lessons are data. All six lessons use the same templates and activity renderer.

## Follow one real message

1. Type “What is a token?” in My chatbot.
2. `chat.js` sends JSON like `{"message": "What is a token?"}` to `POST /api/demo/messages`.
3. FastAPI validates that the message is a nonblank string under the limit.
4. The route calls `reply(message)` in `app/demo.py`.
5. The function finds `token` in the message and returns a string.
6. FastAPI sends JSON back; JavaScript displays the string as safe text.

Notice the boundary: the page handles typing and display; Python decides the reply. In M2, that reply decision moves to a Google model call on the Python server. The browser still sends a message and receives text.

## Your small ownership task

Teach the demo about Python. Open `app/demo.py`, find `reply()`, and add this condition **above the final fallback**:

```python
if "python" in text:
    return "Python is the language powering this little lab."
```

Predict what happens for “What is Python?” and “What is a token in Python?” before testing. The first matching `if` that returns ends the function, so condition order matters. Restart the server after editing Python, then send those messages.

Optional variation: add a rule for your own favorite topic, then explain why the demo is a rule-based chatbot rather than a trained model.

## Start or restart the app

From `D:\Work\Codex\llm-playground`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8001
```

Stop the server with Ctrl+C in its terminal. You can also use `./run.ps1`, or `./run.ps1 -Port 8002` if the default port is occupied. The helper creates a virtual environment and installs runtime dependencies when the environment does not exist.

The local database is `data/tiny-chat.db`. Progress and journal entries survive app restarts. Prediction drafts, tutor question drafts, and the demo conversation live only in the current browser tab's session storage. Do not confuse that demo history with model memory: the demo reply function does not read previous messages.

## Changing lessons through prompts

Ask for the change in this chat. The assistant edits the appropriate lesson JSON, preserves stable IDs, increments its version, checks the content, and regenerates the reading copy. In Settings, use “Reload lesson content”; refresh the lesson page afterward. A malformed update does not replace the active course. Completed lessons keep their completion snapshot and offer optional review for new versions.

If an assessed question changes, use a new round ID. The app compares question identities when displaying current activity results; an old passed activity does not pretend to assess a new question. Historical attempts and earned XP remain saved.

M1 validates reloads but does not include the later draft editor, revision-snapshot publisher, or rollback workspace. Keep the prior JSON file or use version control when making larger course edits.

## What is next

M2 will configure your actual Google Cloud auth mode, verify a short live call, connect Ask AI, and author L07–L09. No reusable Google credential is read, displayed, or required by M1.
