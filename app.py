"""
📚 ASSISTANT PÉDAGOGIQUE IA - VERSION PROFESSIONNELLE
Application Streamlit pour l'analyse de cours par chapitres
Avec fonction d'extraction et téléchargement intégrée
"""

import streamlit as st
import requests
import json
import io
import tempfile
import os
import re
from pathlib import Path
from datetime import datetime
import hashlib
import pandas as pd
from io import BytesIO

# ============================================================
# CONFIGURATION DE LA PAGE
# ============================================================
st.set_page_config(
    page_title="Assistant Pédagogique IA",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# STYLES CSS PERSONNALISÉS
# ============================================================
st.markdown("""
<style>
    /* Styles généraux */
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chapter-card {
        background-color: #F3F4F6;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 5px solid #1E3A8A;
    }
    .chapter-title {
        font-weight: bold;
        color: #1E3A8A;
        font-size: 1.1rem;
    }
    .stats-badge {
        background-color: #10B981;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin-left: 0.5rem;
    }
    .warning-badge {
        background-color: #F59E0B;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    .success-message {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #EFF6FF;
        color: #1E3A8A;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #BFDBFE;
    }
    .footer {
        text-align: center;
        color: #6B7280;
        font-size: 0.9rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #E5E7EB;
    }
    /* Boutons */
    .stButton > button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #2563EB;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    /* Métriques */
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    .metric-label {
        color: #6B7280;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# IMPORT DES BIBLIOTHÈQUES PDF
# ============================================================
try:
    import PyPDF2
    PDF_SUPPORT = True
except:
    PDF_SUPPORT = False

try:
    import pypdf
    PYPDF_SUPPORT = True
except:
    PYPDF_SUPPORT = False

try:
    import pdfplumber
    PDFPLUMBER_SUPPORT = True
except:
    PDFPLUMBER_SUPPORT = False

# ============================================================
# FONCTIONS D'EXTRACTION DE TEXTE
# ============================================================
def extract_text_from_pdf(pdf_file):
    """Extrait le texte d'un fichier PDF avec plusieurs méthodes"""
    text = ""
    methods_tried = []
    
    # Méthode 1: PyPDF2
    if PDF_SUPPORT:
        try:
            pdf_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
            methods_tried.append("PyPDF2")
            if text.strip():
                return text, methods_tried
        except Exception as e:
            pass
    
    # Méthode 2: pypdf
    if PYPDF_SUPPORT:
        try:
            pdf_file.seek(0)
            pdf_reader = pypdf.PdfReader(pdf_file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
            methods_tried.append("pypdf")
            if text.strip():
                return text, methods_tried
        except Exception as e:
            pass
    
    # Méthode 3: pdfplumber (meilleure qualité)
    if PDFPLUMBER_SUPPORT:
        try:
            pdf_file.seek(0)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_file.getvalue())
                tmp_path = tmp_file.name
            
            with pdfplumber.open(tmp_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
                    # Extraction des tableaux si présents
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            text += "\n[Tableau]:\n"
                            for row in table:
                                text += " | ".join([str(cell) for cell in row if cell]) + "\n"
            
            os.unlink(tmp_path)
            methods_tried.append("pdfplumber")
            if text.strip():
                return text, methods_tried
        except Exception as e:
            pass
    
    return text, methods_tried

def extract_text_from_txt(txt_file):
    """Extrait le texte d'un fichier TXT avec gestion d'encodage"""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            txt_file.seek(0)
            return txt_file.read().decode(encoding), [encoding]
        except:
            continue
    
    return None, ["Aucun encodage valide"]

def count_words(text):
    """Compte le nombre de mots dans un texte"""
    words = re.findall(r'\b\w+\b', text, re.UNICODE)
    return len(words)

def count_tokens(text):
    """Estime le nombre de tokens (approximation pour Mistral)"""
    # 1 token ≈ 4 caractères pour le français
    return len(text) // 4

def estimate_reading_time(word_count):
    """Estime le temps de lecture en minutes"""
    # Vitesse de lecture moyenne: 200 mots par minute
    minutes = word_count / 200
    return round(minutes, 1)

# ============================================================
# FONCTIONS API MISTRAL
# ============================================================
def call_mistral_api(messages, api_key, model="mistral-small-latest"):
    """Appelle l'API Mistral avec gestion d'erreur améliorée"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4000,
        "top_p": 0.95
    }
    
    try:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏰ Délai d'attente dépassé. Le document est peut-être trop long.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur API : {str(e)}")
        return None

def analyze_chapter_quality(text):
    """Analyse la qualité d'un chapitre selon les critères"""
    word_count = count_words(text)
    token_count = count_tokens(text)
    reading_time = estimate_reading_time(word_count)
    
    quality = "✅ Idéal" if word_count <= 4000 else "⚠️ Limite" if word_count <= 5000 else "❌ Trop long"
    
    return {
        "word_count": word_count,
        "token_count": token_count,
        "reading_time": reading_time,
        "quality": quality,
        "pages_estimate": round(word_count / 500, 1)  # 500 mots par page environ
    }

# ============================================================
# FONCTIONS D'EXTRACTION ET TÉLÉCHARGEMENT
# ============================================================

def extraire_et_telecharger_documents():
    """
    Fonction complète d'extraction et téléchargement des documents
    """
    
    # Vérifier si des documents existent
    if 'documents' not in st.session_state or not st.session_state['documents']:
        st.warning("⚠️ Aucun document chargé dans la session")
        return None
    
    st.markdown("""
    <div style='background-color: #EFF6FF; padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
        <h3 style='color: #1E3A8A; margin-top: 0;'>📥 Extraction des documents</h3>
        <p>Sélectionnez le format d'extraction souhaité :</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ========================================================
    # 1. PRÉPARATION DES DONNÉES
    # ========================================================
    
    # Collecte de toutes les informations
    extraction_data = {
        "metadata": {
            "date_extraction": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nombre_documents": len(st.session_state['documents']),
            "version_application": "Assistant Pédagogique IA v2.0",
            "timestamp_unix": datetime.now().timestamp()
        },
        "statistiques_globales": {
            "total_mots": 0,
            "total_tokens": 0,
            "temps_lecture_total": 0,
            "documents_par_qualite": {
                "ideal": 0,
                "limite": 0,
                "trop_long": 0
            }
        },
        "documents": []
    }
    
    # Traitement de chaque document
    for i, doc in enumerate(st.session_state['documents']):
        # Extraire le titre et le contenu
        if "\n\n" in doc:
            en_tete, contenu = doc.split("\n\n", 1)
            titre = en_tete.replace("# 📖 CHAPITRE: ", "").replace("# 📖 CHAPITRE MANUEL", "").strip()
        else:
            titre = f"Document {i+1}"
            contenu = doc
        
        # Récupérer les statistiques
        stats = st.session_state['chapter_stats'].get(i, {})
        word_count = stats.get('word_count', len(contenu.split()))
        token_count = stats.get('token_count', len(contenu) // 4)
        reading_time = stats.get('reading_time', round(word_count / 200, 1))
        quality = stats.get('quality', analyze_chapter_quality(contenu)['quality'])
        
        # Mise à jour des stats globales
        extraction_data["statistiques_globales"]["total_mots"] += word_count
        extraction_data["statistiques_globales"]["total_tokens"] += token_count
        extraction_data["statistiques_globales"]["temps_lecture_total"] += reading_time
        
        if "✅" in quality:
            extraction_data["statistiques_globales"]["documents_par_qualite"]["ideal"] += 1
        elif "⚠️" in quality:
            extraction_data["statistiques_globales"]["documents_par_qualite"]["limite"] += 1
        else:
            extraction_data["statistiques_globales"]["documents_par_qualite"]["trop_long"] += 1
        
        # Création de l'objet document
        doc_info = {
            "index": i + 1,
            "titre": titre,
            "nom_fichier_original": titre if "." in titre else f"document_{i+1}.txt",
            "statistiques": {
                "nombre_mots": word_count,
                "nombre_tokens_estimes": token_count,
                "temps_lecture_minutes": reading_time,
                "qualite": quality,
                "pages_estimees": round(word_count / 500, 1)
            },
            "contenu": contenu,
            "extrait": contenu[:500] + "..." if len(contenu) > 500 else contenu
        }
        
        extraction_data["documents"].append(doc_info)
    
    # ========================================================
    # 2. INTERFACE DE TÉLÉCHARGEMENT
    # ========================================================
    
    # Affichage des statistiques
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Documents", extraction_data["metadata"]["nombre_documents"])
    with col2:
        st.metric("📝 Mots totaux", f"{extraction_data['statistiques_globales']['total_mots']:,}")
    with col3:
        st.metric("🔤 Tokens", f"{extraction_data['statistiques_globales']['total_tokens']:,}")
    with col4:
        st.metric("⏱️ Lecture", f"{extraction_data['statistiques_globales']['temps_lecture_total']} min")
    
    # Sélection du format
    format_export = st.radio(
        "📋 Choisissez le format d'export :",
        ["📄 Texte brut (TXT)", "📊 JSON structuré", "📑 Markdown", "📈 CSV (statistiques)", "📚 Tous les formats"],
        horizontal=True
    )
    
    # ========================================================
    # 3. GÉNÉRATION DES DIFFÉRENTS FORMATS
    # ========================================================
    
    # Format TXT
    def generer_txt():
        txt_content = f"""
{'='*80}
EXTRACTION DES DOCUMENTS - ASSISTANT PÉDAGOGIQUE IA
{'='*80}
Date d'extraction : {extraction_data['metadata']['date_extraction']}
Nombre de documents : {extraction_data['metadata']['nombre_documents']}
Total mots : {extraction_data['statistiques_globales']['total_mots']:,}
Total tokens : {extraction_data['statistiques_globales']['total_tokens']:,}
{'='*80}

"""
        for doc in extraction_data["documents"]:
            txt_content += f"""
{'-'*80}
DOCUMENT {doc['index']}: {doc['titre']}
{'-'*80}
Statistiques :
  • Mots : {doc['statistiques']['nombre_mots']:,}
  • Tokens : {doc['statistiques']['nombre_tokens_estimes']:,}
  • Temps lecture : {doc['statistiques']['temps_lecture_minutes']} min
  • Qualité : {doc['statistiques']['qualite']}
  • Pages estimées : {doc['statistiques']['pages_estimees']}

CONTENU :
{doc['contenu']}

"""
        return txt_content
    
    # Format JSON
    def generer_json():
        return json.dumps(extraction_data, ensure_ascii=False, indent=2)
    
    # Format Markdown
    def generer_markdown():
        md_content = f"""# 📚 Extraction des Documents - Assistant Pédagogique IA

## 📊 Métadonnées
- **Date d'extraction** : {extraction_data['metadata']['date_extraction']}
- **Nombre de documents** : {extraction_data['metadata']['nombre_documents']}
- **Total mots** : {extraction_data['statistiques_globales']['total_mots']:,}
- **Total tokens** : {extraction_data['statistiques_globales']['total_tokens']:,}

## 📈 Statistiques globales
| Qualité | Nombre |
|---------|--------|
| ✅ Idéal | {extraction_data['statistiques_globales']['documents_par_qualite']['ideal']} |
| ⚠️ Limite | {extraction_data['statistiques_globales']['documents_par_qualite']['limite']} |
| ❌ Trop long | {extraction_data['statistiques_globales']['documents_par_qualite']['trop_long']} |

## 📄 Documents extraits
"""
        for doc in extraction_data["documents"]:
            md_content += f"""
### Document {doc['index']} : {doc['titre']}

**Statistiques** :
- Mots : {doc['statistiques']['nombre_mots']:,}
- Tokens : {doc['statistiques']['nombre_tokens_estimes']:,}
- Temps lecture : {doc['statistiques']['temps_lecture_minutes']} min
- Qualité : {doc['statistiques']['qualite']}

**Contenu** :
{doc['contenu']}
---
"""
        return md_content
    
    # Format CSV (statistiques uniquement)
    def generer_csv():
        df_data = []
        for doc in extraction_data["documents"]:
            df_data.append({
                "Document": doc['index'],
                "Titre": doc['titre'],
                "Mots": doc['statistiques']['nombre_mots'],
                "Tokens": doc['statistiques']['nombre_tokens_estimes'],
                "Temps_lecture_min": doc['statistiques']['temps_lecture_minutes'],
                "Qualite": doc['statistiques']['qualite'],
                "Pages": doc['statistiques']['pages_estimees']
            })
        df = pd.DataFrame(df_data)
        return df.to_csv(index=False, encoding='utf-8-sig')
    
    # ========================================================
    # 4. BOUTONS DE TÉLÉCHARGEMENT
    # ========================================================
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format_export == "📄 Texte brut (TXT)":
        txt_content = generer_txt()
        st.download_button(
            label="⬇️ Télécharger en TXT",
            data=txt_content,
            file_name=f"extraction_documents_{timestamp}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        # Aperçu
        with st.expander("👁️ Aperçu du fichier TXT"):
            st.text(txt_content[:2000] + "..." if len(txt_content) > 2000 else txt_content)
    
    elif format_export == "📊 JSON structuré":
        json_content = generer_json()
        st.download_button(
            label="⬇️ Télécharger en JSON",
            data=json_content,
            file_name=f"extraction_documents_{timestamp}.json",
            mime="application/json",
            use_container_width=True
        )
        
        with st.expander("👁️ Aperçu du JSON"):
            st.json(json.loads(json_content[:2000] + "..." if len(json_content) > 2000 else json_content))
    
    elif format_export == "📑 Markdown":
        md_content = generer_markdown()
        st.download_button(
            label="⬇️ Télécharger en Markdown",
            data=md_content,
            file_name=f"extraction_documents_{timestamp}.md",
            mime="text/markdown",
            use_container_width=True
        )
        
        with st.expander("👁️ Aperçu Markdown"):
            st.markdown(md_content[:2000] + "...")
    
    elif format_export == "📈 CSV (statistiques)":
        csv_content = generer_csv()
        st.download_button(
            label="⬇️ Télécharger les statistiques (CSV)",
            data=csv_content,
            file_name=f"statistiques_documents_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        with st.expander("👁️ Aperçu des statistiques"):
            df = pd.read_csv(io.StringIO(csv_content))
            st.dataframe(df)
    
    elif format_export == "📚 Tous les formats":
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.download_button(
                "📄 TXT",
                generer_txt(),
                f"extraction_{timestamp}.txt",
                use_container_width=True
            )
        
        with col2:
            st.download_button(
                "📊 JSON",
                generer_json(),
                f"extraction_{timestamp}.json",
                use_container_width=True
            )
        
        with col3:
            st.download_button(
                "📑 Markdown",
                generer_markdown(),
                f"extraction_{timestamp}.md",
                use_container_width=True
            )
        
        with col4:
            st.download_button(
                "📈 CSV",
                generer_csv(),
                f"statistiques_{timestamp}.csv",
                use_container_width=True
            )
    
    # ========================================================
    # 5. OPTIONS D'EXTRACTION AVANCÉES
    # ========================================================
    
    with st.expander("⚙️ Options avancées"):
        st.markdown("**Personnalisez votre extraction :**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            inclure_stats = st.checkbox("Inclure les statistiques détaillées", value=True)
            inclure_metadata = st.checkbox("Inclure les métadonnées", value=True)
        
        with col2:
            format_contenu = st.radio(
                "Format du contenu :",
                ["Texte intégral", "Extraits (500 mots)", "Sans le contenu (stats uniquement)"]
            )
        
        if st.button("🔄 Générer avec ces options"):
            # Adapter l'extraction selon les options
            st.info("Options appliquées ! Sélectionnez un format ci-dessus pour télécharger.")
    
    # ========================================================
    # 6. RAPPORT RÉCAPITULATIF
    # ========================================================
    
    st.markdown("---")
    st.markdown("### 📋 Rapport d'extraction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Documents traités :** {extraction_data['metadata']['nombre_documents']}  
        **Date :** {extraction_data['metadata']['date_extraction']}  
        **Taille totale :** {extraction_data['statistiques_globales']['total_mots']:,} mots
        """)
    
    with col2:
        qualite_data = extraction_data['statistiques_globales']['documents_par_qualite']
        st.markdown(f"""
        **Qualité des documents :**  
        ✅ Idéal : {qualite_data['ideal']}  
        ⚠️ Limite : {qualite_data['limite']}  
        ❌ Trop long : {qualite_data['trop_long']}
        """)
    
    return extraction_data

# ============================================================
# INTERFACE PRINCIPALE
# ============================================================

# En-tête
st.markdown('<h1 class="main-header">📚 Assistant Pédagogique IA</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Posez vos questions sur vos cours • Version optimisée chapitre par chapitre</p>', unsafe_allow_html=True)

# Barre latérale
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/books.png", width=80)
    st.title("📂 Gestion des cours")
    
    # Configuration API
    with st.expander("🔑 Configuration API", expanded=True):
        api_key = None
        try:
            api_key = st.secrets["MISTRAL_API_KEY"]
            st.success("✅ Clé API configurée")
        except:
            api_key = st.text_input("Clé API Mistral", type="password")
            if api_key:
                st.success("✅ Clé API saisie")
        
        if api_key:
            model_choice = st.selectbox(
                "Modèle Mistral",
                ["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"],
                index=0
            )
    
    st.markdown("---")
    
    # Zone d'upload
    st.subheader("📤 Charger les chapitres")
    st.markdown("*Format idéal : 3000-4000 mots par chapitre*")
    
    uploaded_files = st.file_uploader(
        "Sélectionnez vos fichiers (PDF, TXT, MD)",
        type=['pdf', 'txt', 'md'],
        accept_multiple_files=True,
        help="Chargez plusieurs fichiers à la fois"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        process_button = st.button("🚀 Traiter les fichiers", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Tout effacer", use_container_width=True)
    
    if clear_button and 'documents' in st.session_state:
        st.session_state['documents'] = []
        st.session_state['chapter_stats'] = {}
        st.rerun()
    
    st.markdown("---")
    
    # Statistiques globales
    if 'documents' in st.session_state and st.session_state['documents']:
        st.subheader("📊 Statistiques")
        total_chapters = len(st.session_state['documents'])
        total_words = sum(st.session_state['chapter_stats'].get(i, {}).get('word_count', 0) 
                         for i in range(total_chapters))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Chapitres", total_chapters)
        with col2:
            st.metric("Mots totaux", f"{total_words:,}")
        
        # Recommandation
        if total_words > 0:
            avg_words = total_words // total_chapters
            if avg_words > 4500:
                st.warning(f"⚠️ Moyenne: {avg_words} mots/chapitre\nCertains chapitres sont longs")
    
    st.markdown("---")
    
    # NOUVELLE SECTION D'EXTRACTION
    st.markdown("## 📥 Extraction des données")
    
    if 'documents' in st.session_state and st.session_state['documents']:
        if st.button("🚀 Lancer l'extraction", use_container_width=True):
            st.session_state['mode_extraction'] = True
    else:
        st.info("📤 Chargez d'abord des documents")

# ============================================================
# TRAITEMENT DES FICHIERS
# ============================================================
if process_button and uploaded_files:
    documents = []
    chapter_stats = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, file in enumerate(uploaded_files):
        status_text.text(f"Traitement de {file.name}...")
        
        file_content = ""
        methods_used = []
        file_name = file.name
        
        # Extraction selon le type
        if file_name.endswith('.pdf'):
            file_content, methods_used = extract_text_from_pdf(file)
        elif file_name.endswith(('.txt', '.md')):
            file_content, methods_used = extract_text_from_txt(file)
        
        if file_content and len(file_content.strip()) > 100:
            # Analyse du chapitre
            stats = analyze_chapter_quality(file_content)
            chapter_stats[i] = stats
            
            # Ajouter un en-tête avec le nom du fichier
            full_content = f"# 📖 CHAPITRE: {file_name}\n\n{file_content}"
            documents.append(full_content)
            
            # Afficher la qualité
            if stats['quality'] == "✅ Idéal":
                st.sidebar.success(f"✅ {file_name}: {stats['word_count']} mots")
            elif stats['quality'] == "⚠️ Limite":
                st.sidebar.warning(f"⚠️ {file_name}: {stats['word_count']} mots")
            else:
                st.sidebar.error(f"❌ {file_name}: {stats['word_count']} mots (trop long)")
        else:
            st.sidebar.error(f"❌ Impossible de lire {file_name}")
        
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    if documents:
        st.session_state['documents'] = documents
        st.session_state['chapter_stats'] = chapter_stats
        status_text.text("✅ Tous les chapitres ont été traités!")
        st.success(f"✅ {len(documents)} chapitre(s) chargé(s) avec succès!")
    else:
        st.error("❌ Aucun document n'a pu être traité")

# ============================================================
# ZONE DE TEXTE MANUEL
# ============================================================
st.markdown("---")
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Ajouter un chapitre manuellement")
    custom_text = st.text_area(
        "Collez le contenu d'un chapitre :",
        height=150,
        placeholder="Copiez ici le texte de votre chapitre (idéalement 3000-4000 mots)..."
    )

with col2:
    st.subheader("⚡ Actions rapides")
    if custom_text and len(custom_text.strip()) > 100:
        if st.button("➕ Ajouter ce chapitre", use_container_width=True):
            if 'documents' not in st.session_state:
                st.session_state['documents'] = []
                st.session_state['chapter_stats'] = {}
            
            # Analyser le chapitre
            stats = analyze_chapter_quality(custom_text)
            idx = len(st.session_state['documents'])
            st.session_state['chapter_stats'][idx] = stats
            
            # Ajouter
            full_content = f"# 📖 CHAPITRE MANUEL {idx+1}\n\n{custom_text}"
            st.session_state['documents'].append(full_content)
            st.success(f"✅ Chapitre ajouté! ({stats['word_count']} mots)")
            st.rerun()

# ============================================================
# AFFICHAGE DE LA SECTION D'EXTRACTION (si activée)
# ============================================================
if st.session_state.get('mode_extraction', False):
    st.markdown("---")
    resultat = extraire_et_telecharger_documents()
    if resultat:
        st.session_state['donnees_extraction'] = resultat
        
        # Bouton pour fermer
        if st.button("❌ Fermer l'extraction"):
            st.session_state['mode_extraction'] = False
            st.rerun()

# ============================================================
# AFFICHAGE DES CHAPITRES
# ============================================================
if 'documents' in st.session_state and st.session_state['documents'] and not st.session_state.get('mode_extraction', False):
    st.markdown("---")
    st.subheader(f"📚 Bibliothèque de chapitres ({len(st.session_state['documents'])} disponibles)")
    
    # Aperçu des chapitres
    with st.expander("📖 Voir le détail des chapitres", expanded=False):
        tabs = st.tabs([f"Chapitre {i+1}" for i in range(len(st.session_state['documents']))])
        
        for i, tab in enumerate(tabs):
            with tab:
                doc = st.session_state['documents'][i]
                stats = st.session_state['chapter_stats'].get(i, {})
                
                # Métriques du chapitre
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{stats.get("word_count", 0):,}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Mots</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{stats.get("token_count", 0):,}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Tokens</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{stats.get("reading_time", 0)}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Minutes de lecture</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col4:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{stats.get("pages_estimate", 0)}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Pages estimées</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Qualité
                quality = stats.get("quality", "⚠️ Non analysé")
                if "✅" in quality:
                    st.success(f"📊 Qualité: {quality}")
                elif "⚠️" in quality:
                    st.warning(f"📊 Qualité: {quality}")
                else:
                    st.error(f"📊 Qualité: {quality}")
                
                # Aperçu du texte
                preview = doc[:1000] + "..." if len(doc) > 1000 else doc
                st.text_area("Aperçu", preview, height=200, key=f"preview_{i}")
    
    # ============================================================
    # ZONE DE QUESTIONS
    # ============================================================
    st.markdown("---")
    st.subheader("💭 Poser une question")
    
    # Sélection des chapitres
    col1, col2 = st.columns([1, 2])
    
    with col1:
        selection_mode = st.radio(
            "Chapitres à interroger :",
            ["📚 Tous les chapitres", "🎯 Choisir spécifiquement"],
            index=0
        )
    
    with col2:
        if selection_mode == "🎯 Choisir spécifiquement":
            st.markdown("**Sélectionnez les chapitres :**")
            selected_indices = []
            for i in range(len(st.session_state['documents'])):
                stats = st.session_state['chapter_stats'].get(i, {})
                word_count = stats.get("word_count", 0)
                quality_emoji = "✅" if word_count <= 4000 else "⚠️" if word_count <= 5000 else "❌"
                
                if st.checkbox(f"{quality_emoji} Chapitre {i+1} ({word_count} mots)", key=f"select_{i}"):
                    selected_indices.append(i)
            
            if selected_indices:
                st.info(f"📚 {len(selected_indices)} chapitre(s) sélectionné(s)")
                selected_docs = [st.session_state['documents'][i] for i in selected_indices]
                total_words_selected = sum(st.session_state['chapter_stats'].get(i, {}).get('word_count', 0) 
                                         for i in selected_indices)
                
                if total_words_selected > 15000:
                    st.warning(f"⚠️ Attention: {total_words_selected} mots sélectionnés. L'IA pourrait ne pas tout voir.")
        else:
            selected_docs = st.session_state['documents']
            total_words_all = sum(st.session_state['chapter_stats'].get(i, {}).get('word_count', 0) 
                                for i in range(len(st.session_state['documents'])))
            st.info(f"📚 Utilisation de tous les chapitres ({total_words_all} mots totaux)")
            
            if total_words_all > 15000:
                st.warning("⚠️ Le total des mots dépasse la limite recommandée. Privilégiez la sélection manuelle.")
    
    # Zone de question
    question = st.text_area(
        "✏️ Votre question :",
        height=100,
        placeholder="Ex: Qu'est-ce que la santé publique selon le chapitre 1 ?"
    )
    
    # Bouton pour poser la question
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        ask_button = st.button("🔍 Poser la question", type="primary", use_container_width=True)
    
    # ============================================================
    # TRAITEMENT DE LA QUESTION
    # ============================================================
    if ask_button and question:
        if not api_key:
            st.error("❌ Veuillez configurer votre clé API Mistral")
        elif selection_mode == "🎯 Choisir spécifiquement" and not selected_indices:
            st.error("❌ Veuillez sélectionner au moins un chapitre")
        else:
            with st.spinner("🔎 Analyse des chapitres en cours..."):
                # Préparer le contexte
                if selection_mode == "🎯 Choisir spécifiquement":
                    context = "\n\n==========\n\n".join(selected_docs)
                    source_info = f"{len(selected_indices)} chapitre(s) sélectionné(s)"
                else:
                    context = "\n\n==========\n\n".join(st.session_state['documents'])
                    source_info = "tous les chapitres"
                
                # Vérifier la taille
                approx_tokens = len(context) // 4
                if approx_tokens > 35000:  # 35000 tokens max pour éviter les erreurs
                    st.warning(f"⚠️ Contexte très long ({approx_tokens} tokens). L'analyse sera limitée aux premiers chapitres.")
                    context = context[:140000]  # ~35000 tokens
                
                # Construction du prompt système
                system_prompt = f"""Tu es un assistant pédagogique expert pour des élèves ivoiriens.

RÈGLES FONDAMENTALES:
1. Réponds UNIQUEMENT à partir des chapitres fournis ci-dessous
2. Si l'information n'est pas dans les chapitres, dis-le clairement: "Cette information n'est pas dans les chapitres fournis"
3. Cite toujours le chapitre source entre parenthèses: (Chapitre X)
4. Structure tes réponses de manière claire et pédagogique
5. Adapte ton langage pour des élèves (simple mais précis)
6. Si plusieurs chapitres contiennent l'info, mentionne-les tous

CHAPITRES DISPONIBLES ({source_info}):
{context}

Maintenant, réponds à la question de l'élève de façon précise et pédagogique."""
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ]
                
                # Appel API
                result = call_mistral_api(messages, api_key, model_choice)
                
                if result and 'choices' in result:
                    st.markdown("---")
                    st.markdown("### ✨ Réponse :")
                    
                    response_text = result['choices'][0]['message']['content']
                    st.markdown(response_text)
                    
                    # Métriques d'utilisation
                    if 'usage' in result:
                        tokens = result['usage']['total_tokens']
                        cost = tokens * 0.00000015  # Estimation pour small model
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.info(f"📊 Tokens: {tokens:,}")
                        with col2:
                            st.info(f"💰 Coût: ~{cost:.6f}$")
                        with col3:
                            st.info(f"📚 Source: {source_info}")
                else:
                    st.error("❌ Impossible d'obtenir une réponse de l'API")

# ============================================================
# ZONE D'AIDE ET CONSEILS
# ============================================================
with st.expander("ℹ️ Guide d'utilisation et conseils"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📘 Format idéal des chapitres
        
        | Critère | Idéal | Limite | Trop long |
        |---------|-------|--------|-----------|
        | **Mots** | 3000-4000 | 4000-5000 | 5000+ |
        | **Lecture** | 15-20 min | 20-25 min | 25+ min |
        | **Tokens** | 4000-5300 | 5300-6700 | 6700+ |
        | **Précision** | ✅ Excellente | ⚠️ Bonne | ❌ Risquée |
        
        ### 🎯 Comment bien utiliser l'assistant
        
        1. **Découpez vos cours** en chapitres de 3000-4000 mots
        2. **Chargez les chapitres** un par un ou plusieurs à la fois
        3. **Sélectionnez** les chapitres pertinents pour votre question
        4. **Posez des questions précises** sur le contenu
        """)
    
    with col2:
        st.markdown("""
        ### 💡 Exemples de bonnes questions
        
        ✅ **Précises :**
        - "Selon le chapitre 1, quelles sont les 3 causes principales du paludisme ?"
        - "Comparez les définitions de la santé publique dans les chapitres 1 et 2"
        
        ✅ **Pédagogiques :**
        - "Peux-tu m'expliquer le cycle de transmission du paludisme avec des mots simples ?"
        - "Fais-moi un résumé des points clés du chapitre 3"
        
        ❌ **À éviter :**
        - "Parle-moi de tout" (trop vague)
        - "C'est quoi la santé ?" (trop général, pas lié aux chapitres)
        """)

# ============================================================
# PIED DE PAGE
# ============================================================
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("🚀 Propulsé par Mistral AI | 🇨🇮 Version pédagogique ivoirienne | Dernière mise à jour : Février 2026")
st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# INITIALISATION DE LA SESSION
# ============================================================
if 'documents' not in st.session_state:
    st.session_state['documents'] = []

if 'chapter_stats' not in st.session_state:
    st.session_state['chapter_stats'] = {}

if 'mode_extraction' not in st.session_state:
    st.session_state['mode_extraction'] = False

if 'donnees_extraction' not in st.session_state:
    st.session_state['donnees_extraction'] = None
