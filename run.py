from app import app, db
from app.models import User, Deck, Comment
import random


if __name__ == '__main__':
    try:
        app.run(port=5000 + random.randint(1, 50), debug=True)
    except Exception:
        app.run(port=5000 + random.randint(51, 101), debug=True)
    finally:
        app.shell_context_processor(
            {'db': db, 'User': User, 'Comment': Comment, 'Deck': Deck})
