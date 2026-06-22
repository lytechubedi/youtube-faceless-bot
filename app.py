import streamlit as st
import os
from google import genai
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

st.set_page_config(page_title="Automation Faceless", page_icon="📺", layout="centered")

st.title("📺 Mon Robot de Publication YouTube Faceless")
st.write("Interface épurée : Tes clés sont sauvegardées en toute sécurité.")

st.write("---")

# --- CHARGEMENT AUTOMATIQUE ET SÉCURISÉ DES CLÉS ---
try:
    cle_api_gemini = st.secrets["GEMINI_API_KEY"]
    client_id = st.secrets["YOUTUBE_CLIENT_ID"]
    client_secret = st.secrets["YOUTUBE_CLIENT_SECRET"]
    refresh_token = st.secrets["YOUTUBE_REFRESH_TOKEN"]
except Exception as e:
    st.error("⚠️ Les clés secrètes ne sont pas encore configurées dans Streamlit Cloud. Va dans Settings > Secrets pour les ajouter.")
    st.stop()

# --- INTERFACE UNIQUE ET RAPIDE ---
st.header("🎬 Ta Vidéo & Tes Idées")
uploaded_file = st.file_uploader("Importe ta vidéo MP4 (déjà prête)", type=["mp4"])
texte_origine = st.text_area("Colle le titre ou la description d'origine ici", placeholder="Ex: Titre d'origine de la vidéo YouTube dont tu t'inspires...")

st.write("---")

# --- ACTION ---
if st.button("🔥 OPTIMISER ET PUBLIER SUR YOUTUBE"):
    if uploaded_file is None:
        st.warning("⚠️ Tu as oublié d'importer ta vidéo.")
    elif not texte_origine:
        st.warning("⚠️ Donne un texte d'origine pour guider l'IA.")
    else:
        try:
            # 1. TRANSFORMATION PAR L'IA
            with st.spinner("🧠 L'IA réécrit tes textes pour l'algorithme..."):
                client_gemini = genai.Client(api_key=cle_api_gemini)
                
                consigne = (
                    f"Tu es un expert mondial en SEO YouTube Shorts et vidéos virales.\n"
                    f"Prends ce texte d'origine :\n'{texte_origine}'\n\n"
                    f"Génère un pack optimisé au format EXACT suivant :\n"
                    f"TITRE: [Ton titre viral ici, max 60 caractères, avec emojis]\n"
                    f"DESCRIPTION: [Ta description optimisée avec mots-clés et les 5 meilleurs hashtags]\n"
                )

                response = client_gemini.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=consigne
                )
                
                texte_ia = response.text
                
                # Extraction automatique du titre et de la description
                titre_final = "Vidéo Automatique"
                description_final = texte_ia
                
                for ligne in texte_ia.split('\n'):
                    if ligne.startswith("TITRE:"):
                        titre_final = ligne.replace("TITRE:", "").strip()
                    if ligne.startswith("DESCRIPTION:"):
                        description_final = ligne.replace("DESCRIPTION:", "").strip()

            # 2. ENVOI SUR YOUTUBE
            with st.spinner("🚀 Connexion à YouTube et téléversement en cours..."):
                chemin_video_temp = "temp_upload.mp4"
                with open(chemin_video_temp, "wb") as f:
                    f.write(uploaded_file.read())

                info_tokens = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
                creds = Credentials.from_authorized_user_info(info_tokens)
                youtube = build("youtube", "v3", credentials=creds)

                body = {
                    "snippet": {
                        "title": titre_final,
                        "description": description_final,
                        "tags": ["faceless", "shorts", "viral"],
                        "categoryId": "22"
                    },
                    "status": {
                        "privacyStatus": "public"
                    }
                }

                media = MediaFileUpload(chemin_video_temp, chunksize=-1, resumable=True, mimetype="video/mp4")
                requete = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
                reponse_youtube = requete.execute()
                
                if os.path.exists(chemin_video_temp):
                    os.remove(chemin_video_temp)

                st.success("🎉 C'EST EN LIGNE ! Ton contenu Faceless est publié !")
                st.write(f"🔗 ID de ta vidéo : {reponse_youtube['id']}")
                st.write(f"**Titre utilisé :** {titre_final}")

        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            if os.path.exists("temp_upload.mp4"):
                os.remove("temp_upload.mp4")
