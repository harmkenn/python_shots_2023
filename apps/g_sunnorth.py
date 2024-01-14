# https://www.omnicalculator.com/physics/sun-angle
import streamlit as st

from datetime import datetime, timezone, timedelta
import folium
from streamlit_folium import folium_static
from folium import plugins
from apps import z_functions as zf
def app():
    # title of the app
    st.markdown('Get your position from the location of the sun')
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
        setyear = st.number_input('Year: ',1900,2100,2022)
        setmonth = st.number_input('Month: ',1,12,4)
        setday = st.number_input('Day: ',1,31,9)
        sethour = st.number_input('Hour: ',0,23,22)
        setmin = st.number_input('Minute: ',0,59,40)
        setsec = st.number_input('Second: ',0,59,0)
        
        setday = datetime(setyear,setmonth,setday,sethour,setmin,setsec)

        

    with c2:
        if st.button('Now'):
            setday = datetime.now(timezone.utc)
        st.write(str(setday)+'UTC')
        
        
        ssloc = zf.subsolar([setday.year,setday.month,setday.day,setday.hour,setday.minute,setday.second])
        sslat = ssloc[0]
        sslon = ssloc[1]
        st.write('Sub Solar Point: '+str(ssloc)+' MGRS: '+zf.LL2MGRS(sslat,sslon)[1])
        lpmgrs = st.text_input('Your Location (MGRS):','32TPR9792346676')
        yl = zf.MGRS2LL(lpmgrs)
        st.write('Your Location (LL): '+str(round(yl[1],5))+', '+str(round(yl[2],5)))
        melat = zf.MGRS2LL(lpmgrs)[1]
        melon = zf.MGRS2LL(lpmgrs)[2]
        
        when = (setday.year,setday.month,setday.day,setday.hour,setday.minute,setday.second,0)
        location = (melat,melon)
        
        dist = zf.LLDist(melat,melon,sslat,sslon)[0]
        az2sun = zf.LLDist(melat,melon,sslat,sslon)[1]

        st.write('azimuth to the sun: '+ str(az2sun))
        st.write('elevation to the sun: '+ str(zf.sunpos(when, location, True)[1]))
       
        if az2sun < 180 and sslon < yl[2]: sslon = sslon + 360
        if az2sun > 180 and sslon > yl[2]: sslon = sslon - 360
        
        # map
        map = folium.Map(location=[sslat, (sslon+yl[2])/2], zoom_start=1)
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
        points.append([yl[1],yl[2]])
        td = az2sun

        
        for p in range(0,1000):
            get = zf.vPolar(points[p][0],points[p][1],td,dist/1000)
            if az2sun < 180 and points[p][1] > sslon: points[p][1] = points[p][1] - 360
            if az2sun > 180 and points[p][1] < sslon: points[p][1] = points[p][1] + 360
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

        
        

    