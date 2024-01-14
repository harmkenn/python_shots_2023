import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium import plugins
from numpy import pi,poly1d,polyfit,cos,sin
from sklearn.linear_model import ElasticNet
from scipy.optimize import curve_fit
import plotly.express as px
from apps import z_functions as zf

def app():
    # title of the app
       
    st.markdown('Artillery Physics')
    c1,c2 = st.columns((1,3))
    with c1:
        if 'galt' not in st.session_state: st.session_state['galt'] = 700
        galt = st.session_state['galt']
        galt = float(st.text_input('Gun Altitude (Meters):',galt, key = 'e1'))
        st.session_state['galt'] = galt 

        if 'imv' not in st.session_state: st.session_state['imv'] = 500
        imv = st.session_state['imv']
        imv = float(st.text_input('Initial Muzzle Velocity (m/s):',imv, key = 'e2'))
        st.session_state['imv'] = imv 

        if 'qe' not in st.session_state: st.session_state['qe'] = 250
        qe = st.session_state['qe']
        qe = float(st.text_input('Tube Elevation (mils):',qe, key = 'e3'))
        st.session_state['qe'] = qe 

        if 'sw' not in st.session_state: st.session_state['sw'] = 103.5
        sw = st.session_state['sw']
        sw = float(st.text_input('Shell Weight (lbs):',sw, key = 'e4'))
        st.session_state['sw'] = sw 

        m = sw/2.20462 #mass lbs to kg
        th0 = qe * pi / 3200 # initial angle in radians
        g = 9.80665 # gravitational force in m/s/s
        
        alt_press = pd.DataFrame({'alt':[0,200,500,1000,1500,2000,2500,3000,3500,4000,4500,5000,6000,7000,8000,9000],
                           'rho':[1.2250,1.2133,1.1844,1.1392,1.0846,1.0320,.9569,.8632,.7768,.6971,.5895,.4664,.3612,.2655,.1937,.1413]})
                            #Air Pressure at differnet altitudes
        press_M = poly1d(polyfit(alt_press['alt'], alt_press['rho'], 5)) #Pressure Model for any altitude

    with c2:
        pk = .000006 * 46.94681 #This is my predicted k value for the shape of the round.
        rho0 = press_M(galt) #initial Air Pressure
        k = rho0*pk/m # is the drag constant at 0 alt
        traj = pd.DataFrame({'Time(s)':.0,'Pressure':rho0,'k':k*1000000,'V(m/s)':imv,'angle(r)':th0,'angle(m)':qe,'Range(M)':0,'Alt(M)':galt}, index=[0]) #Just the initial Row
        
        dt = .1
        bt = .0
        bthr = th0
        br = 0
        balt = galt
        bp = rho0
        bk = k
        bv = imv
        while balt >galt-.1:
            bt = bt + .1 #next time
            br = br + bv*dt*cos(bthr) # next range
            balt = balt + bv*dt*sin(bthr) # next alt
            bthr = bthr - (g*cos(bthr)/bv)*dt # next angle in radians
            bthm = bthr*3200/pi
            bp = press_M(balt) #next pressure
            bk = bp*pk/m # is the drag constant at y alt
            bv = bv - (sin(bthr) + bk*bv**2) * g *dt # next velocity 
            traj.loc[len(traj)] = [bt,bp,bk*1000000,bv,bthr,bthm,br,balt]  
        st.dataframe(traj)
        fig = px.scatter(x=traj['Range(M)'], y=traj['Alt(M)'])
        MO = max(traj['Alt(M)'])
        rng = max(traj['Range(M)'])
        fig.update_layout(autosize=False,width=800,height=MO/rng*800*2)
        st.plotly_chart(fig)
    with c1:    
        data = pd.DataFrame({'Range (Meters)':str(int(br)),'Time of Flight (s)':str(round(bt,1)),
                             'Angle of Fall':str(int(bthm)),'Final Velocity (m/s)':str(int(bv)),
                             'Max Ord (Meters)':str(int(MO))},index = ['Results']).T 
        st.dataframe(data,height=500) 
