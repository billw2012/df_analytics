# from flask import Flask, jsonify, abort, make_response, request, url_for
import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import pprint
import os
import requests
import threading
import random
import gc

db_filename = 'db.xlsx'


def main(debug):
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
        return flask.make_response(flask.jsonify({'error': error}), 404)

    # e.g.:
    # {
    # 	"tick": 12323123,
    # 	"dwarf": "bill the dwarf",
    # 	"stress": 32008
    # }
    @server.route('/<db_sheet>/add', methods=['POST'])
    def add_data(db_sheet):
        if not flask.request.json:
            abort(400)
        if db_sheet not in db.keys():
            print(f"Creating sheet {db_sheet}")
            db[db_sheet] = pd.DataFrame()
        # if "timestamp" in flask.request.json:
        #     flask.request.json["timestamp"] = pd.to_datetime(flask.request.json["timestamp"], dayfirst=True, exact=True, format="%d/%m/%Y", errors='ignore')
        db[db_sheet] = db[db_sheet].append(flask.request.json, ignore_index=True)
        nice_text = pprint.pformat(flask.request.json)
        print(f"Added data to sheet {db_sheet}: {nice_text}")
        return nice_text, 201

    app = dash.Dash(__name__, server=server)

    def serve_layout():
        sheets = [*db]
        default = None
        if sheets:
            default = sheets[0]
        return html.Div([
            html.Div([
                dcc.Dropdown(
                    id='sheet-dropdown',
                    options=[{'label': v, 'value': v} for v in sheets],
                    value=default
                    # TODO: set default value
                ),
                dcc.Dropdown(
                    id='metric-dropdown'
                )
                #, dcc.RangeSlider(id='time-rangeslider')
            ]),
            dcc.Graph(id='all-graph', animate=True),
            #dcc.Graph(id='average-graph'),
            dcc.Interval(id='interval', interval=5000, n_intervals=0)
        ])

    app.layout = serve_layout

    @app.callback(
        dash.dependencies.Output('metric-dropdown', 'options'),
        [dash.dependencies.Input('sheet-dropdown', 'value')])
    def update_metric_dropdown(sheet):
        if sheet in db:
            return [{'label': v, 'value': v} for v in db[sheet].columns if not v in ['dwarf', 'timestamp', 'tick']]
        return []

    @app.callback(
        dash.dependencies.Output('all-graph', 'figure'),
        [dash.dependencies.Input('metric-dropdown', 'value'),
        dash.dependencies.Input('interval', 'n_intervals')],
        [dash.dependencies.State('sheet-dropdown', 'value')])
    def update_all_graph(metric, interval, sheet):
        try:
            df = db[sheet]
            # Split by dwarf
            dwarfs = df.dwarf.unique()
            data = []
            
            for dwarf in dwarfs:
                dwarf_metric = df[df.dwarf == dwarf]
                data.append(go.Scatter(
                        x=dwarf_metric.tick,
                        y=dwarf_metric[metric],
                        name=dwarf,
                        marker=go.Marker(color='rgb(55, 83, 109)')))
            return go.Figure(
                data=data,
                layout=go.Layout(
                    title=metric,
                    showlegend=True,
                    #legend=go.Legend(x=0, y=1.0),
                    xaxis=dict(range=[max(df.tick) - 30,max(df.tick)]), yaxis=dict(range=[min(df[metric]),max(df[metric])])
                    # margin=go.Margin(l=40, r=0, t=40, b=30)
                )
            )
        except:
            return None

    if debug:
        debug_data_thread = None
        stop_debug_data_thread_event = threading.Event()
        def debug_data_thread_fn():
            dwarfs = ['jay', 'bob', 'bill', 'alice', 'gwen', 'urist', 'mcbob', 'jim', 'xander', 'john', 'joe', 'lit', 'web', 'alex', 'sam', 'rick']
            tick = 1
            s = requests.Session()
            while not stop_debug_data_thread_event.wait(5):
                for dwarf in dwarfs:
                    r = s.post("http://127.0.0.1:8050/debug/add", json={
                        'tick': tick, 
                        'dwarf': dwarf, 
                        'stress': random.randint(-100000, 100000),
                        'focus': random.randint(-10000, 10000)
                        })
                    r.raise_for_status()
                tick = tick + 1
        debug_data_thread = threading.Thread(None, debug_data_thread_fn)
        debug_data_thread.start()
        app.run_server()
        stop_debug_data_thread_event.set()
        debug_data_thread.join()
    else:
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
    main(debug=True)
