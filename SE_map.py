import streamlit as st
import pandas as pd
from streamlit_authenticator import Authenticate
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_folium import folium_static
import folium

# Google Sheets setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)
sheet = client.open("Social Enterprises Ireland").sheet1

def load_data():
    return pd.DataFrame(sheet.get_all_records())

# Initialize authenticator
authenticator = Authenticate(
    secret_key="secret",
    cookie_expiry_days=30,
    sign_up=True,
    hash_passwords=True)

def init_user_data():
    if 'auth_status' not in st.session_state:
        st.session_state['auth_status'] = None

init_user_data()

# Create the layout
st.sidebar.title("Navigation")
menu = ["The Map", "Sign-in", "About"]
choice = st.sidebar.radio("Choose a page:", menu)

# User authentication
if choice == "Sign-in":
    email, authentication_status, username = authenticator.login('Login', 'main', preauthorization_page="signup")
    if authentication_status:
        st.session_state['auth_status'] = 'logged_in'
        st.sidebar.success(f"Logged in as {email}")
        st.sidebar.button('Sign out', on_click=authenticator.logout, args=('main', 'signin'))
    elif authentication_status == False:
        st.sidebar.error('Email/password is incorrect')
    elif authentication_status == None:
        st.sidebar.warning('Please enter your email and password')

# Display the map
if choice == "The Map":
    data = load_data()
    m = folium.Map(location=[53.4129, -8.2439], zoom_start=7)
    for _, row in data.iterrows():
        folium.Marker([row['Latitude'], row['Longitude']], tooltip=row['Name']).add_to(m)
    folium_static(m)

# About page
if choice == "About":
    st.write("This application displays all social enterprises in Ireland on a map.")

# Display user details and forms for update
if st.session_state.get('auth_status') == 'logged_in':
    st.sidebar.title("User Options")
    user_options = st.sidebar.radio("Select an Option:", ["Show Details", "Update Details"])

    if user_options == "Show Details":
        user_data = sheet.find(authenticator.get_user()['email'], in_column=6)
        if user_data:
            user_details = sheet.row_values(user_data.row)
            st.table(pd.DataFrame({
                "Field": ["Name", "Address", "County", "Description", "Eircode", "Email", "Website", "Socials", "Keywords"],
                "Value": user_details
            }))

    elif user_options == "Update Details":
        with st.form("update_details", clear_on_submit=False):
            name = st.text_input("Name", value="")
            address = st.text_input("Address", value="")
            county = st.text_input("County", value="")
            description = st.text_area("Description", value="")
            eircode = st.text_input("Eircode", value="")
            email = st.text_input("Email", value="")
            website = st.text_input("Website", value="")
            socials = st.text_input("Socials", value="")
            keywords = st.text_input("Keywords", value="")
            submitted = st.form_submit_button("Submit")

            if submitted:
                # Update Google Sheets with new details
                user_row = sheet.find(authenticator.get_user()['email'], in_column=6).row
                sheet.update(f'A{user_row}:I{user_row}', [[name, address, county, description, eircode, email, website, socials, keywords]])
                st.success("Details updated successfully!")

if __name__ == '__main__':
    st.title("Social Enterprises in Ireland")
