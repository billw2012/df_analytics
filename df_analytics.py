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

    app.layout = html.Div([
        html.Div([
            dcc.Dropdown(
                id='metric-dropdown'
            )
            #, dcc.RangeSlider(id='time-rangeslider')
        ]),
        dcc.Graph(id='all-graph'),
        #dcc.Graph(id='average-graph'),
        dcc.Interval(id='interval', interval=1000, n_intervals=0)
    ])

    @app.callback(
        dash.dependencies.Output('metric-dropdown', 'options'),
        [dash.dependencies.Input('interval', 'n_intervals')])
    def update_metric_dropdown(value):
        return [{'label': v, 'value': v} for v in [*db]]

    @app.callback(
        dash.dependencies.Output('all-graph', 'figure'),
        [dash.dependencies.Input('metric-dropdown', 'value'),
        dash.dependencies.Input('interval', 'n_intervals')])
    def update_all_graph(value):
        try:
            df = db[value]
            return go.Figure(
                data=[
                    go.Scatter(
                        x=[1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003,
                        2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012],
                        y=[219, 146, 112, 127, 124, 180, 236, 207, 236, 263,
                        350, 430, 474, 526, 488, 537, 500, 439],
                        name='Rest of world',
                        marker=go.Marker(
                            color='rgb(55, 83, 109)'
                        )
                    ),
                    go.Bar(
                        x=[1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003,
                        2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012],
                        y=[16, 13, 10, 11, 28, 37, 43, 55, 56, 88, 105, 156, 270,
                        299, 340, 403, 549, 499],
                        name='China',
                        marker=go.Marker(
                            color='rgb(26, 118, 255)'
                        )
                    )
                ],
                layout=go.Layout(
                    title='US Export of Plastic Scrap',
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