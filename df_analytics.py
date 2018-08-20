# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html

def main():
    app = dash.Dash()

    app.layout = html.Div(children=[
        html.H1(children='Dwarf Fortress Analytics v0.1'),
        html.Div(children='''
            
        '''),

        dcc.Graph(
            id='example-graph',
            figure={
                'data': [
                    {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                    {'x': [1, 2, 3], 'y': [2, 4, 5],
                        'type': 'bar', 'name': u'Montréal'},
                ],
                'layout': {
                    'title': 'Dash Data Visualization'
                }
            }
        )
    ])
    app.run_server(debug=True)

if __name__ == '__main__':
    main()
