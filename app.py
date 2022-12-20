# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from plotly.graph_objs.choroplethmapbox import ColorBar
from dash.dependencies import Input, Output, State
from IPython import embed
import plotly.graph_objects as go
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
import os
import json
import numpy as np
from data import model
from data import remax as df

dark_bg = '#1f2630'
light_bg = '#252e3f'

token = 'pk.eyJ1IjoiZHlsYW56YW0iLCJhIjoiY2t2OWcxaWt3NXV4dzJvczc3cm45YTlrcCJ9.k-EnkUZMK1rybum84KDgXw'
BASE_PATH = os.getcwd()
data_path = os.path.join(BASE_PATH, 'data')
asset_path = os.path.join(BASE_PATH, 'assets')
fn_reset_css = os.path.join(asset_path, 'reset.css')
fn_data = os.path.join(data_path, 'remax_properties.csv')
fn_geo = os.path.join(data_path, 'geojson.json')
with open(fn_geo) as f:
    coords = json.load(f)

app = Dash(__name__)
app.css.append_css({'external_url': fn_reset_css})
app.server.static_folder = 'static'  # if you run app.py from 'root-dir-name' you don't need to specify.
app.title = 'Malta Property Analysis'


def transform_types(df):
    df.Price = df.Price.astype(int)
    df.TotalRooms = df.TotalRooms.astype(int)
    df.TotalBedrooms = df.TotalBedrooms.astype(int)
    df.TotalBathrooms = df.TotalBathrooms.astype(int)
    df.TotalSqm = df.TotalSqm.astype(int)
    df.TotalIntArea = df.TotalIntArea.astype(int)
    df.TotalExtArea = df.TotalExtArea.astype(int)
    df.InsertionDate = df.InsertionDate.apply(pd.Timestamp)
    df.LastModified = df.LastModified.apply(pd.Timestamp)
    return df

df = transform_types(df)
town_province = df[['Town', 'Province']].groupby('Town').first()

price_by_loc = df.groupby(['Town', 'TransactionType']).median()['Price']
locs = np.unique(df.Town)
features = coords['features']

mids = [x['id'] for x in features if x['id'] in price_by_loc]
df_fmt = price_by_loc.loc[mids].reset_index()
df_fmt['format_price'] = df_fmt.Price.apply(lambda x: '€'+str(x))

@app.callback(
    Output('malta-fig', 'figure'),
    Input('rent-sale-tabs', 'value'),
)
def update_mapbox(trans):
    print(f'updating map: {trans}')

    df_trans = df_fmt[df_fmt.TransactionType==trans]

    lat, lon = 35.917973, 14.409943
    zmin = df_trans.Price.quantile(0.1)
    zmax = df_trans.Price.quantile(0.95)

    # burgyl, oranges, hot, YlOrBr
    colorscale = 'solar'
    fig = go.Figure(
        go.Choroplethmapbox(
            geojson=coords, 
            locations=df_trans.Town, 
            z=df_trans.Price, 
            colorscale=colorscale,
            zmin=zmin, 
            zmax=zmax, 
            marker_line_width=0.1,
            colorbar=ColorBar(
                bgcolor=light_bg,
                borderwidth=0,
                tickcolor='#ffffff',
                tickfont={"family": "Open Sans", "color": "#ffffff"},
            )
        ),
    )

    mbs = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"
    fig.update_layout(
        mapbox_style=mbs, 
        mapbox_zoom=10.1, 
        mapbox_accesstoken=token, 
        mapbox_center = {"lat": lat, "lon": lon},
        plot_bgcolor=light_bg,
        paper_bgcolor=light_bg,
        height=700,
        margin={'b': 20, 'l': 0, 'r': 120, 't': 20},
        dragmode=False,
    )
    return fig

def load_mapbox():
    graph = dcc.Graph(
            id='malta-fig', 
            config={
                'displayModeBar': False, 
                #'scrollZoom': False,
            }, 
            #animate=True,
            style={
                'width': '70%',
                'float': 'right',
            }
        )

    return graph 

@app.callback(
    Output('loc-hist-fig', 'figure'),
    Input('beds-quote-slider', 'value'),
    Input('loc-quote-dd', 'value'),
    Input('type-quote-dd', 'value'),
    Input('rent-sale-tabs', 'value'),
)
def update_hist(beds, town, prop_type, trans):
    df_subset = df[
        (df.Town==town)
        &(df.PropertyType==prop_type)
        &(df.TransactionType==trans)
        #&(df.TotalBedrooms==beds)
    ]
    fig = px.histogram(
        df_subset,
        x='Price',
        height=150,
        title = 'asdasdasd'
    )
    fig.update_yaxes(visible=False)
    #fig.update_layout(showlegend=False)
    fig.update_layout(
        plot_bgcolor=light_bg,
        paper_bgcolor=light_bg,
        margin={'b': 0, 'l': 0, 'r': 0, 't': 0},
        font=dict(color="darkgray"),
        dragmode=False,
    )
    return fig

def load_histogram():
    graph = dcc.Graph(
            id='loc-hist-fig', 
            config={
                'displayModeBar': False, 
            }, 
        )

    return graph 

@app.callback(
    Output('loc-quote-dd', 'value'),
    Input('malta-fig', 'clickData'))
def display_click_data(clickData):
    return clickData['points'][0]['location'] if clickData else 'Attard'

def load_option_pane():
    layout = html.Div(
        [
            html.Div(
                dcc.Tabs(id="rent-sale-tabs", value='For Sale', children=[
                    dcc.Tab(label='For Sale', value='For Sale', className="tabval"),
                    dcc.Tab(label='For Rent', value='For Rent', className='tabval'),
                ],
                className="tab-container",
                ),
            ),
            html.Div([
            dcc.Dropdown(options=[{'label': k, 'value': k} for k in df.Town.unique()],
                         id='loc-quote-dd',
                         className='option',
                         value='Attard',
                        ),
            dcc.Dropdown(options=[{'label': k, 'value': k} for k in df.PropertyType.unique()],
                        id='type-quote-dd',
                        className='option',
                        value='Apartment',
                        ),
            dcc.Dropdown(options=[{'label': f'{i} bedrooms', 'value': i} for i in range(1, 5)],
                        id='beds-quote-slider',
                        className='option',
                        value=2,
                        ),
            html.Div(id='quote-output', className='option'),
            load_histogram(),
            ],
            id='selection-content'            
            )
        ], 
        id='selection-area'
    )
    return layout

@app.callback(
    Output('quote-output', 'children'),
    Input('beds-quote-slider', 'value'),
    Input('loc-quote-dd', 'value'),
    Input('type-quote-dd', 'value'),
    Input('rent-sale-tabs', 'value'),
)
def quote_button(beds, town, prop_type, transaction):

    X = {
        #'TotalSqm': area, 
        'TotalBedrooms': beds, 
        'Town': town, 
        'PropertyType': prop_type,
        #'TotalBathrooms': baths, 
        'Province': town_province.loc[town][0],
        'TransactionType': transaction,
    }
    X = pd.DataFrame(X, index=[0])
    out = model.predict(X)[0]

    divn = 1000 if out > 10000 else 50 
    out = int(out//divn*divn)
    return f'Estimate is €{out:,}'

if __name__ == '__main__':

    graph = load_mapbox()
    option_pane = load_option_pane()
    hist = load_histogram()


    app.layout = html.Div(
        [
            html.Div(id='header', children=[
                html.Div('Malta Property Analysis', id='title'),
            ]),
            html.Div(
                children=[
                    option_pane,
                    graph,
                ],
                style = {
                    'padding-top': '17vh', 
                    'overflow': 'auto', 
                    'display': 'flex',
                    'margin-right': '20px',
                }
            ),
            html.Div('''The publicly available data was collected from remax-malta.com and I make no claim that the data is fully up to date and
                    representative of the whole Maltese property scene. Prices shown in this page are inclusive of
                    commissions charged by Remax Malta. I have no association with Remax Malta.''', id='disclaimer'),
        ], 
        id='malta-map-area',
        style={
            'background-color': dark_bg,
            'height': '100vh'
        }
    )


    app.run_server(debug=True)
