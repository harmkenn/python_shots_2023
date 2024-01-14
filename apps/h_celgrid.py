import streamlit as st
import pandas as pd
from numpy import pi
from datetime import datetime, timezone, timedelta
import folium
from streamlit_folium import folium_static
from folium import plugins
from apps import z_functions as zf 
import ephem
def app():
    # title of the app
    c1,c2 = st.columns((1,1))
    with c1:
        lu = st.sidebar.text_input('Lookup: ') 
        if len(lu)>=3:
            where = zf.lookup(lu)
            st.sidebar.write(where[0])
            st.sidebar.write('Lat: '+str(where[1])+' Lon: '+str(where[2]))
            st.sidebar.write('MGRS: '+where[3])
            alt = zf.elevation(where[1],where[2])
            st.sidebar.write('Alt :'+str(round(alt,2))+' Meters')

        options = ['the Sun','the Moon','Polaris','Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
        selection = st.selectbox("Celestial Object", options)
        
        if 'h_time' not in st.session_state: st.session_state['h_time'] = ephem.Date(datetime.now(timezone.utc))
        h_time = st.session_state['h_time']
        if st.button('Now'):
            h_time = ephem.Date(datetime.now(timezone.utc))
        h_time = st.text_input('UTC Time',h_time)
        st.session_state['h_time'] = h_time
        st.write(str(h_time)+'UTC')
    with c2:
        st.markdown(f'Get your position from your direction and altitude to {selection}.')
        h_az = st.number_input(f'Azimuth degrees to {selection}: ', 0.00,360.00,110.00)
        h_alt = st.number_input(f'Altitude degrees to {selection}: ',-90.00,90.00,45.00)

    # https://theskylive.com/planetarium?obj=moon#ra|9.854204231576311|dec|32.20240956176751|fov|50

    origin = ephem.Observer()
    origin.lat = '0'  # Example latitude (London, United Kingdom)
    origin.lon = '0'
    if selection == 'the Sun': 
        cel = ephem.Sun()
    elif selection == 'the Moon': 
        cel = ephem.Moon()
    elif selection == 'Polaris': 
        cel = ephem.star('Polaris') # https://theskylive.com/sky/stars/polaris-alpha-ursae-minoris-star
    elif selection == 'Mercury': 
        cel = ephem.Mercury() # https://theskylive.com/where-is-mercury
    elif selection == 'Venus': 
        cel = ephem.Venus()
    elif selection == 'Mars': 
        cel = ephem.Mars()
    elif selection == 'Jupiter': 
        cel = ephem.Jupiter()
    elif selection == 'Saturn': 
        cel = ephem.Saturn()
    elif selection == 'Uranus': 
        cel = ephem.Uranus()
    elif selection == 'Neptune': 
        cel = ephem.Neptune()
    else: out = 'Something else'
    
    cel.compute(origin)
 
    cel_azimuth = float(cel.az)*180/pi
    cel_altitude = float(cel.alt)*180/pi
    
    cel_dist = 40050*(90-cel_altitude)/360
    dist = 40050*(90-h_alt)/360*1000
    #st.write(f'sub-Celestial distace from observer: ', cel_dist)
    #st.write(f"{selection}'s Azimuth from 0,0:", cel_azimuth)
    #st.write(f"{selection}'s Altitude from 0,0:", cel_altitude)
    sub_cel = zf.vPolar(0,0,cel_azimuth,cel_dist*1000)
    st.write(f"{selection}'s Sub-Coordinates: (", str(sub_cel[0]), f",", str(sub_cel[1]), f') and ',zf.LL2MGRS(sub_cel[0],sub_cel[1])[1]  )

    
    obloc = zf.revVpolar(sub_cel[0],sub_cel[1],float(h_az),dist)

    st.write(f"Observer's Coordinates: (", str(obloc[0]), f",", str(obloc[1]), f') and ',zf.LL2MGRS(obloc[0],obloc[1])[1]  )
    st.write(f"Distance from Observer to Sun's Sub-Coordinates: ", str(dist), ' meters.')
    
    #st.write(f'here {selection} is: ', zf.sub_cel(selection))
    
    
    sslat = sub_cel[0]  
    sslon = sub_cel[1]
    melat = obloc[0]
    melon = obloc[1]     
    # map
    map = folium.Map(location=[0, sslon], zoom_start=1)
    # add tiles to map
    attribution = "Map tiles by Google"
    folium.raster_layers.TileLayer('Open Street Map', attr=attribution).add_to(map)
    folium.raster_layers.TileLayer('Stamen Terrain', attr=attribution).add_to(map)
    # Add custom base maps to folium
    folium.raster_layers.TileLayer(
            tiles = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr = 'Google',
            name = 'Google Maps',
            overlay = False,
            control = True
        ).add_to(map)
    folium.raster_layers.TileLayer(
            tiles = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr = 'Google',
            name = 'Google Satellite',
            overlay = False,
            control = True
        ).add_to(map)
    folium.raster_layers.TileLayer(
            tiles = 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
            attr = 'Google',
            name = 'Google Terrain',
            overlay = False,
            control = True
        ).add_to(map)

    # add layer control to show different maps
    folium.LayerControl().add_to(map)
    
    # plugin for mini map
    minimap = plugins.MiniMap(toggle_display=True)

    # add minimap to map
    map.add_child(minimap)
    
    # add scroll zoom toggler to map
    plugins.ScrollZoomToggler().add_to(map)

    # add full screen button to map
    plugins.Fullscreen(position='topright').add_to(map)
    
    # add marker to map https://fontawesome.com/v5.15/icons?d=gallery&p=2&m=free
    sun = folium.features.CustomIcon('Icons/target.png',icon_size=(30,30))
    folium.Marker(location=[sslat, sslon], color='green', tooltip='SubSolar Point',icon=sun).add_to(map)
    pal = folium.features.CustomIcon('Icons/paladin.jpg',icon_size=(30,20))
    folium.Marker(location=[melat, melon], color='green', tooltip='my location',icon=pal).add_to(map)

    points = []
    points.append([melat,melon])
    td = h_az
    for p in range(0,1000):
        get = zf.vPolar(points[p][0],points[p][1],td,dist/1000)
        if h_az < 180 and points[p][1] > sslon: points[p][1] = points[p][1] - 360
        if h_az > 180 and points[p][1] < sslon: points[p][1] = points[p][1] + 360
        points.append([get[0],get[1]])
        td = zf.LLDist(get[0],get[1],sslat,sslon)[1]
    del points[-1]
    points.append([sslat,sslon])
    # st.write(points)
    folium.PolyLine(points, color='red').add_to(map)

    draw = plugins.Draw()
    draw.add_to(map)
    # display map
    folium_static(map)



        
        

    