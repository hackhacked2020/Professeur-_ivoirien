import streamlit as st
import requests
import json
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="Assistant Pédagogique Ivoirien",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Assistant Pédagogique Ivoirien")
st.markdown("Posez vos questions sur les cours !")

# Fonction pour appeler l'API Mistral directement
def call_mistral_api(messages, api_key):
    """Appelle l'API Mistral via HTTP"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "mistral-small-latest",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur API : {str(e)}")
        return None

# Interface utilisateur
with st.sidebar:
    st.header("📤 Charger les cours")
    
    # Récupération de la clé API
    api_key = None
    
    # D'abord essayer de récupérer depuis les secrets
    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
        st.success("✅ Clé API trouvée dans les secrets")
    except:
        # Sinon, demander à l'utilisateur
        api_key = st.text_input("🔑 Clé API Mistral", type="password")
        if api_key:
            st.success("✅ Clé API saisie")
    
    if not api_key:
        st.warning("⚠️ Veuillez configurer votre clé API Mistral")
    
    st.markdown("---")
    
    uploaded_files = st.file_uploader(
        "Déposez vos fichiers (TXT, PDF)",
        type=['txt', 'pdf', 'md', 'docx'],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("📚 Traiter les documents"):
        documents = []
        for file in uploaded_files:
            try:
                # Lire le contenu du fichier
                if file.type == "text/plain" or file.name.endswith('.txt') or file.name.endswith('.md'):
                    content = file.read().decode('utf-8')
                    documents.append(f"Document: {file.name}\n\n{content[:5000]}")  # Limiter pour l'API
                elif file.name.endswith('.pdf'):
                    documents.append(f"Document: {file.name} (Format PDF - Texte non extrait automatiquement)")
                else:
                    documents.append(f"Document: {file.name}")
            except Exception as e:
                st.warning(f"Erreur avec {file.name}: {str(e)}")
        
        if documents:
            st.session_state['documents'] = documents
            st.success(f"✅ {len(documents)} document(s) chargés !")
            st.info("💡 Pour les PDF, vous pouvez copier-coller le texte manuellement dans la zone ci-dessous")

# Zone de texte pour coller du contenu
st.subheader("📝 Ou collez votre texte ici :")
custom_text = st.text_area("Collez le contenu de vos cours :", height=150)

if custom_text:
    if 'documents' not in st.session_state:
        st.session_state['documents'] = []
    st.session_state['documents'].append(f"Texte collé:\n{custom_text}")
    st.success("✅ Texte ajouté !")

# Zone principale
if 'documents' in st.session_state and st.session_state['documents']:
    st.subheader(f"📚 {len(st.session_state['documents'])} document(s) chargés")
    
    # Afficher les documents
    with st.expander("📖 Voir les documents chargés"):
        for i, doc in enumerate(st.session_state['documents']):
            st.markdown(f"**Document {i+1}:**")
            st.text(doc[:200] + "..." if len(doc) > 200 else doc)
            st.markdown("---")
    
    question = st.text_area("💭 Votre question :", height=100)
    
    col1, col2 = st.columns([1, 5])
    with col1:
        ask_button = st.button("🔍 Poser la question", type="primary", use_container_width=True)
    
    if ask_button and question:
        if not api_key:
            st.error("❌ Clé API Mistral requise")
        else:
            with st.spinner("🔎 Recherche dans les documents..."):
                # Préparer le contexte (prendre les 3 premiers documents max)
                context = "\n\n---\n\n".join(st.session_state['documents'][:3])
                
                # Préparer les messages
                messages = [
                    {"role": "system", "content": f"""Tu es un assistant pédagogique pour des élèves ivoiriens.
                    Réponds à la question en utilisant UNIQUEMENT les documents fournis ci-dessous.
                    Si l'information n'est pas dans les documents, dis-le honnêtement.
                    Adapte ton langage pour des élèves.
                    
                    DOCUMENTS:
                    {context}"""},
                    {"role": "user", "content": question}
                ]
                
                # Appeler l'API
                result = call_mistral_api(messages, api_key)
                
                if result and 'choices' in result:
                    st.markdown("### ✨ Réponse :")
                    response_text = result['choices'][0]['message']['content']
                    st.write(response_text)
                    
                    # Afficher l'utilisation
                    if 'usage' in result:
                        tokens = result['usage']['total_tokens']
                        cost = tokens * 0.0000001  # Estimation
                        st.caption(f"📊 Tokens utilisés : {tokens} (~{cost:.6f}$)")
                else:
                    st.error("Impossible d'obtenir une réponse")
else:
    st.info("👈 Commencez par charger des documents dans le menu latéral")

# Pied de page
st.markdown("---")
st.markdown("🚀 Propulsé par Mistral AI | 🇨🇮 Version éducative ivoirienne")

# Instructions
with st.expander("ℹ️ Comment utiliser cette application"):
    st.markdown("""
    1. **Configurez votre clé API** (une fois dans les secrets Streamlit)
    2. **Chargez vos documents** (TXT, ou copiez-collez le texte)
    3. **Posez des questions** sur le contenu
    4. L'IA répondra UNIQUEMENT à partir de vos documents
    
    **Astuce :** Pour les PDF, copiez-collez le texte dans la zone prévue.
    """)
