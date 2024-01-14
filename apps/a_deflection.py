import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium import plugins

from apps import z_functions as zf

def app():
    # title of the app
    st.markdown('Deflection')
    c1,c2 = st.columns((1,2))
    with c1:
        if 'a_lat' not in st.session_state: st.session_state['a_lat'] = -30
        lat = st.session_state['a_lat']
        lat = float(st.text_input('Latitude', lat))
        st.session_state['a_lat'] = lat
        if 'a_lon' not in st.session_state: st.session_state['a_lon'] = 30
        lon = st.session_state['a_lon']
        lon = float(st.text_input('Longitude', lon))
        #st.session_state['a_lon'] = lon
        back = zf.LL2MGRS(lat,lon)
        ip = zf.LL2MGRS(lat+.1,lon+.1)
        st.write('UTM: ',back[0])
        st.write('MGRS: ',back[1])

               
        lu = st.sidebar.text_input('Lookup: ') 
        if len(lu)>=3:
            where = zf.lookup(lu)
            st.sidebar.write(where[0])
            st.sidebar.write('Lat: '+str(where[1])+' Lon: '+str(where[2]))
            st.sidebar.write('MGRS: '+where[3])
            alt = zf.elevation(where[1],where[2])
            st.sidebar.write('Alt :'+str(round(alt,2))+' Meters')
            
    with c1:
        if 'a_aof' not in st.session_state: st.session_state['a_aof'] = 2000
        aof = st.session_state['a_aof']
        aof = float(st.text_input('Azimuth of Fire (mils): ',aof))
        st.session_state['a_aof'] = aof
        
        if 'a_lpmgrs' not in st.session_state: st.session_state['a_lpmgrs'] = back[1]
        lpmgrs = st.session_state['a_lpmgrs']
        lpmgrs = st.text_input('Launch Point (MGRS):',lpmgrs)
        st.session_state['a_lpmgrs'] = lpmgrs
        
        if 'a_ipmgrs' not in st.session_state: st.session_state['a_ipmgrs'] = ip[1]
        ipmgrs = st.session_state['a_ipmgrs']
        ipmgrs = st.text_input('Impact Point (MGRS):',ipmgrs)
        st.session_state['a_ipmgrs'] = ipmgrs
        
        lp = zf.MGRS2LL(lpmgrs)
        
        ip = zf.MGRS2LL(ipmgrs)
        st.write('UTM :',ip[0])
        st.write('Impact Point (LL): '+str(round(ip[1],5))+', '+str(round(ip[2],5)))
    with c2:
        # map
        map = folium.Map(location=[lp[1], lp[2]], zoom_start=10)
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
        pal = folium.features.CustomIcon('Icons/paladin.jpg',icon_size=(30,20))
        tgt = folium.features.CustomIcon('Icons/target.png',icon_size=(25,25))
        folium.Marker(location=[lp[1],lp[2]], color='green',popup=lpmgrs, tooltip='Launch Point',icon=pal).add_to(map)
        folium.Marker(location=[ip[1],ip[2]], color='green',popup=ipmgrs, tooltip='Impact Point',icon=tgt).add_to(map)
        pback = zf.vPolar(lp[1],lp[2],int(aof)*180/3200,30000)
        
        # AOF line
        folium.PolyLine([[lp[1],lp[2]],[pback[0],pback[1]]],tooltip='Azimuth of Fire',popup=aof).add_to(map)
        # Gun Target line
        folium.PolyLine([[lp[1],lp[2]],[ip[1],ip[2]]],color='red',tooltip='Gun Target Line',popup='gtl').add_to(map)
        # radius of the circle in meters
        folium.Circle(radius=30000, location=[lp[1],lp[2]], color='green').add_to(map)
        
        
        draw = plugins.Draw()
        draw.add_to(map)
        # display map
        folium_static(map) 
        
        with c2:
            deets = zf.LLDist(lp[1],lp[2],ip[1],ip[2])
            st.write('Distance: ' + str(int(deets[0])) + ' meters')
            st.write('Bearing: '+str(round(deets[1],2)) + ' degrees')
            st.write('Azimuth: '+str(round(deets[1]*3200/180,2)) + ' mils')
            diff =  round(aof-deets[1]*3200/180+3200,0)
            if diff<0: diff = diff + 6400
            st.write('Deflection: '+str(diff)+' mils')
            
    
        
        
        
        
        
        
        
        
        