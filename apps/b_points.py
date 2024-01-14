import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium import plugins
from numpy import log

from apps import z_functions as zf

def app():
    # title of the app
    st.markdown('Point to Point')
    c1,c2 = st.columns((1,3))
    with c1:
        lu = st.sidebar.text_input('Lookup: ') 
        if len(lu)>=3:
            where = zf.lookup(lu)
            st.sidebar.write(where[0])
            st.sidebar.write('Lat: '+str(where[1])+' Lon: '+str(where[2]))
            st.sidebar.write('MGRS: '+where[3])
            alt = zf.elevation(where[1],where[2])
            st.sidebar.write('Alt :'+str(round(alt,2))+' Meters')
    with c1:
        if 'b_lpmgrs' not in st.session_state: st.session_state['b_lpmgrs'] = '12RWU1059022575'
        b_lpmgrs = st.session_state['b_lpmgrs']
        b_lpmgrs = st.text_input('Launch Point (MGRS):',b_lpmgrs, key = "b1")
        st.session_state['b_lpmgrs'] = b_lpmgrs
        lp = zf.MGRS2LL(b_lpmgrs)
        st.write('Launch Point (LL): '+str(round(lp[1],5))+', '+str(round(lp[2],5)))
        
        if 'b_ipmgrs' not in st.session_state: st.session_state['b_ipmgrs'] = '31UDQ5248411718'
        ipmgrs = st.session_state['b_ipmgrs']
        ipmgrs = st.text_input('Impact Point (MGRS):',ipmgrs,key = 'b2')
        st.session_state['b_ipmgrs'] = ipmgrs
        
        ip = zf.MGRS2LL(ipmgrs)
        st.write('Impact Point (LL): '+str(round(ip[1],5))+', '+str(round(ip[2],5)))
    
    if len(b_lpmgrs)>3 and len(ipmgrs)>3:
        
        
        with c1:
            deets = zf.LLDist(lp[1],lp[2],ip[1],ip[2])
            azdeg = deets[1]
            st.write('Distance: ' + str(round(deets[0],0)) + ' meters')
            totalD = deets[0]
            st.write('Launch Bearing: '+str(round(deets[1],2)) + ' degrees')
            st.write('Launch Azimuth: '+str(round(deets[1]*3200/180,2)) + ' mils')
            st.write('Impact Bearing: '+str(round(deets[3],2)) + ' degrees')
            st.write('Impact Azimuth: '+str(round(deets[3]*3200/180,2)) + ' mils')
        with c2:
            # map
            if ip[2]>lp[2] and azdeg > 180: ip[2] = ip[2] - 360
            if ip[2]<lp[2] and azdeg < 180: ip[2] = ip[2] + 360
            map = folium.Map(location=[(lp[1]+ip[1])/2, (lp[2]+ip[2])/2], zoom_start=-1.36*log(deets[0]/1000)+14)
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
            folium.Marker(location=[lp[1],lp[2]], color='green',popup=b_lpmgrs, tooltip='Launch Point',icon=pal).add_to(map)
            folium.Marker(location=[ip[1],ip[2]], color='green',popup=ipmgrs, tooltip='Impact Point',icon=tgt).add_to(map)
            
 
            
        with c2:
           # st.write(deets)
            points = []
            points.append([lp[1],lp[2]])
            td = deets[1]
            for p in range(0,1000):
                get = zf.vPolar(points[p][0],points[p][1],td,deets[0]/1000)
                if azdeg > 180 and points[p][1] > points [p-1][1]: points[p][1] = points[p][1] - 360
                points.append([get[0],get[1]])
                td = zf.LLDist(get[0],get[1],ip[1],ip[2])[1]
            del points[-1]
            points.append([ip[1],ip[2]])
           # st.write(points)
            folium.PolyLine(points, color='red').add_to(map)
            
            
        
            
            draw = plugins.Draw()
            draw.add_to(map)
            # display map
            folium_static(map) 
            
            


        
    