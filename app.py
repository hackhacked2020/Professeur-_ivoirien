import streamlit as st
import os
from mistralai import Mistral
import tempfile
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="Assistant Pédagogique",
    page_icon="📚",
    layout="wide"
)

# Titre
st.title("📚 Assistant Pédagogique IA")
st.markdown("Posez vos questions sur les cours !")

# Initialisation du client Mistral
@st.cache_resource
def init_mistral():
    api_key = st.secrets["MISTRAL_API_KEY"]
    return Mistral(api_key=api_key)

# Zone de téléchargement des fichiers
with st.sidebar:
    st.header("📤 Charger les cours")
    uploaded_files = st.file_uploader(
        "Déposez vos PDF, TXT ou Word",
        type=['pdf', 'txt', 'docx', 'md'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} fichier(s) chargé(s)")
        
        # Bouton pour traiter les fichiers
        if st.button("🔄 Traiter les documents"):
            with st.spinner("Analyse des documents en cours..."):
                # Sauvegarder temporairement les fichiers
                file_texts = []
                for uploaded_file in uploaded_files:
                    # Lire le contenu (simplifié pour l'exemple)
                    text = "Contenu extrait du fichier: " + uploaded_file.name + "\n"
                    file_texts.append(text)
                
                # Sauvegarder dans la session
                st.session_state['documents'] = file_texts
                st.success("Documents prêts !")

# Interface principale
if 'documents' in st.session_state and st.session_state['documents']:
    # Afficher la liste des documents chargés
    with st.expander("📖 Voir les documents chargés"):
        for i, doc in enumerate(st.session_state['documents']):
            st.write(f"{i+1}. {doc[:100]}...")
    
    # Zone de question
    question = st.text_area("💭 Votre question :", height=100)
    
    if st.button("🔍 Poser la question") and question:
        with st.spinner("Recherche dans les cours..."):
            try:
                # Version simplifiée - en réalité on ferait une recherche vectorielle
                context = "\n".join(st.session_state['documents'])
                
                # Appel à Mistral
                client = init_mistral()
                response = client.chat.complete(
                    model="mistral-small-latest",
                    messages=[
                        {"role": "system", "content": f"Réponds à la question en utilisant UNIQUEMENT ces documents:\n{context}"},
                        {"role": "user", "content": question}
                    ]
                )
                
                # Afficher la réponse
                st.markdown("### ✨ Réponse :")
                st.write(response.choices[0].message.content)
                
                # Afficher le coût estimé
                st.caption("💡 Coût approximatif : 0.001$ (offert pour les premiers tests)")
                
            except Exception as e:
                st.error(f"Erreur : {e}")
else:
    st.info("👈 Commencez par charger des documents dans le menu latéral")

# Pied de page
st.markdown("---")
st.markdown("🚀 Propulsé par Mistral AI | Gratuit pour usage éducatif")
