import streamlit as st
import requests
from datetime import datetime, date
import locale
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError
from geopy.extra.rate_limiter import RateLimiter

locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

DEFAULT_PICKUP = (-73.985428, 40.748817)
DEFAULT_DROPOFF = (-73.985428, 40.748817)

for key, default in {
    "pickup_longitude": DEFAULT_PICKUP[0],
    "pickup_latitude": DEFAULT_PICKUP[1],
    "dropoff_longitude": DEFAULT_DROPOFF[0],
    "dropoff_latitude": DEFAULT_DROPOFF[1],
    "pickup_address": "",
    "dropoff_address": "",
}.items():
    st.session_state.setdefault(key, default)


@st.cache_resource
def get_geocoder():
    geolocator = Nominatim(user_agent="taxifare-app")
    return RateLimiter(geolocator.geocode, min_delay_seconds=1)


geocode = get_geocoder()

st.title("☝🏼 TaxiFare YBB ☝🏼")

#st.markdown("Saisis les informations de ta course :")
"### saisis ce que tu as à saisir hein !"

st.set_page_config(
    page_title="YBB", # => Quick reference - Streamlit
    page_icon="💋",
    layout="centered", # wide
    initial_sidebar_state="auto") # collapsed

# --- Date & heure ---
pickup_date = st.date_input("Pickup date", min_value=date.today())
pickup_date_long = pickup_date.strftime("%A %d %B")
st.write("✅ OK, got it :", pickup_date_long)
pickup_time = st.time_input("Pickup time")
st.write("👌🏼 OK, c'est tout bon ! On sera là pour ", pickup_time.strftime("%H:%M"))

pickup_datetime = datetime.combine(pickup_date, pickup_time)

# --- Coordonnées ---
st.markdown("### géocodage (optionnel)")
pickup_address = st.text_input("Pickup address", key="pickup_address")
dropoff_address = st.text_input("Dropoff address", key="dropoff_address")

geocode_feedback = st.empty()
if st.button("Géocoder les adresses"):
    messages = []
    if pickup_address:
        try:
            location = geocode(pickup_address)
            if location:
                st.session_state["pickup_longitude"] = float(location.longitude)
                st.session_state["pickup_latitude"] = float(location.latitude)
                messages.append(
                    f"Départ : {location.latitude:.6f}, {location.longitude:.6f}"
                )
            else:
                messages.append("Départ introuvable")
        except GeocoderServiceError as err:
            messages.append(f"Erreur géocodage départ : {err}")

    if dropoff_address:
        try:
            location = geocode(dropoff_address)
            if location:
                st.session_state["dropoff_longitude"] = float(location.longitude)
                st.session_state["dropoff_latitude"] = float(location.latitude)
                messages.append(
                    f"Arrivée : {location.latitude:.6f}, {location.longitude:.6f}"
                )
            else:
                messages.append("Arrivée introuvable")
        except GeocoderServiceError as err:
            messages.append(f"Erreur géocodage arrivée : {err}")

    if messages:
        geocode_feedback.info(" ｜ ".join(messages))

pickup_longitude = st.number_input(
    "Pickup longitude", value=st.session_state["pickup_longitude"], format="%.6f", key="pickup_longitude"
)
pickup_latitude = st.number_input(
    "Pickup latitude", value=st.session_state["pickup_latitude"], format="%.6f", key="pickup_latitude"
)
dropoff_longitude = st.number_input(
    "Dropoff longitude", value=st.session_state["dropoff_longitude"], format="%.6f", key="dropoff_longitude"
)
dropoff_latitude = st.number_input(
    "Dropoff latitude", value=st.session_state["dropoff_latitude"], format="%.6f", key="dropoff_latitude"
)

# --- Nombre de passagers ---
passenger_count = st.number_input(
    "Passenger count", min_value=1, max_value=8, step=1, value=1
)

# --- API endpoint ---
API_URL = "https://taxifare-337592679787.europe-west1.run.app/"


# --- Bouton prédiction ---
if st.button("Prix de la course"):

    # Payload à envoyer à FastAPI
    params = {
        "pickup_datetime": pickup_datetime.isoformat(),
        "pickup_longitude": pickup_longitude,
        "pickup_latitude": pickup_latitude,
        "dropoff_longitude": dropoff_longitude,
        "dropoff_latitude": dropoff_latitude,
        "passenger_count": int(passenger_count),
    }

    # st.subheader("Payload envoyé à l’API :")
    # st.json(params)

    # Appel API
    try:
        response = requests.get(f"{API_URL}/predict?", params=params)
        response.raise_for_status()
        prediction = response.json()

        st.success("Prédiction reçue ! 🚕")
        st.write(prediction["fare"])

    except Exception as e:
        st.error(f"Erreur lors de l'appel API : {e}")
