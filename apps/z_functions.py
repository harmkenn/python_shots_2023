import streamlit as st
#import numpy as np
from numpy import sqrt,pi,cos,sin,tan,arctan,arctan2,floor,exp,arcsin
import pandas as pd
import requests
import urllib.request
import json
import pygeodesy as pg
import pyproj

nd = pd.read_csv('data/northdes.csv')

def getIndexes(dfObj, value):
    ''' Get index positions of value in dataframe i.e. dfObj.'''
    listOfPos = list()
    # Get bool dataframe with True at positions where the given value exists
    result = dfObj.isin([value])
    # Get list of columns that contains the value
    seriesObj = result.any()
    columnNames = list(seriesObj[seriesObj == True].index)
    # Iterate over list of columns and fetch the rows indexes where value exists
    for col in columnNames:
        rows = list(result[col][result[col] == True].index)
        for row in rows:
            listOfPos.append((row, col))
    # Return a list of tuples indicating the positions of value in the dataframe
    return listOfPos

# Lat Lon to MGRS
def LL2MGRS(lat,lon):
    # Pick a hemisphere
    hem = 'N'
    if lat<0: hem = 'S'
    # convert to radians
    
    latr = lat*pi/180
    lonr = lon*pi/180
    
    # Lets go find Easting
    sec1 = pi/(180*3600) #One Second
    a = 6378137 # Equitorial Radius
    b = 6356752.31424518 #Polar Radius
    k0 = .9996 #Scalar Factor Constant
    gzen = floor(1/6*lon)+31 #Longitude Zone
    Czone = 6*gzen - 183 #Longitude of the center of the zone
    dlon = lon - Czone # Longitude from the center of the zone
    p = dlon*3600/10000 #Hecta seconds?
    e = sqrt(1-(b/a)**2) #eccentricity
    e1 = sqrt(a**2-b**2)/b
    e1sq = e1**2
    c = a**2/b
    nu = a/sqrt(1-(e*sin(latr))**2) #r curv 2
    Kiv = nu*cos(latr)*sec1*k0*10000 #Coef for UTM 4
    Kv = (sec1*cos(latr))**3*(nu/6)*(1-tan(latr)**2+e1sq*cos(latr)**2)*k0*10**12 #Coef for UTM 5
    Easting = 500000+Kiv*p+Kv*p**3
    
    # Now let's go find Northing
    n = (a-b)/(a+b)
    A0 = a*(1-n+(5*n**2/4)*(1-n)+(81*n**4/64)*(1-n)) # Meridional Arc Length
    B0 = (3*a*n/2)*(1-n-(7*n**2/8)*(1-n)+55*n**4/64) # Meridional Arc Length
    C0 = (15*a*n**2/16)*(1-n+(3*n**2/4)*(1-n)) # Meridional Arc Length
    D0 = (35*a*n**3/48)*(1-n+11*n**2/16) # Meridional Arc Length
    E0 = (315*a*n**4/51)*(1-n) # Meridional Arc Length
    S = A0*latr - B0*sin(2*latr) + C0*sin(4*latr) - D0*sin(6*latr) + E0*sin(8*latr) # Meridional Arc
    Ki = S*k0 #Coef for UTM 1
    Kii = nu*sin(latr)*cos(latr)*sec1**2*k0*100000000/2 #Coef for UTM 2
    Kiii = ((sec1**4*nu*sin(latr)*cos(latr)**3)/24)*(5-tan(latr)**2+9*e1sq*cos(latr)**2*cos(latr)**4)*k0*10**16 #Coef for UTM 2
    Northing = Ki + Kii * p**2 + Kiii * p**4
    if lat < 0: Northing = 10000000 + Northing # In the Southern Hemisphere is Northing is measured from the south pole instead of from the equator
  
    Easting = int(floor(Easting)) # 6 digit easting
    Northing = int(floor(Northing)) # 7 or 8 digit northing
    
    ## Now let's turn UTM into MGRS
    gzoe = 'Odd' 
    if gzen % 2 == 0: gzoe = 'Even' # longitude grid zone
    
    gsen = int(floor(Easting/100000)) #Grab off the first digit off the Easting
    gsnn = int(floor(Northing/100000)) #Grab off the first two digits off the Northing
    if gzoe =='Even': gsnn = gsnn + 5
    #ck gridsquare letters
    ckgsn = ['A','B','C','D','E','F','G','H','J','K','L','M','N','P','Q','R','S','T','U','V'] # northing grid square letter
    gsn = gsnn%20 # Latitude letter zone count
    
    gsnl = ckgsn[gsn] # northing grid zone letter
    
    if gzoe =='Even': gsnn = gsnn - 5
    
    eldf = pd.DataFrame({1:['A','J','S'],2:['B','K','T'],3:['C','L','U'],4:['D','M','V'],5:['E','N','W'],6:['F','P','X'],7:['G','Q','Y'],8:['H','R','Z']},index=[1,2,0])
    gsel = eldf.loc[gzen%3,gsen]
    
    this = pd.DataFrame({'hem':hem,'gzoe':gzoe,'gsnl':gsnl,'gsnn':gsnn},index=[0])
    
    this = this.merge(nd, how='left', on=['hem','gzoe','gsnl','gsnn'])
    
    gznl = this.loc[0,'gznl']
    
    return [str(int(gzen))+str(gznl)+' '+str(Easting).rjust(6, "0")+' '+str(Northing).rjust(8, "0"),
            str(int(gzen))+str(gznl)+str(gsel)+str(gsnl)+str(Easting-gsen*100000).rjust(5, "0")+str(Northing-gsnn*100000).rjust(5, "0")]

# MGRS to Lat Lon
def MGRS2LL(mgrs):
    out = ''.join([i for i in mgrs if not i.isdigit()])
    ppp = mgrs.split(out)
    l = [out[index : index + 1] for index in range(0, 3, 1)]
    ten = [ppp[1][index : index + 5] for index in range(0, 10, 5)]
    gzen = int(ppp[0])
    gznl = l[0]
    gsel = l[1]
    gsnl = l[2]
    east5 = int(ten[0])
    north5 = int(ten[1])
    # grid square easting letters data frame
    gseldf = pd.DataFrame({1:['A','J','S'],2:['B','K','T'],3:['C','L','U'],4:['D','M','V'],5:['E','N','W'],6:['F','P','X'],7:['G','Q','Y'],8:['H','R','Z']},index=[1,2,0])
    
    sec1 = pi/(180*3600) #One Second
    a = 6378137 # Equitorial Radius
    b = 6356752.31424518 #Polar Radius
    k0 = .9996 #Scalar Factor Constant
    e1 = sqrt(a**2-b**2)/b
    e1sq = e1**2
    c = a**2/b
    
    hem = 'S'
    if gznl in 'NPQRSTUVWX': hem = 'N'
    
    eI = getIndexes(gseldf,gsel)[0][1]
    Easting = eI*100000 + east5
    
    gzoe = 'Odd' 
    if gzen % 2 == 0: gzoe = 'Even'
    this = pd.DataFrame({'hem':hem,'gzoe':gzoe,'gsnl':gsnl,'gznl':gznl},index=[0])
    this = this.merge(nd, how='left', on=['hem','gzoe','gsnl','gznl'])
    gsnn = this.loc[0,'gsnn']
    Northing = gsnn*100000 + north5
    NfEQ = Northing
    if hem == 'S': NfEQ = Northing - 10000000
    Fi = (NfEQ)/(6366197.724*k0)
    Ni = (c/(1+e1sq*(cos(Fi))**2)**(1/2))*k0
    Czone = 6*gzen-183
    dln = (Easting-500000)/Ni
    A1 = sin(2*Fi)
    A2 = A1*(cos(Fi))**2
    J2 = Fi+(A1/2)
    J4 = (3*J2+A2)/4
    J6 = (5*J4+A2*(cos(Fi))**2)/3
    alfa = 3/4*e1sq
    beta = 5/3*alfa**2
    gamma = 35/27*alfa**3
    Bfi = k0*c*(Fi-(alfa*J2)+(beta*J4)-(gamma*J6))
    BB = (NfEQ-Bfi)/Ni
    zeta = ((e1sq*dln**2)/2)*(cos(Fi))**2
    Xi = dln*(1-(zeta/3))
    Eta = BB*(1-zeta)+Fi
    ShXi = (exp(Xi)-exp(-Xi))/2
    dLam = arctan(ShXi/cos(Eta))
    Tau = arctan(cos(dLam)*tan(Eta))
    FiR = Fi+(1+e1sq*(cos(Fi))**2-(3/2)*e1sq*sin(Fi)*cos(Fi)*(Tau-Fi))*(Tau-Fi)
    lat = FiR/pi*180
    lon = dLam/pi*180+Czone
    
    return [str(gzen)+str(gznl)+' '+str(Easting).rjust(6, "0")+' '+str(Northing).rjust(8, "0"),lat,lon]
    
def lookup(what):
    response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address='+ what +'&key=AIzaSyAfnLNZjvYdMx-cyga_qA1oJ6P36dRGalA')
    resp_json_payload = response.json()
    address = resp_json_payload['results'][0]['formatted_address']
    lat = resp_json_payload['results'][0]['geometry']['location']['lat']
    lon = resp_json_payload['results'][0]['geometry']['location']['lng']
    mgrs = LL2MGRS(lat,lon)
    return [address,lat,lon,mgrs[1]]

def elevation(lat, lng):
    with urllib.request.urlopen('https://maps.googleapis.com/maps/api/elevation/json?'+"locations=%s,%s&sensor=%s" % (lat, lng, "false")+'&key=AIzaSyAfnLNZjvYdMx-cyga_qA1oJ6P36dRGalA') as f:
        response = json.loads(f.read().decode())    
        return response['results'][0]['elevation']



def sunpos(when, location, refraction):
# Extract the passed data
    year, month, day, hour, minute, second, timezone = when
    latitude, longitude = location
# Math typing shortcuts

# Convert latitude and longitude to radians
    rlat = latitude*pi/180
    rlon = longitude*pi/180
# Decimal hour of the day at Greenwich
    greenwichtime = hour - timezone + minute / 60 + second / 3600
# Days from J2000, accurate from 1901 to 2099
    daynum = (
        367 * year
        - 7 * (year + (month + 9) // 12) // 4
        + 275 * month // 9
        + day
        - 730531.5
        + greenwichtime / 24
    )
# Mean longitude of the sun
    mean_long = daynum * 0.01720279239 + 4.894967873
# Mean anomaly of the Sun
    mean_anom = daynum * 0.01720197034 + 6.240040768
# Ecliptic longitude of the sun
    eclip_long = (
        mean_long
        + 0.03342305518 * sin(mean_anom)
        + 0.0003490658504 * sin(2 * mean_anom)
    )
# Obliquity of the ecliptic
    obliquity = 0.4090877234 - 0.000000006981317008 * daynum
# Right ascension of the sun
    rasc = arctan2(cos(obliquity) * sin(eclip_long), cos(eclip_long))
# Declination of the sun
    decl = arcsin(sin(obliquity) * sin(eclip_long))
# Local sidereal time
    sidereal = 4.894961213 + 6.300388099 * daynum + rlon
# Hour angle of the sun
    hour_ang = sidereal - rasc
# Local elevation of the sun
    elevation = arcsin(sin(decl) * sin(rlat) + cos(decl) * cos(rlat) * cos(hour_ang))
# Local azimuth of the sun
    azimuth = arctan2(
        -cos(decl) * cos(rlat) * sin(hour_ang),
        sin(decl) - sin(rlat) * sin(elevation)
    )
# Convert azimuth and elevation to degrees
    azimuth = into_range(azimuth*180/pi, 0, 360)
    elevation = into_range(elevation*180/pi, -180, 180)
# Refraction correction (optional)
    if refraction:
        targ = (elevation + (10.3 / (elevation + 5.11)))*pi/180
        elevation += (1.02 / tan(targ)) / 60
# Return azimuth and elevation in degrees
    return (round(azimuth, 2), round(elevation, 2))
def into_range(x, range_min, range_max):
    shiftedx = x - range_min
    delta = range_max - range_min
    return (((shiftedx % delta) + delta) % delta) + range_min

def subsolar(utc):
    ye, mo, da, ho, mi, se = utc 
    ta = pi * 2
    ut = ho + mi / 60 + se / 3600
    t = 367 * ye - 7 * (ye + (mo + 9) // 12) // 4
    dn = t + 275 * mo // 9 + da - 730531.5 + ut / 24
    sl = dn * 0.01720279239 + 4.894967873
    sa = dn * 0.01720197034 + 6.240040768
    t = sl + 0.03342305518 * sin(sa)
    ec = t + 0.0003490658504 * sin(2 * sa)
    ob = 0.4090877234 - 0.000000006981317008 * dn
    st = 4.894961213 + 6.300388099 * dn
    ra = arctan2(cos(ob) * sin(ec), cos(ec))
    de = arcsin(sin(ob) * sin(ec))
    la = de*180/pi
    lo = (ra - st)*180/pi % 360
    lo = lo - 360 if lo > 180 else lo
    return [round(la, 6), round(lo, 6)]


import ephem

def sub_cel(cel_ob):
    observer = ephem.Observer()
    observer.lat = '0'  # Example latitude (London, United Kingdom)
    observer.lon = '0'
    if cel_ob == 'the Sun': 
        cel = ephem.Sun()
    elif cel_ob == 'the Moon': 
        cel = ephem.Moon()
    elif cel_ob == 'Polaris': 
        cel = ephem.star('Polaris') # https://theskylive.com/sky/stars/polaris-alpha-ursae-minoris-star
    elif cel_ob == 'Mercury': 
        cel = ephem.Mercury() # https://theskylive.com/where-is-mercury
    elif cel_ob == 'Venus': 
        cel = ephem.Venus()
    elif cel_ob == 'Mars': 
        cel = ephem.Mars()
    elif cel_ob == 'Jupiter': 
        cel = ephem.Jupiter()
    elif cel_ob == 'Saturn': 
        cel = ephem.Saturn()
    elif cel_ob == 'Uranus': 
        cel = ephem.Uranus()
    elif cel_ob == 'Neptune': 
        cel = ephem.Neptune()
    else: out = 'Something else'
    
    cel.compute(observer)
    cel_azimuth = float(cel.az)*180/pi
    cel_altitude = float(cel.alt)*180/pi
    
    sub_cel_dist = 40050*(90-cel_altitude)*1000/360
    
    sub_cel = vPolar(0,0,cel_azimuth,sub_cel_dist)
    st.write([0,0,cel_azimuth,sub_cel_dist])

    return [cel_ob,sub_cel[1],sub_cel[0]]

def LLDist(lat1d,lon1d,lat2d,lon2d):
    # https://en.wikipedia.org/wiki/Vincenty%27s_formulae
    a=6378137.0
    f = 1/298.257223563
    b = (1-f)*a
    lat1r=lat1d*pi/180
    lon1r=lon1d*pi/180
    lat2r=lat2d*pi/180
    lon2r=lon2d*pi/180
    U1 = arctan((1-f)*tan(lat1r))
    U2 = arctan((1-f)*tan(lat2r))
    L = lon2r-lon1r
    lam = L

    for i in range(7):
        sinσ = sqrt((cos(U2)*sin(lam))**2+(cos(U1)*sin(U2)-sin(U1)*cos(U2)*cos(lam))**2)
        cosσ = sin(U1)*sin(U2)+cos(U1)*cos(U2)*cos(lam)
        σ = arctan2(sinσ,cosσ)
        sinα = cos(U1)*cos(U2)*sin(lam) / sinσ
        cos2α = 1 - sinα**2
        if cos2α == 0: cos2α = .000000000001
        cos2σm = cosσ - 2*sin(U1)*sin(U2) / cos2α
        C = f/16*cos2α*(4+f*(4-3*cos2α))
        lam = L+(1-C)*f*sinα*(σ+C*sinσ*(cos2σm+C*cosσ*(-1+2*cos2σm**2)))

    u2 = cos2α*(a**2/b**2-1)
    A = 1+u2/16384*(4096+u2*(-768+u2*(320-175*u2)))
    B = u2/1024*(256+u2*(-128+u2*(74-47*u2)))
    Δσ = B*sinσ*(cos2σm+B/4*(cosσ*(-1+2*cos2σm**2)-B/6*cos2σm*(-3+4*sinσ**2)*(-3+4*cos2σm**2)))
    dist = b*A*(σ-Δσ)

    faz = arctan2(sin(lon2r-lon1r)*cos(lat2r),cos(lat1r)*sin(lat2r)-sin(lat1r)*cos(lat2r)*cos(lon2r-lon1r))
    fazd = (faz*180/pi+360)%360
    baz = arctan2(sin(lon1r-lon2r)*cos(lat1r),cos(lat2r)*sin(lat1r)-sin(lat2r)*cos(lat1r)*cos(lon1r-lon2r))
    bazd = (baz*180/pi+360)%360
    iazd = (bazd+180)%360

    return [dist,fazd,bazd,iazd]

def vPolar(lat1d,lon1d,dird,dists):
    # https://en.wikipedia.org/wiki/Vincenty%27s_formulae
    a=6378137.0
    f = 1/298.257223563
    b = (1-f)*a
 
    lat1r=lat1d*pi/180
    lon1r=lon1d*pi/180
    dirr = dird*pi/180
    U1 = arctan((1-f)*tan(lat1r))
    sig1 = arctan2(tan(U1),cos(dirr))
    sinα = cos(U1)*sin(dirr)
    u2 = (1-sinα**2)*(a**2/b**2-1)
    k1 = (sqrt(1+u2)-1)/(sqrt(1+u2)+1)
    A = (1+.25*k1**2)/(1-k1)
    B = k1*(1-3/8*k1**2)
    sig = dists/b/A

    for i in range(4):
        tsm = 2*sig1+sig
        dsig = B*sin(sig)*(cos(tsm)+B/4*(cos(sig)*(-1+2*cos(tsm))-B/6*cos(tsm)*(-3+4*sin(sig)**2)*(-3+4*cos(tsm)**2)))
        sig = dists/b/A+dsig

    lat2r = arctan2(sin(U1)*cos(sig)+cos(U1)*sin(sig)*cos(dirr),(1-f)*sqrt(sinα**2+(sin(U1)*sin(sig)-cos(U1)*cos(sig)*cos(dirr))**2))
    lam = arctan2(sin(sig)*sin(dirr),cos(U1)*cos(sig)-sin(U1)*sin(sig)*cos(dirr))
    C = f/16*(1-sinα**2)*(4+f*(4-3*(1-sinα**2)))
    L = lam-(1-C)*f*sinα*(sig+C*sin(sig)*(cos(tsm)+C*cos(sig)*(-1+2*cos(tsm)**2)))
    lon2r = L+lon1r
    lat2d = lat2r*180/pi
    lon2d = lon2r*180/pi
    if lon2d < -180: lon2d = lon2d+360
    more = LLDist(lat1d,lon1d,lat2d,lon2d)
    iazd = more[3]
    return [lat2d,lon2d,dird,iazd]

def revVpolar(lat2d,lon2d,lazd,distm):
    bazd = (lazd + 180)%360
    taz = bazd
    for i in range(20):
        temp = vPolar(lat2d , lon2d,taz,distm)
        taz = taz - (temp[3]-bazd)
    lat1d = temp[0]
    lon1d = temp[1]
    liazr = (taz +180)%360
    return [lat1d,lon1d, lazd, liazr]