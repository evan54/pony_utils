from pony import orm
from pony.orm import Required, Optional, Set, db_session, show, composite_key
from decimal import Decimal
import datetime as dtt
import pandas as pd


###############################################################################
# DATABASE DEFINITION
###############################################################################

_db = orm.Database()


class Helper:

    def __repr__(self):
        class_name = type(self).__name__
        return '<' + class_name + self.label() + '>'


###############################################################################
# INSTITUTION
###############################################################################
class Table1(Helper, _db.Entity):
    attr0 = Required(str, unique=True)
    table2s = Set('Table2')


class Table2(Helper, _db.Entity):
    name = Required(str, unique=True)
    table1 = Required('Table1')
    table6s = Set('Table6')
    notes = Optional(str)


class Table3(Helper, _db.Entity):
    name = Required(str, unique=True)
    table6s = Set('Table6')


class Table4(Helper, _db.Entity):
    number = Required(str, unique=True)
    valid_from = Required(dtt.datetime)
    valid_to = Optional(dtt.datetime)
    table6s = Required('Table6')


class Table5(Helper, _db.Entity):
    text = Required(str, unique=True)
    table6s = Required('Table6')


class Table6(Helper, _db.Entity):
    table2 = Required('Table2')
    table3 = Required('Table3')
    description = Required(str, unique=True)
    table6 = Optional('Table5')
    date_opened = Optional(dtt.datetime)
    date_closed = Optional(dtt.datetime)
    table4s = Set('Table4')
    table7s = Set('Table7')
    table8 = Required('Table8')
    table10 = Optional('Table10')


class Table7(Helper, _db.Entity):
    date = Required(dtt.datetime)
    start = Required(dtt.datetime)
    description = Required(str)
    amount = Required(Decimal)
    table10 = Required('Table10')
    table6 = Required('Table6')
    tabel14s = Set('Table14')
    table9s = Set('Table9')


###############################################################################
# ACCOUNTING
###############################################################################
class Table8(Helper, _db.Entity):
    name = Required(str)
    is_true = Required(bool)
    is_false = Required(bool)
    table11s = Set('Table11')
    table6s = Set('Table6')


class Table9(Helper, _db.Entity):
    date = Required(dtt.datetime)
    description = Required(str)
    table12s = Set('Table12')
    table11s = Set('Table11')
    table7s = Set('Table7')
    table9s = Set('Table9', reverse='table9s')


class Table10(Helper, _db.Entity):
    name = Required(str, unique=True)
    transactions = Set('Table11')
    table7s = Set('Table7')
    table6s = Set('Table6')


class Table11(Helper, _db.Entity):
    amount = Required(Decimal)
    table10 = Required('Table10')
    table8= Required('Table8')
    table9s= Set('Table9')


class Table12(Helper, _db.Entity):
    name = Required(str, unique=True)
    table9s = Set('Table9')


###############################################################################
# DOCUMENT REFERENCE STORAGE
###############################################################################
class Table13(Helper, _db.Entity):
    name = Required(str, unique=True)
    table14s = Set('Table14')


class Table14(Helper, _db.Entity):
    filename = Required(str, unique=True)
    suffix = Required(str)
    table13 = Required('Table13')
    date_added = Required(dtt.datetime)
    period_start = Optional(dtt.datetime)
    period_end = Optional(dtt.datetime)
    description = Optional(str)
    table7s = Set('Table7')


###############################################################################
# CONNECT TO DATABASE
###############################################################################
orm.set_sql_debug(False)
_db.bind(provider='sqlite', filename=':memory:', create_db=True)
_db.generate_mapping(create_tables=True)

commit = _db.commit
select = orm.select
entities = _db.entities

# hack to overcome pyflakes thinking that variables aren't used
show = show
db_session = db_session
