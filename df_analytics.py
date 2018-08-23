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
        if "timestamp" in flask.request.json:
            flask.request.json["timestamp"] = pd.to_datetime(flask.request.json["timestamp"], origin='julian')
        #if "timestamp" in flask.request.json:
        #    db[sheet] = db[sheet].append(pd.Series(flask.request.json, index=[flask.request.json["timestamp"]]))
        #else:
        db[sheet] = db[sheet].append(flask.request.json, ignore_index=True)
        nice_text = pprint.pformat(flask.request.json)
        print(f"Added data to sheet {sheet}: {nice_text}")
        return nice_text, 201

    app = dash.Dash(__name__, server=server)

    def serve_layout():
        return html.Div([
            html.Div([
                dcc.Dropdown(
                    id='metric-dropdown',
                    options=[{'label': v, 'value': v} for v in [*db]]
                )
                #, dcc.RangeSlider(id='time-rangeslider')
            ]),
            dcc.Graph(id='all-graph'),
            #dcc.Graph(id='average-graph'),
            dcc.Interval(id='interval', interval=1000, n_intervals=0)
        ])

    app.layout = serve_layout

    # @app.callback(
    #     dash.dependencies.Output('metric-dropdown', 'options'),
    #     [dash.dependencies.Input('interval', 'n_intervals')])
    # def update_metric_dropdown(value):
    #     return [{'label': v, 'value': v} for v in [*db]]

    @app.callback(
        dash.dependencies.Output('all-graph', 'figure'),
        [dash.dependencies.Input('metric-dropdown', 'value'),
        dash.dependencies.Input('interval', 'n_intervals')])
    def update_all_graph(metric, interval):
        try:
            df = db[metric]
            # Split by dwarf
            dwarfs = df.dwarf.unique()
            data = []
            for dwarf in dwarfs:
                dwarf_metric = df[df.dwarf == dwarf]
                data.append(go.Scatter(
                        x=dwarf_metric.timestamp,
                        y=dwarf_metric.stress,
                        name=dwarf,
                        marker=go.Marker(color='rgb(55, 83, 109)')))
            return go.Figure(
                data=data,
                layout=go.Layout(
                    title='Stress',
                    showlegend=True,
                    legend=go.Legend(
                        x=0,
                        y=1.0
                    ),
                    margin=go.Margin(l=40, r=0, t=40, b=30)
                )
            )
        except:
            return None

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