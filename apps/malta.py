import plotly.express as px
from dash import html
from dash import dcc
import os
import pandas as pd
import numpy as np
import json

token = 'pk.eyJ1IjoiZHlsYW56YW0iLCJhIjoiY2t2OWcxaWt3NXV4dzJvczc3cm45YTlrcCJ9.k-EnkUZMK1rybum84KDgXw'

statistic = 'median'

price_by_loc = df.groupby('locality').median()['price']
locs = np.unique(df.locality)

fn = os.path.join('apps', 'geojson.json')

print('loading json...')
with open(fn) as f:
    out = json.load(f)

features = out['features']

mids = [x['id'] for x in features if x['id'] in price_by_loc]
df = price_by_loc.loc[mids].reset_index()
ignore = ['Wardija']
df = df[~df.locality.isin(ignore)]
#df.at[0, 'price'] = 0
df['format_price'] = df.price.apply(lambda x: '€'+str(x))
import plotly.graph_objects as go

lat, lon = 35.917973, 14.409943
zmin = min(df.price)
zmin = df.price.quantile(0.05)
zmax = df.price.quantile(0.95)
fig = go.Figure(go.Choroplethmapbox(geojson=out, locations=df.locality, z=df.price, colorscale='Turbo',
                                    zmin=zmin, zmax=zmax, marker_line_width=0.1))
fig.update_layout(mapbox_style="light", mapbox_zoom=10, mapbox_accesstoken=token, mapbox_center = {"lat": lat,
                                                                                                   "lon": lon})
#fig.update_layout(mapbox_style="light", mapbox_accesstoken=token, mapbox_zoom=3, mapbox_center = {"lat": 37.0902, "lon": -95.7129})

#fig = px.choropleth(df, geojson=out, locations='locality', color='price',
#                           color_continuous_scale="Turbo",
#                           range_color=(min(df.price), max(df.price)),
#                           labels={'price':'Price EUR'}
#                          )
#fig.update_geos(fitbounds="locations", visible=False)
#fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
#fig.show()

instructions = '''
Average property price by locality.
'''

layout = html.Div([
    html.Div(instructions, id='malta-exp', className='instructions'),
    dcc.Graph(id='malta-graph', figure=fig, config={'displayModeBar': False}, animate=True)
    ], id='malta-map-area')
#layout = dcc.Graph(id='malta-graph', figure=fig, config={'displayModeBar': False, 'scrollZoom': False})

