import graphviz as gv

try:
    from .db_loader import db, db_session, entities
except ModuleNotFoundError:
    from db_loader import db, db_session, entities


def get_port(s):
    return 'port="' + s.replace(' ', '_') + '"'


def calculate_graph():

    s = gv.Graph('graph', node_attr={'shape': 'plaintext'}, engine='neato',
                 graph_attr={'splines': 'true', 'overlap': 'false'})

    edges = []

    for entity in db.entities:

        table_def = '<table border="0" cellborder="1" cellspacing="0">'
        header = (f'<tr><td bgcolor="black"><font color="white">{entity}'
                  '</font></td></tr>')

        attrs = ''
        for attr in db.entities[entity]._attrs_:
            name = attr.name
            port = get_port(name)
            attrs += f'<tr><td {port}>{name}</td></tr>'
            # if isinstance(attr, db.Set):
            if attr.py_type in db.entities.values():
                edges.append((f'{entity}:{attr.name}',
                              f'{attr.py_type.__name__}:id'))

        s_struct = '<' + table_def + header + attrs + '</table>>'
        s.node(entity, s_struct)

    s.edges(edges)

    s.attr(overlap='false')
    s.view(directory='/tmp/')


if __name__ == '__main__':
    calculate_graph()
