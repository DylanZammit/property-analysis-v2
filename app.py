# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from plotly.graph_objs.choroplethmapbox import ColorBar
from IPython import embed
import plotly.graph_objects as go
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
import os
import json
import numpy as np

dark_bg = '#1f2630'
light_bg = '#252e3f'

token = 'pk.eyJ1IjoiZHlsYW56YW0iLCJhIjoiY2t2OWcxaWt3NXV4dzJvczc3cm45YTlrcCJ9.k-EnkUZMK1rybum84KDgXw'
BASE_PATH = os.getcwd()
data_path = os.path.join(BASE_PATH, 'data')
asset_path = os.path.join(BASE_PATH, 'assets')
fn_reset_css = os.path.join(asset_path, 'reset.css')
fn_data = os.path.join(data_path, 'remax_properties.csv')
fn_geo = os.path.join(data_path, 'geojson.json')

app = Dash(__name__)
app.css.append_css({'external_url': fn_reset_css})
app.server.static_folder = 'static'  # if you run app.py from 'root-dir-name' you don't need to specify.
app.title = 'Malta Property Analysis'


def get_data():
    df = pd.read_csv(fn_data, index_col=0)

    #DO NOT CLEAN HERE
    df = df[df.Price!='POR']
    df = df[df.Price > 100000]

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

def load_mapbox():
    print('loading geo-json...')
    with open(fn_geo) as f:
        coords = json.load(f)

    price_by_loc = df.groupby('Town').median()['Price']
    locs = np.unique(df.Town)
    features = coords['features']

    mids = [x['id'] for x in features if x['id'] in price_by_loc]
    df_fmt = price_by_loc.loc[mids].reset_index()
    df_fmt['format_price'] = df_fmt.Price.apply(lambda x: '€'+str(x))

    lat, lon = 35.917973, 14.409943
    zmin = df_fmt.Price.quantile(0.1)
    zmax = df_fmt.Price.quantile(0.8)
    print(zmin, zmax)

    # burgyl, oranges, hot, YlOrBr
    colorscale = 'solar'
    fig = go.Figure(
        go.Choroplethmapbox(
            geojson=coords, 
            locations=df_fmt.Town, 
            z=df_fmt.Price, 
            colorscale=colorscale,
            zmin=zmin, 
            zmax=zmax, 
            marker_line_width=0.1,
            colorbar=ColorBar(
                bgcolor=light_bg,
                borderwidth=0,
                tickcolor='#ffffff',
            )
        ),
    )

    mbs = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"
    fig.update_layout(
        mapbox_style=mbs, 
        mapbox_zoom=10.3, 
        mapbox_accesstoken=token, 
        mapbox_center = {"lat": lat, "lon": lon},
        plot_bgcolor=light_bg,
        paper_bgcolor=light_bg,
        height=800,
        margin={'b': 0, 'l': 0, 'r': 0, 't': 0},
    )
    graph = dcc.Graph(
            id='malta-graph', 
            figure=fig,
            #figure={'data': fig, 'layout': {}}, 
            config={
                'displayModeBar': False, 
                #'scrollZoom': False,
            }, 
            animate=True,
            style={
                'width': '70%',
                'float': 'right',
            }
        )

    return graph 

def load_option_pane():
    layout = html.Div(
        [
            
            dcc.Dropdown(id='loc-quote-dd',
                          className='option',
                         #placeholder='Choose locality',
                         value='Attard',
                         options=[
                             {'label': k, 'value': k} for k in np.unique(df.Town)
                         ],
                         #className='custom-select',
                        ),
            dcc.Dropdown(id='type-quote-dd',
                         className='option',
                         #placeholder='Choose property type',
                         value='Apartment',
                         options=[
                             {'label': k, 'value': k} for k in np.unique(df.PropertyType)
                         ],
                        ),
            dcc.Slider(id='beds-quote-slider',
                       min=1,
                       max=10,
                       marks={i: {'label': str(i)} for i in range(1, 11)},
                       #marks={i: {'label': str(i), 'color': '#77b0b1'} for i in range(1, 11)},
                       tooltip={"placement": "bottom", "always_visible": True},
                       step=1,
                       value=2,
                       updatemode='drag',
                       className='option',
                       included=False),
            dcc.Slider(id='area-quote-slider',
                       className='option',
                       min=0,
                       max=500,
                       marks={i: {'label': str(i)+'m\u00b2'} for i in range(0, 501, 100)},
                       tooltip={"placement": "bottom", "always_visible": True},
                       step=5,
                       value=150,
                       updatemode='drag',
                       included=False),
        ], 
        id='selection-area'
    )
    return layout

df = get_data()
graph = load_mapbox()
option_pane = load_option_pane()


app.layout = html.Div(
    [
        html.Div(id='header', children=[
            html.Div('Malta Properties', id='title'),
        ]),
        html.Div(
            [
                option_pane,
                graph,
            ],
            style = {'padding-top': '17vh', 'overflow': 'auto', 'display': 'flex'}
        )
    ], 
    id='malta-map-area',
    style={
        'background-color': dark_bg,
        #'background-color': '#191a1a',
        'height': '100vh'
    }
)


if __name__ == '__main__':
    app.run_server(debug=True)
