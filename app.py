import streamlit as st
import os
from google import genai
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import requests

st.set_page_config(page_title="Automation Faceless", page_icon="📺", layout="centered")

st.title("📺 Mon Robot de Publication YouTube Faceless")

# --- CHARGEMENT DES SECRETS DE BASE ---
try:
    cle_api_gemini = st.secrets["GEMINI_API_KEY"]
    client_id = st.secrets["YOUTUBE_CLIENT_ID"]
    client_secret = st.secrets["YOUTUBE_CLIENT_SECRET"]
except Exception as e:
    st.error("⚠️ Configure d'abord GEMINI_API_KEY, YOUTUBE_CLIENT_ID et YOUTUBE_CLIENT_SECRET dans tes Secrets Streamlit.")
    st.stop()

# --- VÉRIFICATION DU REFRESH TOKEN ---
if "YOUTUBE_REFRESH_TOKEN" in st.secrets:
    # Si le token existe, l'application s'affiche normalement
    refresh_token = st.secrets["YOUTUBE_REFRESH_TOKEN"]
    st.success("✅ Connexion YouTube opérationnelle et sécurisée.")
    
    st.write("---")
    st.header("🎬 Ta Vidéo & Tes Idées")
    uploaded_file = st.file_uploader("Importe ta vidéo MP4", type=["mp4"])
    texte_origine = st.text_area("Colle le titre ou la description d'origine ici")

    if st.button("🔥 OPTIMISER ET PUBLIER SUR YOUTUBE"):
        if uploaded_file is None or not texte_origine:
            st.warning("⚠️ Remplis tous les champs avant de publier.")
        else:
            try:
                with st.spinner("🧠 L'IA réécrit tes textes..."):
                    client_gemini = genai.Client(api_key=cle_api_gemini)
                    consigne = f"Prends ce texte :\n'{texte_origine}'\nGénère un format :\nTITRE: [Titre viral 60 car]\nDESCRIPTION: [Description + hashtags]"
                    response = client_gemini.models.generate_content(model='gemini-2.5-flash', contents=consigne)
                    texte_ia = response.text
                    
                    titre_final = "Vidéo Shorts"
                    description_final = texte_ia
                    for ligne in texte_ia.split('\n'):
                        if ligne.startswith("TITRE:"): titre_final = ligne.replace("TITRE:", "").strip()
                        if ligne.startswith("DESCRIPTION:"): description_final = ligne.replace("DESCRIPTION:", "").strip()

                with st.spinner("🚀 Téléversement sur YouTube..."):
                    chemin_video_temp = "temp_upload.mp4"
                    with open(chemin_video_temp, "wb") as f:
                        f.write(uploaded_file.read())

                    info_tokens = {"client_id": client_id, "client_secret": client_secret, "refresh_token": refresh_token, "token_uri": "https://oauth2.googleapis.com/token"}
                    creds = Credentials.from_authorized_user_info(info_tokens)
                    youtube = build("youtube", "v3", credentials=creds)

                    body = {"snippet": {"title": titre_final, "description": description_final, "tags": ["shorts", "viral"], "categoryId": "22"}, "status": {"privacyStatus": "public"}}
                    media = MediaFileUpload(chemin_video_temp, chunksize=-1, resumable=True, mimetype="video/mp4")
                    requete = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
                    reponse_youtube = requete.execute()
                    
                    if os.path.exists(chemin_video_temp): os.remove(chemin_video_temp)
                    st.success(f"🎉 C'EST EN LIGNE ! ID : {reponse_youtube['id']}")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")

else:
    # Si le token est manquant, on affiche l'outil de génération automatique
    st.warning("🔑 Configuration initiale : Liaison avec ton compte YouTube")
    
    url_actuelle = st.text_input("Colle l'URL complète de cette page Streamlit (sans rien après .app) :", placeholder="https://ton-app.streamlit.app")
    
    if url_actuelle:
        if url_actuelle.endswith("/"):
            url_actuelle = url_actuelle[:-1]
            
        # Création du lien de connexion unique pour TA chaîne
        lien_autorisation = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={url_actuelle}&"
            f"response_type=code&"
            f"scope=https://www.googleapis.com/auth/youtube.upload&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        
        st.markdown(f"### [🔗 CLIQUE ICI POUR CONNECTER TA CHAÎNE YOUTUBE]({lien_autorisation})")
        st.caption("Une fois connecté, Google va te renvoyer ici avec un code secret dans la barre d'adresse.")

    # Détection automatique du retour de Google
    if "code" in st.query_params:
        code_recu = st.query_params["code"]
        
        with st.spinner("🔄 Échange du code contre ton Refresh Token définitif..."):
            url_token = "https://oauth2.googleapis.com/token"
            data = {
                "code": code_recu,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": url_actuelle,
                "grant_type": "authorization_code"
            }
            response = requests.post(url_token, data=data)
            resultat = response.json()
            
            if "refresh_token" in resultat:
                st.success("🎯 REFRESH TOKEN GÉNÉRÉ AVEC SUCCÈS !")
                st.write("Copie cette ligne et ajoute-la dans tes **Secrets Streamlit** :")
                st.code(f'YOUTUBE_REFRESH_TOKEN = "{resultat["refresh_token"]}"')
                st.info("Une fois la ligne ajoutée et sauvegardée dans tes Secrets, actualise la page pour faire disparaître cet écran !")
            else:
                st.error(f"Erreur Google : {resultat}")
