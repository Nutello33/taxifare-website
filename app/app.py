import streamlit as st
import requests
from datetime import datetime, date, time
import locale
# locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
locale.setlocale(locale.LC_TIME, "")
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError
from geopy.extra.rate_limiter import RateLimiter

# --------- Géocodage ---------
DEFAULT_PICKUP = (-73.961784, 40.803766)
DEFAULT_DROPOFF = (-73.958925, 40.782993)
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
pickup_address = st.text_input("Pickup address", key="pickup_address")
dropoff_address = st.text_input("Dropoff address", key="dropoff_address")

pickup_longitude = st.session_state["pickup_longitude"]
pickup_latitude = st.session_state["pickup_latitude"]
dropoff_longitude = st.session_state["dropoff_longitude"]
dropoff_latitude = st.session_state["dropoff_latitude"]

# --- Nombre de passagers ---
passenger_count = st.number_input(
    "Passenger count", min_value=1, max_value=8, step=1, value=1
)

# --- API endpoint ---
API_URL = "https://taxifare-337592679787.europe-west1.run.app/"


# --- Bouton prédiction ---
if st.button("Prix de la course"):
    info_messages = []

    if pickup_address:
        try:
            location = geocode(pickup_address)
            if location:
                pickup_latitude = float(location.latitude)
                pickup_longitude = float(location.longitude)
                st.session_state["pickup_latitude"] = pickup_latitude
                st.session_state["pickup_longitude"] = pickup_longitude
                info_messages.append(
                    f"Départ géocodé : {pickup_latitude:.6f}, {pickup_longitude:.6f}"
                )
            else:
                st.error("Départ introuvable, vérifie l'adresse de prise en charge.")
                st.stop()
        except GeocoderServiceError as err:
            st.error(f"Erreur géocodage départ : {err}")
            st.stop()
        except Exception as err:
            st.error(f"Erreur inattendue géocodage départ : {err}")
            st.stop()

    if dropoff_address:
        try:
            location = geocode(dropoff_address)
            if location:
                dropoff_latitude = float(location.latitude)
                dropoff_longitude = float(location.longitude)
                st.session_state["dropoff_latitude"] = dropoff_latitude
                st.session_state["dropoff_longitude"] = dropoff_longitude
                info_messages.append(
                    f"Arrivée géocodée : {dropoff_latitude:.6f}, {dropoff_longitude:.6f}"
                )
            else:
                st.error("Arrivée introuvable, vérifie l'adresse de destination.")
                st.stop()
        except GeocoderServiceError as err:
            st.error(f"Erreur géocodage arrivée : {err}")
            st.stop()
        except Exception as err:
            st.error(f"Erreur inattendue géocodage arrivée : {err}")
            st.stop()

    if info_messages:
        st.info(" ｜ ".join(info_messages))

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

        fare_value = prediction["fare"]
        formatted_fare = f"{fare_value:,.2f} $ 🎁"
        st.write(formatted_fare)


    except Exception as e:
        st.error(f"Erreur lors de l'appel API : {e}")
