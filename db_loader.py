import sys
import importlib.util
from pathlib import Path


def _import_database():
    if len(sys.argv) < 2:
        raise ValueError(
            'Need Database definition as well, typical use:',
            'python -m mydash.ponyorm_app.<FUNCTION> db_definition.py')
    db_file = sys.argv[1]
    pnfn = Path(db_file).absolute()
    file_path = str(pnfn)
    module_name = pnfn.name
    if '.py' == module_name[-3:]:
        module_name = module_name[:-3]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    db = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db)
    db_session = db.db_session
    entities = db.entities
    return db, db_session, entities


db, db_session, entities = _import_database()
