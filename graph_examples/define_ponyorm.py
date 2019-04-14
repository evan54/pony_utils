from pony import orm
from pony.orm import Required, Optional, db_session, composite_key, Set
from decimal import Decimal


###############################################################################
# DATABASE DEFINITION
###############################################################################

_db = orm.Database()


class Table1(_db.Entity):
    name = Required(str)
    table2s = Set('Table2')


class Table2(_db.Entity):
    height = Required(Decimal)
    length = Required(Decimal)
    table1 = Optional('Table1')
    composite_key(height, length, table1)


###############################################################################
# CONNECT TO DATABASE
###############################################################################
orm.set_sql_debug(True)
_db.bind(provider='sqlite', filename=':memory:', create_db=True)
_db.generate_mapping(create_tables=True)

commit = _db.commit
select = orm.select
entities = _db.entities

# hack to overcome pyflakes thinking that variables aren't used
with db_session:
    Table2(height=2, length=1)

with db_session:
    Table2.exists(height=2, length=1)
