# from flask import Flask, jsonify, abort, make_response, request, url_for
import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import pprint
import os

db_filename = 'db.xlsx'
def main():
    db = {}
    try:
        with pd.ExcelFile(db_filename) as xls:
            print(f"Loading database {db_filename}")
            for sheet in xls.sheet_names:
                print(f"  Loading sheet {sheet}")
                db[sheet] = pd.read_excel(xls, sheet)
    except ImportError as err:
        print("Database import error: " + str(err))
    except FileNotFoundError:
        print("No database found")
    except: # corrupt file?
        print(f"Database load failed, reseting db file {db_filename}")
        db = {}

    server = flask.Flask(__name__)

    @server.errorhandler(404)
    def not_found(error):
        return flask.make_response(flask.jsonify({'error': 'Not found'}), 404)

    # e.g.:
    # {
    # 	"year": 123,
    # 	"tick_in_year": 2244,
    # 	"dwarf": "bill the dwarf",
    # 	"stress": 32008
    # }
    @server.route('/<sheet>/add', methods=['POST'])
    def add_data(sheet):
        if not flask.request.json:
            abort(400)
        if not sheet in db.keys():
            print(f"Creating sheet {sheet}")
            db[sheet] = pd.DataFrame()
            #flask.request.json)
        #else:
        db[sheet] = db[sheet].append(flask.request.json, ignore_index=True)
        nice_text = pprint.pformat(flask.request.json)
        print(f"Added data to sheet {sheet}: {nice_text}")
        return nice_text, 201

    app = dash.Dash(__name__, server=server)

    df = pd.read_csv(
        'https://gist.githubusercontent.com/chriddyp/'
        'cb5392c35661370d95f300086accea51/raw/'
        '8e0768211f6b747c0db42a9ce9a0937dafcbd8b2/'
        'indicators.csv')

    available_indicators = df['Indicator Name'].unique()

    app.layout = html.Div([
        html.Div([

            html.Div([
                dcc.Dropdown(
                    id='xaxis-column',
                    options=[{'label': i, 'value': i} for i in available_indicators],
                    value='Fertility rate, total (births per woman)'
                ),
                dcc.RadioItems(
                    id='xaxis-type',
                    options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                    value='Linear',
                    labelStyle={'display': 'inline-block'}
                )
            ],
            style={'width': '48%', 'display': 'inline-block'}),

            html.Div([
                dcc.Dropdown(
                    id='yaxis-column',
                    options=[{'label': i, 'value': i} for i in available_indicators],
                    value='Life expectancy at birth, total (years)'
                ),
                dcc.RadioItems(
                    id='yaxis-type',
                    options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                    value='Linear',
                    labelStyle={'display': 'inline-block'}
                )
            ],style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
        ]),

        dcc.Graph(id='indicator-graphic'),

        dcc.Slider(
            id='year--slider',
            min=df['Year'].min(),
            max=df['Year'].max(),
            value=df['Year'].max(),
            step=None,
            marks={str(year): str(year) for year in df['Year'].unique()}
        )
    ])

    @app.callback(
        dash.dependencies.Output('indicator-graphic', 'figure'),
        [dash.dependencies.Input('xaxis-column', 'value'),
        dash.dependencies.Input('yaxis-column', 'value'),
        dash.dependencies.Input('xaxis-type', 'value'),
        dash.dependencies.Input('yaxis-type', 'value'),
        dash.dependencies.Input('year--slider', 'value')])
    def update_graph(xaxis_column_name, yaxis_column_name,
                    xaxis_type, yaxis_type,
                    year_value):
        dff = df[df['Year'] == year_value]

        return {
            'data': [go.Scatter(
                x=dff[dff['Indicator Name'] == xaxis_column_name]['Value'],
                y=dff[dff['Indicator Name'] == yaxis_column_name]['Value'],
                text=dff[dff['Indicator Name'] == yaxis_column_name]['Country Name'],
                mode='markers',
                marker={
                    'size': 15,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'}
                }
            )],
            'layout': go.Layout(
                xaxis={
                    'title': xaxis_column_name,
                    'type': 'linear' if xaxis_type == 'Linear' else 'log'
                },
                yaxis={
                    'title': yaxis_column_name,
                    'type': 'linear' if yaxis_type == 'Linear' else 'log'
                },
                margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
                hovermode='closest'
            )
        }
    app.run_server()
    #try:
    if os.path.isfile(db_filename):
        os.remove(db_filename)
    if len(db) > 0:
        with pd.ExcelWriter("db.xlsx") as xls:
            print("Saving database db.xlsx")
            for sheet, df in db.items():
                print(f"  Saving sheet {sheet}")
                df.to_excel(xls, sheet_name=sheet)
    #except:
    #    print("Couldn't save database")
    #    pass


if __name__ == '__main__':
    main()