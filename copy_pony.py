import re
from pathlib import Path

try:
    from .db_loader import db  # , db_session, entities
except ModuleNotFoundError:
    from db_loader import db  # , db_session, entities


def copy():
    db_file = Path(db.__file__)

    with open(db_file, 'r') as f:
        file_content = f.read()

    for entity in db.entities:
        file_content = re.sub(fr'\b{entity}\b', f'{entity}_', file_content)

    import pdb
    pdb.set_trace()
    with open(str(db_file).replace('.py', '_.py'), 'w') as f:
        f.write(file_content)


if __name__ == '__main__':
    copy()
