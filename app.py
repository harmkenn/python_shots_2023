import streamlit as st
from multiapp import MultiApp
from apps import z_functions as zf
from apps import a_deflection,b_points,c_polar,d_afatds,e_physics,f_sungrid,g_sunnorth,h_celgrid,i_grid_cel  # import your app modules here
st.set_page_config(layout="wide",)
app = MultiApp()

CURRENT_THEME = "dark"
IS_DARK_THEME = True


# Add all your application here
app.add_app("Deflection", a_deflection.app)
app.add_app("Point to Point", b_points.app)
app.add_app("Polar", c_polar.app)
app.add_app("AFATDS", d_afatds.app)
app.add_app("Artillery Physics", e_physics.app)
app.add_app("Sun to Grid", f_sungrid.app)
app.add_app("Grid to Sun", g_sunnorth.app)
app.add_app("Celestial to Grid", h_celgrid.app)
app.add_app("Grid to Celestial", i_grid_cel.app)

# The main app
app.run()

