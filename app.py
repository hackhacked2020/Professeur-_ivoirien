import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from docx import Document
import io

st.set_page_config(page_title="Assistant Pédagogique Gemini", layout="wide")
st.title("📚 Assistant Pédagogique (Gemini 1.5 Pro)")

# Configuration API Google (gratuite)
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Gemini 1.5 Pro a un contexte de 1 MILLION de tokens !
model = genai.GenerativeModel('gemini-1.5-pro')

def extract_text_from_file(uploaded_file):
    """Extrait le texte selon le type de fichier"""
    if uploaded_file.type == "application/pdf":
        # Extraction PDF
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        # Extraction DOCX
        doc_bytes = uploaded_file.read()
        doc = Document(io.BytesIO(doc_bytes))
        return "\n".join([para.text for para in doc.paragraphs])
    
    else:
        # TXT et autres
        return uploaded_file.getvalue().decode("utf-8")

# Sidebar pour upload
with st.sidebar:
    st.header("📤 Charger les cours")
    uploaded_files = st.file_uploader(
        "Déposez vos PDF, TXT ou Word",
        type=['pdf', 'txt', 'docx', 'md'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} fichier(s) chargé(s)")
        
        if st.button("🔄 Préparer les documents"):
            with st.spinner("Extraction du texte..."):
                all_texts = []
                for file in uploaded_files:
                    text = extract_text_from_file(file)
                    all_texts.append(f"--- {file.name} ---\n{text[:50000]}")  # Limite pour l'affichage
                
                # Concaténer tous les textes
                full_context = "\n\n".join(all_texts)
                st.session_state['full_context'] = full_context
                st.session_state['files_processed'] = True
                st.success("✅ Documents prêts !")
                
                # Afficher un aperçu
                with st.expander("Aperçu des documents"):
                    st.text(full_context[:1000] + "...")

# Interface principale
if 'files_processed' in st.session_state and st.session_state['files_processed']:
    # Zone de question
    question = st.text_area("💭 Votre question sur les cours :", height=150)
    
    col1, col2 = st.columns([1, 5])
    with col1:
        ask_button = st.button("🔍 Poser la question", type="primary", use_container_width=True)
    
    if ask_button and question:
        with st.spinner("Recherche dans les cours et génération de la réponse..."):
            try:
                # Construction du prompt
                prompt = f"""Tu es un assistant pédagogique expert. Réponds à la question de l'étudiant en utilisant UNIQUEMENT les documents fournis.
                
DOCUMENTS PÉDAGOGIQUES:
{st.session_state['full_context']}

QUESTION DE L'ÉTUDIANT: {question}

INSTRUCTIONS:
- Utilise UNIQUEMENT les informations des documents fournis
- Si l'information n'est pas dans les documents, dis-le clairement
- Explique de manière pédagogique et détaillée
- Structure ta réponse avec des titres et des puces si nécessaire
- Donne des exemples concrets quand c'est possible

RÉPONSE PÉDAGOGIQUE:"""

                # Appel à Gemini (gratuit, 60 requêtes par minute)
                response = model.generate_content(prompt)
                
                # Afficher la réponse
                st.markdown("### ✨ Réponse Pédagogique")
                st.markdown(response.text)
                
                # Ajouter un bouton pour sauvegarder
                st.download_button(
                    label="📥 Sauvegarder la réponse",
                    data=response.text,
                    file_name="reponse_pedagogique.txt",
                    mime="text/plain"
                )
                
                # Métriques d'utilisation (Gemini est gratuit !)
                st.caption("✅ Utilisation gratuite - Gemini 1.5 Pro (1M tokens de contexte)")
                
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.info("Vérifiez votre clé API Google dans les secrets Streamlit")
else:
    st.info("👈 Commencez par charger des documents dans le menu latéral")
    
    # Exemple d'utilisation
    with st.expander("📝 Comment ça marche ?"):
        st.markdown("""
        **Fonctionnalités :**
        - ✅ Traitement de PDF, DOCX, TXT
        - ✅ Contexte de 1 MILLION de tokens (peut tenir plusieurs livres !)
        - ✅ Réponses détaillées et pédagogiques
        - ✅ 100% gratuit (60 requêtes/minute)
        - ✅ Pas de limite de documents
        """)

# Pied de page
st.markdown("---")
st.markdown("🚀 Propulsé par **Google Gemini 1.5 Pro** | **Complètement gratuit** | [Obtenir une clé API](https://makersuite.google.com/app/apikey)")
