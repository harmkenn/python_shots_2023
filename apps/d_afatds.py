
SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium import plugins
from numpy import log, pi, sin, arctan, cos, array, tan
from scipy.optimize import curve_fit
import plotly.express as px
from apps import z_functions as zf

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

def app():
    # title of the app
       
    st.markdown('AFATDS')
    c1,c2,c3 = st.columns((1,3,1.5))
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
        if 'd_lpmgrs' not in st.session_state: st.session_state['d_lpmgrs'] = '29NQH5872754513'
        d_lpmgrs = st.session_state['d_lpmgrs']
        d_lpmgrs = st.text_input('Launch Point (MGRS):',d_lpmgrs, key = 'd1')
        st.session_state['d_lpmgrs'] = d_lpmgrs
        
        lp = zf.MGRS2LL(d_lpmgrs)
        st.write('Launch Point (LL):') 
        st.write(str(round(lp[1],5))+', '+str(round(lp[2],5)))

        if 'd_lpalt' not in st.session_state: st.session_state['d_lpalt'] = 123
        d_lpalt = st.session_state['d_lpalt']
        d_lpalt = st.text_input('Launch Altitude (M):',d_lpalt, key = 'd3')
        st.session_state['d_lpalt'] = d_lpalt

        if 'd_ipmgrs' not in st.session_state: st.session_state['d_ipmgrs'] = '29NQH4843150392'
        d_ipmgrs = st.session_state['d_ipmgrs']
        d_ipmgrs = st.text_input('Impact Point (MGRS):',d_ipmgrs, key = 'd2')
        st.session_state['d_ipmgrs'] = d_ipmgrs

        ip = zf.MGRS2LL(d_ipmgrs)
        st.write('Impact Point (LL):')
        st.write(str(round(ip[1],5))+', '+str(round(ip[2],5)))

        if 'd_ipalt' not in st.session_state: st.session_state['d_ipalt'] = 321
        d_ipalt = st.session_state['d_ipalt']
        d_ipalt = st.text_input('Impact Altitude (M):',d_ipalt, key = 'd4')
        st.session_state['d_ipalt'] = d_ipalt

        if 'd_AOF' not in st.session_state: st.session_state['d_AOF'] = 0
        d_AOF = st.session_state['d_AOF']
        d_AOF = st.text_input('Azimuth of Fire (mils):',d_AOF, key = 'd5')
        st.session_state['d_AOF'] = d_AOF 
        
    if len(d_lpmgrs)>3 and len(d_ipmgrs)>3:
        
        with c1:
            deets = zf.LLDist(lp[1],lp[2],ip[1],ip[2])
            st.write('Distance: ' + str(round(deets[0],0)) + ' meters')
            st.write('Launch Bearing: '+str(round(deets[1],2)) + ' degrees')
            st.write('Launch Azimuth: '+str(round(deets[1]*3200/180,2)) + ' mils')
            st.write('Impact Bearing: '+str(round(deets[3],2)) + ' degrees')
            st.write('Impact Azimuth: '+str(round(deets[3]*3200/180,2)) + ' mils')
        with c2:
            # map
            map = folium.Map(location=[(lp[1]+ip[1])/2, (lp[2]+ip[2])/2], zoom_start=-1.36*log(deets[0]/1000)+15)
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
            folium.Marker(location=[lp[1],lp[2]], color='green',popup=d_lpmgrs, tooltip='Launch Point',icon=pal).add_to(map)
            folium.Marker(location=[ip[1],ip[2]], color='green',popup=d_ipmgrs, tooltip='Impact Point',icon=tgt).add_to(map)
            

            
        with c2:
            points = []
            points.append([lp[1],lp[2]])
            for p in range(1,101):
                get = zf.vPolar(lp[1],lp[2],deets[1],deets[0]*p/100)
                points.append([get[0],get[1]])
            points.append([ip[1],ip[2]])
            folium.PolyLine(points, color='red').add_to(map)
            
            
        
            
            draw = plugins.Draw()
            draw.add_to(map)
            # display map
            folium_static(map) 
        with c3:
            rng = round(deets[0],0)
            chrg = st.selectbox('Charge:',['Auto','1L','2L','3H','4H','5H'])
            if chrg == 'Auto':
                chrg = pd.cut([rng], bins=[-1,2000,5000,8000,12000,15000,25000,99999999], labels=['Too Short','1L','2L','3H','4H','5H','Too Far'])
                chrg = chrg[0]

            ning = int(d_lpmgrs[-5:])
            if ning > 1000:
                ring = ning - 1000
                sp = d_lpmgrs[:-5]+str(ring).rjust(5, "0")
            else:
                ring = ning + 1000
                sp = d_lpmgrs[:-5]+str(ring).rjust(5, "0")
            spll = zf.MGRS2LL(sp)
            gd = zf.LLDist(spll[1],spll[2],lp[1],lp[2])

            gdm = gd[1]/180*3200
            if gdm > 4800:
                gdm = gdm - 6400
            if gdm > 1600:
                gdm = gdm - 3200

            macs = pd.read_csv('data/M795Macs.csv')

            #macs = macs[macs['Chg'].str.contains(chrg[-2:])]
            
            # Load data from CSV file
            
            macs = macs.loc[macs['Chg'] == chrg]

            # Extract the feature and target variables
            X = macs[['Range (M)']] # , 'cosAZ', 'Galt (M)','Talt (M)'
            y = macs[['Drift']] # , 'QE (mils)', 'TOF', 'MAX Ord (M)'
            
            # Creating polynomial features
            
            poly_features = PolynomialFeatures(degree=3)
            input_features_poly = poly_features.fit_transform(X)

            # Creating and training the polynomial regression model
            model = LinearRegression()
            model.fit(input_features_poly, y)
            
            new_data = pd.DataFrame({'Range (M)':[rng]}) #, 'cosAZ':[deets[0]*pi/180], 'Galt (M)':[d_lpalt],'Talt (M)':[d_ipalt]
            new_input_features_poly = poly_features.transform(new_data)
            output = model.predict(new_input_features_poly)
            drift = output[0,0]
            defl = 3200 + int(d_AOF) - deets[1] *3200/180 + drift + gdm
            if defl<0: defl = defl + 6400
            
            # Extract the feature and target variables
            X = macs[['Range (M)', 'sinAZ', 'Galt (M)','AOS (mils)']]
            y = macs[['QE (mils)', 'TOF']] # , 'MAX Ord (M)'
            
            # Creating polynomial features
            
            poly_features = PolynomialFeatures(degree=3)
            input_features_poly = poly_features.fit_transform(X)

            # Creating and training the polynomial regression model
            model = LinearRegression()
            model.fit(input_features_poly, y)
            
            new_data = pd.DataFrame({'Range (M)':[rng], 
                                     'sinAZ':[sin(deets[1]*pi/180)], 
                                     'Galt (M)':[d_lpalt], 
                                     'AOS (mils)':[arctan((int(d_ipalt)-int(d_lpalt))/rng)*3200/pi]})

            new_input_features_poly = poly_features.transform(new_data)
            output = model.predict(new_input_features_poly)
 
            qe = output[0,0]
            tof = output[0,1]
            
            # Extract the feature and target variables
            X = macs[['QE (mils)']]
            y = macs[['Moz']] 
            
            # Creating polynomial features
            
            poly_features = PolynomialFeatures(degree=3)
            input_features_poly = poly_features.fit_transform(X)

            # Creating and training the polynomial regression model
            model = LinearRegression()
            model.fit(input_features_poly, y)
            
            new_data = pd.DataFrame({'QE (mils)':[qe]})
            
            new_input_features_poly = poly_features.transform(new_data)
            output = model.predict(new_input_features_poly)
            mo = output[0,0] + int(d_lpalt) * .95
            
            
                        
            data = pd.DataFrame({'Range (Meters)':str(int(rng)),
                                 'Shell':'M795','Charge':chrg, 'Muzzle Velocity (m/s)':str(round(macs['MV (m/s)'].mean(),1)),'Azimuth to Target (mils)':str(round(deets[1]*3200/180 - gdm,0)),
                                 'Grid Declination (mils)':str(round(gdm,1)),'Drift (mils)':str(round(drift,1)),
                                 'Deflection (mils)':str(round(defl,1)), 'QE (mils)':str(round(qe,1)),
                                 'Time of Flight (sec)':str(round(tof,1)), 'Max Ord':str(int(mo))},
                                index = ['Fire Mission']).T 
                                
                                
                                 #'MaxOrd (Meters)':str(round(mo,0))
                                 
            st.dataframe(data,height=500) 
           
        with c2:
            # Define the cubic polynomial function
            def cubic_function(x, a, b, c, d):
                return a * x**3 + b * x**2 + c * x + d

            # Define the x and y coordinates of the four points
            x_data = array([0, 200, .6*rng, rng])
            y_data = array([int(d_lpalt), tan(qe*pi/3200)*200+int(d_lpalt), mo, int(d_ipalt)])

            # Use curve_fit to fit the cubic function to the data
            popt, pcov = curve_fit(cubic_function, x_data, y_data)

            # Retrieve the fitted coefficients
            a_fit, b_fit, c_fit, d_fit = popt
            
            # This is for mv deceleration
            
            def find_ratio(ss, a1, n1):
                ratio = 0.0

                # Iterate over a range of values for ratio
                for r in range(1, 1000):
                    r /= 1000.0  # Convert to decimal value

                    # Calculate the sum using the geometric series formula
                    Sn = a1 * (1 - r**n1) / (1 - r)

                    # Compare the calculated sum with the desired sum
                    if abs(Sn - ss) < ss*.05:
                        ratio = r
                        break

                return ratio

            # Example usage
            ss = rng
            a1 = macs['MV (m/s)'].mean() * cos(qe*pi/3200)
            n1 = int(tof)

            ratio = find_ratio(ss, a1, n1) 
            
            tPoints = pd.DataFrame(index=range(n1+3))
            tPoints['Ranges'] = a1 * (1 - ratio ** tPoints.index) / (1 - ratio)
            def traj(x):
                return a_fit * x ** 3 + b_fit * x ** 2 + c_fit * x + d_fit
            tPoints['Alts'] = tPoints['Ranges'].apply(traj)
            

            
            x, y = tPoints['Ranges'], tPoints['Alts']
            
            fig = px.scatter(tPoints, x=x, y=y)
            fig.update_layout(autosize=False,width=700,height=mo/rng*800*2.5)
            st.plotly_chart(fig)
            

            st.write(tPoints)
        
 
            
            
            
            


        
    