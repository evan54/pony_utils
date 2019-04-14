import datetime as dtt
import decimal

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from mydash.component import Row, Col, Button

try:
    from .db_loader import db, db_session, entities
except ModuleNotFoundError:
    from db_loader import db, db_session, entities


@db_session
def get_table_summary():
    tables = {}
    name_size = 6
    el_size = 3
    for table in entities:
        tables[table] = entities[table].select().count()
    header = [Row([Col(html.H3('Table Name'), size=name_size),
                   Col(html.H3('Elements'), size=el_size)])]
    tables = [Row([Col(key, size=name_size), Col(tables[key], size=el_size)])
              for key in tables]
    return html.Div(header + tables)


class MyButtons:

    types = ['add', 'modify', 'delete']
    names = ['Add New', 'Modify', 'Delete']

    def __init__(self, table_name):
        self.field_ids = [f'{t}-button-{table_name}' for t in self.types]
        self.table_name = table_name

    def get_buttons(self):
        return [Button(id=id_, children=name, className='btn',
                       n_clicks_timestamp=0)
                for id_, name in zip(self.field_ids, self.names)]

    def get_inputs(self):
        return [Input(component_id, 'n_clicks_timestamp')
                for component_id in self.field_ids]


@db_session
def label(val, use_label=True):
    if use_label and hasattr(val, 'label'):
        return val.label()
    elif isinstance(val, dtt.datetime):
        date_str = val.strftime('%Y-%m-%d')
        no_hour_min = val.hour == val.minute == 0
        time_str = '' if no_hour_min else ' ' + val.strftime('%H:%M')
        return date_str + time_str
    elif isinstance(val, str):
        return val
    elif val is not None:
        return repr(val)


def get_table_and_id_from_repr(entry_repr):
    if '[' in entry_repr:
        start_bracket = entry_repr.index('[')
        end_bracket = entry_repr.index(']')
        table_name = entry_repr[1:start_bracket]
        id_ = int(entry_repr[start_bracket+1:end_bracket])
        return table_name, id_


@db_session
def get_entry_from_repr(entry_repr):
    table_name_id = get_table_and_id_from_repr(entry_repr)
    if table_name_id:
        return entities[table_name_id[0]][table_name_id[1]]


class PonyTable:

    ID = 0
    SET = 1
    REFERENCE = 2
    DATE = 3
    STR = 4
    BOOL = 5
    DECIMAL = 6

    def __init__(self, table_name):
        self.table_name = table_name

    @property
    @db_session
    def table(self):
        return entities[self.table_name]

    @property
    @db_session
    def table_cols(self):
        return [a.name for a in self.table._attrs_]

    @db_session
    def _unpack_args(self, args):
        output = {}
        for col, arg in zip(self.table_cols, args):
            col_type = self._get_type(col)
            if col_type is self.SET:
                arg = [get_entry_from_repr(e) for e in arg]
            elif col_type is self.REFERENCE:
                print(arg, type(arg))
                arg = get_entry_from_repr(arg)
            elif col_type is self.DATE:
                print(arg)
            elif col_type is self.BOOL:
                arg = len(arg) > 0
                print(arg)
            output[col] = arg
        return output

    def _get_type(self, key):
        attr = self.get_attribute(key)
        attr_type = attr.py_type
        if isinstance(attr, db.Set):
            return self.SET
        elif attr_type in entities.values():
            return self.REFERENCE
        elif attr_type is dtt.datetime:
            return self.DATE
        elif attr_type is str:
            return self.STR
        elif attr_type is bool:
            return self.BOOL
        elif attr_type is decimal.Decimal:
            return self.DECIMAL
        elif key == 'id':
            return self.ID
        else:
            raise ValueError(f'Unknown type for {self.table_name}: {key} - '
                             f'({attr}, {attr_type})')

    def none_val(self, key):
        attr_type = self._get_type(key)
        if attr_type == self.SET:
            return []
        elif attr_type == self.REFERENCE:
            return None
        elif attr_type == self.DATE:
            return None
        elif attr_type == self.STR:
            return ''
        elif attr_type == self.BOOL:
            raise ValueError('BOOL type cannot have a None equivalent')
        elif attr_type == self.DECIMAL:
            raise ValueError('DECIMAL type cannot have a None equivalent')
        elif key == 'id':
            raise ValueError('ID type cannot have a None equivalent')

    @db_session
    def get_entry(self, id_):
        return self.table[id_].to_dict(related_objects=True,
                                       with_collections=True)

    @db_session
    def get_attribute(self, key):
        return getattr(self.table, key)

    def is_unique(self, key):
        return self.get_attribute(key).is_unique

    def is_required(self, key):
        return self.get_attribute(key).is_required

    @db_session
    def add_entry(self, args):
        e_dict = self._unpack_args(args)
        if 'id' in e_dict:
            e_dict.pop('id')
        entities[self.table_name](**e_dict)

    @db_session
    def modify_entry(self, args):
        e_dict = self._unpack_args(args)
        current_entry = entities[self.table_name][e_dict['id']]
        for key in self.table_cols:
            print(current_entry, key,
                  e_dict[key] if key in e_dict else self.none_val(key))
            setattr(current_entry, key,
                    e_dict[key] if key in e_dict else self.none_val(key))

    @db_session
    def delete_entry(self, args):
        e_dict = self._unpack_args(args)
        if e_dict['id']:
            entities[self.table_name][e_dict['id']].delete()


class EntryForm:

    WHITE = {'background': '#fff'}
    GREY = {'background': '#f5f5f5'}
    FULL_WIDTH = {'width': '100%'}

    col_size = 2

    def __init__(self, table_name=None):
        self.table = PonyTable(table_name)

        self._dummy_output_id = f'dummy-output-{table_name}'
        self.state_list = [
            State(*a) for a in self._get_component_id_property()]
        self.form_id = f'{self.table.table_name}-database-entry'

    def _get_field_entry_id(self, key):
        return f'formid-{self.table.table_name}-{key}'

    def _get_component_id_property(self):
        s = []
        for key in self.table.table_cols:
            field_type = self.table._get_type(key)
            component_id = self._get_field_entry_id(key)
            if field_type == self.table.ID:
                component_property = 'children'

            elif field_type == self.table.DATE:
                component_property = 'date'

            elif field_type in [self.table.STR, self.table.DECIMAL,
                                self.table.REFERENCE, self.table.SET]:
                component_property = 'value'

            elif field_type == self.table.BOOL:
                component_property = 'values'
            s.append((component_id, component_property))
        return s

    def _get_component_for(self, key, val):
        field_type = self.table._get_type(key)
        value = self._get_value_for(key, val)

        if field_type == self.table.ID:
            component = html.Div(id=self._get_field_entry_id('id'),
                                 children=value)

        elif field_type == self.table.SET:
            attr = self.table.get_attribute(key)
            attr_type = attr.py_type
            options = [{'label': entry.label(), 'value': repr(entry)} for
                       entry in attr_type.select().fetch()]
            component = dcc.Dropdown(id=self._get_field_entry_id(key),
                                     options=options,
                                     value=value,
                                     multi=True)

        elif field_type == self.table.REFERENCE:
            attr = self.table.get_attribute(key)
            attr_type = attr.py_type
            options = [{'label': entry.label(), 'value': repr(entry)} for entry
                       in attr_type.select().fetch()]
            component = dcc.Dropdown(id=self._get_field_entry_id(key),
                                     options=options, value=value)

        elif field_type == self.table.DATE:
            date_picker_kwargs = dict(
                id=self._get_field_entry_id(key),
                display_format='D MMM YYYY',
                clearable=True, with_portal=True,
            )
            if val:
                date_picker_kwargs['date'] = value
            component = dcc.DatePickerSingle(**date_picker_kwargs)

        elif field_type == self.table.STR:
            component = dcc.Input(id=self._get_field_entry_id(key),
                                  placeholder=value,
                                  value=value,
                                  style=self.FULL_WIDTH)

        elif field_type == self.table.BOOL:
            component = dcc.Checklist(id=self._get_field_entry_id(key),
                                      options=[{'label': key, 'value': key}],
                                      values=value)

        elif field_type == self.table.DECIMAL:
            component = dcc.Input(id=self._get_field_entry_id(key),
                                  placeholder=value,
                                  value=value,
                                  style=self.FULL_WIDTH)
        return component

    def _get_value_for(self, key, val):
        field_type = self.table._get_type(key)
        if field_type in [self.table.ID, self.table.DATE]:
            return val
        if field_type in [self.table.STR, self.table.DECIMAL]:
            return val if val else ''
        elif field_type == self.table.SET:
            return None if val is None else [repr(v) for v in val]
        elif field_type == self.table.REFERENCE:
            return repr(val)
        elif field_type == self.table.BOOL:
            return [key] if val else []

    def _get_header(self):
        return Row(html.H3(id=f'entry-header-table-{self.table.table_name}',
                           children=self.table.table_name))

    def get_form(self, id_=None):
        return html.Div(self.get_form_children(id_), id=self.form_id)

    @db_session
    def get_form_children(self, id_=None):
        """
        Takes in a table name and an id and produces a form to fill out
        If an id_ is passed it populates the form with the values.
        """
        e_dict = {} if id_ is None else self.table.get_entry(id_)
        children = [self._get_header()]
        bkg_toggle = 0
        for key in self.table.table_cols:
            val = e_dict.get(key)
            component = self._get_component_for(key, val)
            if bkg_toggle:
                bkg = self.WHITE
            else:
                bkg = self.GREY
            bkg_toggle = 1 - bkg_toggle
            star = '*' if self.table.is_unique(key) else ''
            hat = '^' if self.table.is_required(key) else ''
            child = Row([Col(key + star + hat, size=self.col_size),
                         Col(component)], style=bkg)
            children.append(child)
        return children

    def get_dummy_output(self):
        return html.Div(id=self._dummy_output_id, hidden=True)


@db_session
def initialise():
    entry_forms = {table_name: EntryForm(table_name)
                   for table_name in entities}
    dummy_outputs = [ef.get_dummy_output() for ef in entry_forms.values()]
    _options = [{'label': table_name, 'value': table_name}
                for table_name in entities]
    table_dropdown = dcc.Dropdown(id='table-dropdown', options=_options)
    inspect_entry = Col(size=12, id='inspect-entry')
    entry_dropdown = dcc.Dropdown(id='entry-dropdown')
    return (entry_forms, dummy_outputs, table_dropdown, entry_dropdown,
            inspect_entry)


(entry_forms, dummy_outputs, table_dropdown, entry_dropdown,
 inspect_entry) = initialise()


@db_session
def _get_entry_dropdown_options(table_name):
    if table_name:
        entries = entities[table_name].select()
        options = [{'label': entry.label(), 'value': repr(entry)}
                   for entry in entries]
    else:
        options = []
    return options


layout = Row([
            Col(size=4, children=get_table_summary()),
            Col(size=8, children=[
                table_dropdown,
                entry_dropdown,
                html.Div(id='entry-content')
            ] + dummy_outputs
            )
        ])


@db_session
def modify_entry(add_timestamp, modify_timestamp, remove_timestamp, table_name,
                 output, *args):
    print('modify_entry')
    if table_name:
        output = output + 1 if output else 1
        t = PonyTable(table_name)
        if add_timestamp > max(modify_timestamp, remove_timestamp):
            print('Add', modify_timestamp)
            t.add_entry(args)
        elif modify_timestamp > max(add_timestamp, remove_timestamp):
            print('Modify', modify_timestamp)
            t.modify_entry(args)
        elif remove_timestamp > max(add_timestamp, modify_timestamp):
            print('Remove', remove_timestamp)
            t.delete_entry(args)
    return output


def assign_callbacks(app):

    @app.callback(Output(entry_dropdown.id, 'options'),
                  [Input(table_dropdown.id, 'value')] +
                  [Input(d.id, 'children') for d in dummy_outputs])
    def choose_table(table_name, *args):
        print('choose_table')
        return _get_entry_dropdown_options(table_name) if table_name else []

    @app.callback(Output(entry_dropdown.id, 'value'),
                  [Input(table_dropdown.id, 'value')],
                  [State(entry_dropdown.id, 'value')])
    def reset_entry_value(new_table_name, current_entry_repr):
        print('reset_entry_value', new_table_name, current_entry_repr)
        if current_entry_repr:
            table_name, id_ = get_table_and_id_from_repr(current_entry_repr)
            if table_name == new_table_name:
                return current_entry_repr
        return None

    @app.callback(Output('entry-content', 'children'),
                  [Input(entry_dropdown.id, 'value'),
                  Input(table_dropdown.id, 'value')])
    def choose_entry(entry_repr, table_name):
        print('choose_entry', entry_repr, table_name)
        id_ = get_table_and_id_from_repr(entry_repr)[1] if entry_repr else None
        if table_name:
            ef = entry_forms[table_name]
            form = ef.get_form(id_)
            buttons = MyButtons(table_name).get_buttons()
            return html.Div([form] + buttons)

    for table_name, ef in entry_forms.items():
        app.callback(Output(f'dummy-output-{table_name}', 'children'),
                     MyButtons(table_name).get_inputs(),
                     [State('table-dropdown', 'value'),
                      State(f'dummy-output-{table_name}', 'children')]
                     + ef.state_list)(modify_entry)

    return app


if __name__ == '__main__':
    app = dash.Dash(__name__)
    app.css.append_css({
        'external_url': ('https://stackpath.bootstrapcdn.com/'
                         'bootstrap/4.1.1/css/bootstrap.min.css')
    })

    app.layout = html.Div(
        className='container-fluid',
        children=[
            dcc.Location(id='url', refresh=False),
            html.Div(id='page-content'),
        ])

    @app.callback(Output('page-content', 'children'),
                  [Input('url', 'pathname')])
    def route(pathname):
        if pathname == '/':
            return layout
        else:
            return 'Σφάλμα: 404'

    app.config.supress_callback_exceptions = True

    app = assign_callbacks(app)
    app.run_server(debug=True)
