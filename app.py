import streamlit.components.v1 as components
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timezone, timedelta

def get_paris_now():
    """Retourne la date et l'heure courante au fuseau horaire de Paris / Massilly (UTC+2 CEST)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Paris"))
    except Exception:
        return datetime.now(timezone.utc) + timedelta(hours=2)

def get_paris_now_str(with_ms=False):
    dt = get_paris_now()
    if with_ms:
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return dt.strftime("%Y-%m-%d %H:%M:%S")


try:
    from streamlit_gsheets import GSheetsConnection
    HAS_GSHEETS = True
except ImportError:
    try:
        from st_gsheets_connection import GSheetsConnection
        HAS_GSHEETS = True
    except ImportError:
        HAS_GSHEETS = False

def get_gsheets_connection():
    if HAS_GSHEETS:
        try:
            return st.connection("gsheets", type=GSheetsConnection)
        except Exception:
            return None
    return None

# Configuration de la page
st.set_page_config(
    page_title="Massilly - Audit 5S Mobile v14",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Données des zones et sponsors officiels de Massilly
ZONES_MASSILLY = {
    "Zone 1": {"label": "Zone 1 - Filmeuse et quais production", "sponsor": "Audrey Sordet"},
    "Zone 2": {"label": "Zone 2 - Bureaux expédition", "sponsor": "Anthony Duplessis"},
    "Zone 3": {"label": "Zone 3 - Quai chargement", "sponsor": "Jonathan Mele"},
    "Zone 4": {"label": "Zone 4 - Zone préparation commande", "sponsor": "Thomas Collin"},
    "Zone 5": {"label": "Zone 5 - Emplacements boîtes", "sponsor": "Gaspard Sommereux"},
    "Zone 6": {"label": "Zone 6 - Palettier", "sponsor": "Mariia Leliukh"},
    "Zone 7": {"label": "Zone 7 - Bureaux et zones réception MP", "sponsor": "Céline Hereng"},
    "Zone 8": {"label": "Zone 8 - Zone stockage métal", "sponsor": "Dimitri Dupasquier"},
    "Zone 9": {"label": "Zone 9 - Local joint", "sponsor": "Frédéric Bouvy"},
    "Zone 10": {"label": "Zone 10 - Stockage produits dangereux", "sponsor": "Nathalie Berthelin"}
}

# Les 15 critères d'audit officiels de Massilly
CRITERES_OFFICIELS = [
    # Sort (Trier)
    {
        "id": "c1",
        "cat": "1S - TRIER (Seiri)",
        "check_txt": "Les sols, les murs et les abords. Pas d'éléments inutiles, palettes cassées ou objets encombrants.",
        "txt": "Les éléments inutiles ont été supprimés de la zone (au sol, sur les murs, sur les abords).",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Vérifier qu'aucune palette cassée, film plastique usagé, cerclage ou déchet n'encombre le sol.<br>• Contrôler l'absence d'outils hors d'usage ou de matériel obsolète.<br>• Appliquer la règle des 3 mois : tout ce qui n'a pas servi depuis 3 mois doit être évacué."
    },
    {
        "id": "c2",
        "cat": "1S - TRIER (Seiri)",
        "check_txt": "Les servantes, tiroirs, établis et armoires. Vidés de tout matériel ou objet inutile.",
        "txt": "Les servantes/tiroirs/établis/armoires sont vidés des choses inutiles.",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Ouvrir les tiroirs des établis, armoires et servantes de la zone.<br>• S'assurer qu'aucun chiffon souillé, pièce usée ou vieux document ne s'y accumule.<br>• Ne garder que le strict nécessaire aux opérations quotidiennes."
    },
    {
        "id": "c3",
        "cat": "1S - TRIER (Seiri)",
        "check_txt": "Les allées de circulation. Libres et totalement dégagées de tout encombrement.",
        "txt": "Les allées de circulation sont dégagées.",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Parcourir les allées piétons et chariots de la zone.<br>• S'assurer que les allées restent libres à 100% sans aucun débordement de palette ou carton.<br>• Vérifier que les accès aux extincteurs et arrêts d'urgence sont dégagés."
    },
    # Straighten (Organiser, ranger)
    {
        "id": "c4",
        "cat": "2S - RANGER (Seiton)",
        "check_txt": "Tous les équipements et outils. Rangés et identifiés à leur emplacement (marquage au sol ou autre).",
        "txt": "Tous les équipements et outils utilisés dans la zone sont rangés et identifiés (marquage au sol ou autres).",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Contrôler que chaque chariot, bac, benne, outil ou transpalette possède son contour tracé au sol.<br>• Vérifier que le matériel est effectivement rangé à l'intérieur de son marquage tracé."
    },
    {
        "id": "c5",
        "cat": "2S - RANGER (Seiton)",
        "check_txt": "Les fournitures, consommables et moyens de nettoyage. Clairement identifiés et rangés.",
        "txt": "Les fournitures, les consommables et le moyen de nettoyage sont clairement identifiés et rangés.",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Vérifier la présence du panneau d'ombres (Shadow Board) pour le balai, la pelle et la balayette.<br>• S'assurer que chaque consommable (film étirable, étiquettes) a son emplacement identifié."
    },
    {
        "id": "c6",
        "cat": "2S - RANGER (Seiton)",
        "check_txt": "Les matières premières. Stockées correctement dans la zone dédiée avec identification.",
        "txt": "Les matières premières sont correctement stockées dans la zone.",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Inspecter les palettes de matières premières et consommables.<br>• Vérifier qu'elles sont rangées dans leur zone dédiée et portent la feuille d'identification bleue officielle si bloquées."
    },
    # Sweep (Nettoyer)
    {
        "id": "c7",
        "cat": "3S - NETTOYER (Seiso)",
        "check_txt": "Les sols, surfaces de travail et équipements. Propres, dépoussiérés et en bon état.",
        "txt": "Les sols, les surfaces de travail et les équipements sont propres.",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Vérifier l'état de propreté du sol de la zone et des surfaces des pupitres/établis.<br>• S'assurer de l'absence de traces de graisse, de poussière accumulée ou de rognures métalliques."
    },
    {
        "id": "c8",
        "cat": "3S - NETTOYER (Seiso)",
        "check_txt": "Les déchets de la zone. Collectés et recyclés correctement (cartons, plastiques...).",
        "txt": "Les déchets sont recyclés correctement (cartons, plastiques...).",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Vérifier la séparation sélective : bac cartons, bac plastiques, bac métaux.<br>• S'assurer que les poubelles de zone ne débordent pas."
    },
    {
        "id": "c9",
        "cat": "3S - NETTOYER (Seiso)",
        "check_txt": "L'environnement de travail global. Agréable (éclairages, marquage au sol, absence de poussières/graffitis).",
        "txt": "L'environnement de travail est agréable (éclairages, marquage au sol, poussières, graffitis).",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Vérifier le bon éclairage de la zone, l'état des marquages et la propreté générale.<br>• S'assurer que l'espace est sain et sans dégradation visuelle."
    },
    # Standardize (Standardiser)
    {
        "id": "c10",
        "cat": "4S - STANDARDISER (Seiketsu)",
        "check_txt": "Le code couleur de la zone. Clairement identifié et facilement compréhensible.",
        "txt": "La zone possède un code couleur et est facilement compréhensible.",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Vérifier le respect de la charte graphique des couleurs (allées, zones de stock, zones de danger).<br>• S'assurer que n'importe quel arrivant comprend immédiatement l'organisation visuelle de la zone."
    },
    {
        "id": "c11",
        "cat": "4S - STANDARDISER (Seiketsu)",
        "check_txt": "Les étiquettes au sol ou au mur. Parfaitement visibles et en bon état.",
        "txt": "Les étiquettes au sol ou au mur sont visibles et en bon état.",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Contrôler l'état des étiquettes d'emplacement, bandes au sol et marquages muraux.<br>• Remplacer toute étiquette détériorée, décollée ou illisible."
    },
    {
        "id": "c12",
        "cat": "4S - STANDARDISER (Seiketsu)",
        "check_txt": "L'attribution des emplacements. Évident visuellement que chaque chose est à sa place.",
        "txt": "Il est évident que chaque chose est à sa place (bennes, corbeilles, outils...).",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Vérifier visuellement si bennes, corbeilles, outils et chariots occupent leur place désignée.<br>• Déceler immédiatement tout objet hors emplacement standard."
    },
    # Sustain (Respecter)
    {
        "id": "c13",
        "cat": "5S - RESPECTER (Shitsuke)",
        "check_txt": "L'organisation générale. Bonne tenue globale sans aucun danger de sécurité.",
        "txt": "La zone a une bonne organisation générale et ne présente aucun danger sécurité.",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Vérifier qu'aucun risque de chute, de collision ou de blessure n'existe dans la zone.<br>• S'assurer du respect permanent des règles de sécurité et de rangement."
    },
    {
        "id": "c14",
        "cat": "5S - RESPECTER (Shitsuke)",
        "check_txt": "La documentation et consignes de zone. À jour (pas de notes manuscrites ou obsolètes).",
        "txt": "Les documents/instructions/informations sont à jour (pas de notes obsolètes, manuscrites...).",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Vérifier le panneau d'affichage 5S de la zone.<br>• Éliminer tout affichage sauvage, feuille volante manuscrite ou consigne périmée."
    },
    {
        "id": "c15",
        "cat": "5S - RESPECTER (Shitsuke)",
        "check_txt": "Le standard de zone. Conforme, à jour et approprié aux réalités du terrain.",
        "txt": "Le standard de la zone est conforme et approprié.",
        "expl": "💡 <b>Que vérifier sur le terrain ?</b><br>• Contrôler si le référentiel visuel 'Standard 5S' reflète exactement l'état de la zone.<br>• Valider l'application rigoureuse du standard par l'ensemble de l'équipe."
    }
]


# Initialisation robuste de la session
st.session_state.setdefault("user_authenticated", False)
st.session_state.setdefault("user_role", "")
st.session_state.setdefault("user_name", "")
st.session_state.setdefault("user_zone", "")
st.session_state.setdefault("audit_started", False)
st.session_state.setdefault("current_q_idx", 0)
st.session_state.setdefault("answers", {})
st.session_state.setdefault("test_mode", False)
st.session_state.setdefault("portal_shown", False)
st.session_state.setdefault("auth_step", 0)
st.session_state.setdefault("audit_saved", False)

# Définition dynamique des fichiers de données selon le mode (Réel vs Test)
if st.session_state.get("test_mode", False):
    SHARED_DATA_FILE = "test_suivi_audits_5s.csv"
    SHARED_LOG_FILE = "test_journal_activite_5s.json"
else:
    SHARED_DATA_FILE = "suivi_audits_5s.csv"
    SHARED_LOG_FILE = "journal_activite_5s.json"

# Création automatique des fichiers s'ils n'existent pas
if not os.path.exists(SHARED_DATA_FILE):
    colonnes_init = [
        "Date", "Zone", "Sponsor", "Auditeur", "Role",
        "c1", "c1_comment", "c2", "c2_comment", "c3", "c3_comment",
        "c4", "c4_comment", "c5", "c5_comment", "c6", "c6_comment",
        "c7", "c7_comment", "c8", "c8_comment", "c9", "c9_comment",
        "c10", "c10_comment", "c11", "c11_comment", "c12", "c12_comment",
        "c13", "c13_comment", "c14", "c14_comment", "c15", "c15_comment",
        "Score_Total", "Pourcentage", "Observations", "Actions_Correctives"
    ]
    pd.DataFrame(columns=colonnes_init).to_csv(SHARED_DATA_FILE, index=False, encoding='utf-8')

if not os.path.exists(SHARED_LOG_FILE):
    with open(SHARED_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False)

def charger_audits():
    conn = get_gsheets_connection()
    if conn is not None:
        try:
            df = conn.read(ttl=0)
            if df is not None and not df.empty:
                df = df.dropna(how="all")
                return df
        except Exception:
            pass

    try:
        return pd.read_csv(SHARED_DATA_FILE, encoding='utf-8')
    except Exception:
        return pd.DataFrame()


def log_click_event(action, details=""):
    """Enregistre un clic utilisateur avec horodatage milliseconde."""
    timestamp = get_paris_now_str(with_ms=True)
    user = st.session_state.get("user_name", "ANONYME")
    role = st.session_state.get("user_role", "INCONNU")
    zone = st.session_state.get("user_zone", "NON_DEFINIE")
    
    event = {
        "timestamp": timestamp,
        "user": user,
        "role": role,
        "zone": zone,
        "action": action,
        "details": details
    }
    
    if "user_click_history" not in st.session_state:
        st.session_state["user_click_history"] = []
    st.session_state["user_click_history"].append(event)
    
    # Écriture dans le fichier CSV du journal de clics
    click_log_file = "test_journal_clics_5s.csv" if st.session_state.get("test_mode", False) else "journal_clics_5s.csv"
    file_exists = os.path.exists(click_log_file)
    try:
        with open(click_log_file, "a", encoding="utf-8") as f:
            if not file_exists:
                f.write("Timestamp;User;Role;Zone;Action;Details\n")
            f.write(f"{timestamp};{user};{role};{zone};{action};{details}\n")
    except Exception as e:
        pass


def trigger_vote_fx(step_num, vote_type="OUI"):
    """Joue le son de confirmation OUI (identique pour tous) et affiche la notification visuelle personnalisée (Smiley + Couleurs) selon le vote."""
    vote_upper = str(vote_type).upper()
    
    if "NON" in vote_upper:
        icon = "😞"
        label = f"⚠️ ÉTAPE {step_num} : NON-CONFORME (NON) 😞"
        border_color = "#EF4444"
        bg_gradient = "linear-gradient(135deg, rgba(225, 29, 72, 0.95), rgba(15, 23, 42, 0.95))"
    elif "PARTIEL" in vote_upper or "N/A" in vote_upper:
        icon = "🤔"
        label = f"❓ ÉTAPE {step_num} : PARTIEL / RÉSERVE 🤔"
        border_color = "#F59E0B"
        bg_gradient = "linear-gradient(135deg, rgba(245, 158, 11, 0.95), rgba(15, 23, 42, 0.95))"
    else:  # OUI
        icon = "😊"
        label = f"✨ ÉTAPE {step_num} : CONFORME (OUI) 😊"
        border_color = "#10B981"
        bg_gradient = "linear-gradient(135deg, rgba(16, 185, 129, 0.95), rgba(15, 23, 42, 0.95))"

    # Son de confirmation OUI identique pour OUI, NON et PARTIEL (Accord Do-Mi-Sol)
    js_audio = """
        var pWin = window.parent || window;
        if (!pWin.globalAudioCtx || pWin.globalAudioCtx.state === 'closed') {
            pWin.globalAudioCtx = new (pWin.AudioContext || pWin.webkitAudioContext)();
        }
        var ctx = pWin.globalAudioCtx;
        if (ctx.state === 'suspended') { ctx.resume(); }
        var notes = [523.25, 659.25, 783.99];
        var now = ctx.currentTime;
        notes.forEach(function(freq, i){
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, now + i * 0.08);
            gain.gain.setValueAtTime(0.25, now + i * 0.08);
            gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.08 + 0.25);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now + i * 0.08);
            osc.stop(now + i * 0.08 + 0.25);
        });
    """

    js_code = f"""<script>
    (function(){{
        try {{
            {js_audio}
        }} catch(e) {{}}
    }})();
    </script>"""
    components.html(js_code, height=1, width=1)
    
    overlay_html = f"""<div class='step-flash-overlay' style='background: {bg_gradient} !important; border-color: {border_color} !important;'>
        <div class='falling-box-anim'>{icon}</div>
        <div class='step-valid-badge' style='color: #FFFFFF !important;'>{label}</div>
    </div>"""
    st.markdown(overlay_html, unsafe_allow_html=True)

def trigger_step_validation_fx(step_num, vote_type="OUI"):
    """Joue un son distinct et affiche une animation visuelle selon le vote."""
    trigger_vote_fx(step_num, vote_type)

def trigger_final_save_fx():
    """Joue une fanfare festive et déclenche une pluie de boîtes métalliques et feux d'artifice."""
    js_code = """<script>
    (function(){
        try {
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            var notes = [523.25, 659.25, 783.99, 1046.50];
            notes.forEach(function(freq, i){
                var osc = ctx.createOscillator();
                var gain = ctx.createGain();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(freq, ctx.currentTime + i * 0.12);
                gain.gain.setValueAtTime(0.25, ctx.currentTime + i * 0.12);
                gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + i * 0.12 + 0.35);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(ctx.currentTime + i * 0.12);
                osc.stop(ctx.currentTime + i * 0.12 + 0.35);
            });
        } catch(e) {}
    })();
    </script>"""
    components.html(js_code, height=0, width=0)
    
    overlay_html = """<div class='final-save-overlay'>
        <div class='final-save-box'>📦 🎁 🏆 ⚡ 🌟</div>
        <div class='final-save-title'>🎉 AUDIT 5S ENREGISTRÉ AVEC SUCCÈS !</div>
        <div class='final-save-sub'>Données & Horodatage mémorisés dans Google Sheets & CSV</div>
    </div>"""
    st.markdown(overlay_html, unsafe_allow_html=True)
    st.balloons()


def sauvegarder_audit_local(data_dict):
    gsheets_ok = False
    err_details = ""
    conn = get_gsheets_connection()
    if conn is not None:
        try:
            try:
                existing_df = conn.read(ttl=0)
                if existing_df is None or existing_df.empty:
                    existing_df = pd.DataFrame()
                else:
                    existing_df = existing_df.dropna(how="all")
            except Exception:
                existing_df = pd.DataFrame()
                
            new_row = pd.DataFrame([data_dict])
            if not existing_df.empty:
                updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            else:
                updated_df = new_row
                
            conn.update(data=updated_df)
            gsheets_ok = True
        except Exception as e:
            err_details = str(e)

    # Backup local CSV
    try:
        df = pd.read_csv(SHARED_DATA_FILE, encoding='utf-8')
    except Exception:
        df = pd.DataFrame()

    new_row = pd.DataFrame([data_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(SHARED_DATA_FILE, index=False, encoding='utf-8')

    # Journal JSON
    log_entry = {
        "timestamp": get_paris_now_str(),
        "type": "TEST - Diagnostic" if st.session_state.get("test_mode", False) else "Diagnostic Réel",
        "details": f"Zone {data_dict.get('Zone', '')} par {data_dict.get('Auditeur', '')} ({data_dict.get('Score_Total', 0)}/15 - {data_dict.get('Pourcentage', 0)}%)",
        "gsheets": "OK" if gsheets_ok else f"OFFLINE ({err_details})"
    }
    try:
        with open(SHARED_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except Exception:
        logs = []
    logs.append(log_entry)
    with open(SHARED_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)

    return gsheets_ok, err_details


# ========================================== STYLE CSS : DESIGN 3D PURE ET SÉCURISÉ
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;600;700;800&family=Playfair+Display:ital,wght=0,600;0,800;1,600&display=swap');

    .stApp {
        background: linear-gradient(-45deg, #0A1128, #101F42, #071126, #001F3D) !important;
        background-size: 400% 400% !important;
        animation: gradientBG 20s ease infinite !important;
        color: #F8FAFC !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp label, .stApp p, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #F8FAFC !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    .question-card, .question-card p, .question-card span, .question-card li, .question-card div, .question-card h4, .question-text {
        color: #0F172A !important;
    }

    .main-header-3d {
        font-family: 'Playfair Display', serif !important;
        font-weight: 900 !important;
        font-size: 3.3rem !important;
        text-align: center !important;
        text-transform: uppercase;
        margin-top: -10px;
        margin-bottom: 5px;
        background: linear-gradient(135deg, #FFFFFF 20%, #38BDF8 60%, #0E529E 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-shadow: 
            0 1px 0 #E2E8F0,
            0 2px 0 #CBD5E1,
            0 3px 0 #94A3B8,
            0 4px 0 #64748B,
            0 5px 0 #475569,
            0 6px 0 #334155,
            0 7px 0 #1E293B,
            0 12px 18px rgba(0,0,0,0.6) !important;
        animation: floatHeader 3.8s ease-in-out infinite alternate !important;
        transform: perspective(800px) rotateX(15deg);
    }
    
    @keyframes floatHeader {
        0% { transform: perspective(800px) rotateX(15deg) translateY(0px); }
        100% { transform: perspective(800px) rotateX(15deg) translateY(-10px); }
    }

    .user-id-badge-3d {
        background: linear-gradient(135deg, #1E293B, #0B1329) !important;
        border: 3px solid #38BDF8 !important;
        border-radius: 20px !important;
        color: #FFFFFF !important;
        text-align: center;
        padding: 20px 40px !important;
        font-size: 1.7rem !important;
        font-weight: 900 !important;
        letter-spacing: 5px;
        margin: 20px auto 30px auto !important;
        max-width: 820px;
        box-shadow: 0 15px 35px rgba(56, 189, 248, 0.4) !important;
    }

    /* --- CARTE BOÎTE DÉCORÉE MASSILLY 1911 (ACCEUIL 3D PRESTIGE) --- */
    .massilly-box-card-3d {
        background: linear-gradient(135deg, #0A1E3F 0%, #0E529E 60%, #062850 100%) !important;
        border: 4px solid #F59E0B !important; /* Dorure Or Massilly */
        border-radius: 24px !important;
        padding: 40px 25px !important;
        text-align: center !important;
        margin: 25px auto !important;
        max-width: 650px !important;
        box-shadow: 
            0 20px 50px rgba(0, 0, 0, 0.8),
            0 0 30px rgba(245, 158, 11, 0.4) !important;
        transform: perspective(800px) rotateX(5deg);
        animation: boxFloat 3.5s ease-in-out infinite alternate !important;
    }

    @keyframes boxFloat {
        0% { transform: perspective(800px) rotateX(5deg) translateY(0px); }
        100% { transform: perspective(800px) rotateX(5deg) translateY(-12px); }
    }

    /* --- SELECTBOX XXL TACTILE SPÉCIALE SMARTPHONE --- */
    div[data-testid="stSelectbox"] > div {
        background: linear-gradient(135deg, #1E293B, #0F172A) !important;
        border: 3px solid #38BDF8 !important;
        border-radius: 18px !important;
        min-height: 82px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important;
        display: flex !important;
        align-items: center !important;
    }

    div[data-testid="stSelectbox"] div[role="combobox"] {
        font-size: 24px !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        padding-left: 20px !important;
    }

    div[data-testid="stSelectbox"] label {
        font-size: 30px !important; height: 95px !important;
        font-weight: 900 !important;
        color: #38BDF8 !important;
        letter-spacing: 1.5px !important;
        margin-bottom: 12px !important;
        text-transform: uppercase !important;
    }

    /* --- TOUS LES BOUTONS PRESTIGE 3D --- */
    .stButton > button, div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #0E529E 0%, #38BDF8 50%, #0E529E 100%) !important;
        background-size: 200% auto !important;
        color: #FFFFFF !important;
        height: 85px !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        border-radius: 20px !important;
        border: none !important;
        border-bottom: 8px solid #063970 !important;
        box-shadow: 0 15px 30px rgba(14, 82, 158, 0.45) !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.6) !important;
        cursor: pointer !important;
        letter-spacing: 2px !important;
    }

    /* Boutons de vote (OUI / NON / N/A) */
    div[data-testid="stHorizontalBlock"] button {
        width: 100% !important;
        height: 115px !important;
        font-size: 28px !important;
        font-weight: 900 !important;
        border-radius: 22px !important;
        color: #FFFFFF !important;
        border: none !important;
    }

    

    

    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {
        background: linear-gradient(135deg, #3B82F6, #1D4ED8) !important;
        border-bottom: 8px solid #1E40AF !important;
    }

    .back-btn-container + .stButton button, .back-btn-container button {
        background: rgba(30, 41, 59, 0.8) !important;
        color: #94A3B8 !important;
        border: 2px solid #475569 !important;
        height: 60px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
    }

    .small-btn-container + .stButton button, .small-btn-container button {
        height: 50px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        background: #1E293B !important;
    }

    /* ========================================== EXPLOSION DE PARTICULES 3D PLEIN ÉCRAN ========================================== */
    .explosion-overlay {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 999999 !important;
        background: rgba(10, 17, 40, 0.92) !important;
        backdrop-filter: blur(12px) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }

    .explosion-core-flash {
        position: absolute;
        width: 150px;
        height: 150px;
        background: radial-gradient(circle, #FFFFFF 0%, #38BDF8 50%, rgba(56,189,248,0) 100%);
        border-radius: 50%;
        animation: coreFlash 1.1s ease-out forwards;
    }

    @keyframes coreFlash {
        0% { transform: scale(0.1); opacity: 1; filter: drop-shadow(0 0 50px #38BDF8); }
        50% { transform: scale(8); opacity: 0.9; filter: drop-shadow(0 0 120px #FFFFFF); }
        100% { transform: scale(25); opacity: 0; }
    }

    .particle-3d {
        position: absolute;
        font-size: 2.8rem;
        user-select: none;
        animation: burstOut 1.1s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
    }

    @keyframes burstOut {
        0% {
            transform: translate(0, 0) scale(0.2) rotate(0deg);
            opacity: 1;
            filter: drop-shadow(0 0 10px #38BDF8);
        }
        70% {
            opacity: 1;
            filter: drop-shadow(0 0 25px #F59E0B);
        }
        100% {
            transform: translate(var(--tx), var(--ty)) scale(2.2) rotate(var(--rot));
            opacity: 0;
            filter: drop-shadow(0 0 40px rgba(255,255,255,0));
        }
    }

    /* --- LOGO 5S FLOTTANT 3D HAUTE DÉFINITION (ACCUEIL) --- */
    .logo-5s-3d-floating {
        background: linear-gradient(135deg, rgba(14, 82, 158, 0.35), rgba(15, 23, 42, 0.9)) !important;
        border: 3px solid #38BDF8 !important;
        border-radius: 26px !important;
        padding: 30px 15px !important;
        text-align: center !important;
        margin: 20px auto !important;
        max-width: 90vw !important;
        width: 100% !important;
        box-shadow: 
            0 20px 50px rgba(56, 189, 248, 0.35),
            inset 0 0 30px rgba(56, 189, 248, 0.25) !important;
        transform: perspective(900px) rotateX(8deg);
        animation: floatLogo5S 3.5s ease-in-out infinite alternate !important;
    }

    @keyframes floatLogo5S {
        0% { transform: perspective(900px) rotateX(8deg) translateY(0px) scale(0.99); }
        100% { transform: perspective(900px) rotateX(8deg) translateY(-12px) scale(1.02); }
    }

    .logo-5s-3d-text {
        font-family: 'Playfair Display', serif !important;
        font-size: clamp(1.6rem, 6.5vw, 3.2rem) !important;
        font-weight: 900 !important;
        text-align: center !important;
        display: block !important;
        width: 100% !important;
        margin: 0 auto !important;
        padding: 0 !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #38BDF8 50%, #0E529E 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-shadow: 0 10px 25px rgba(56, 189, 248, 0.5) !important;
        letter-spacing: 2px !important;
        white-space: normal !important;
        word-break: keep-all !important;
        line-height: 1.25 !important;
    }

    /* --- CARTE BLEU (GARÇONS) ET CARTE ROSE (FILLES) --- */
    
    

    .logo-5s-3d-floating {
        background: linear-gradient(135deg, rgba(14, 82, 158, 0.35), rgba(15, 23, 42, 0.9)) !important;
        border: 3px solid #38BDF8 !important;
        border-radius: 26px !important;
        padding: 30px 15px !important;
        text-align: center !important;
        margin: 20px auto !important;
        max-width: 95vw !important;
        width: 100% !important;
        box-shadow: 0 20px 50px rgba(56, 189, 248, 0.35), inset 0 0 30px rgba(56, 189, 248, 0.25) !important;
    }

    .logo-5s-3d-text {
        font-family: 'Playfair Display', serif !important;
        font-size: clamp(1.4rem, 6vw, 3rem) !important;
        font-weight: 900 !important;
        text-align: center !important;
        margin: 0 auto !important;
        display: block !important;
        width: 100% !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #38BDF8 50%, #0E529E 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-shadow: 0 10px 25px rgba(56, 189, 248, 0.5) !important;
        letter-spacing: 2px !important;
    }

    /* --- SPECIFICITÉ ÉLEVÉE : BLEU PUR POUR LES GARÇONS / ROSE MAGENTA PUR POUR LES FILLES --- */
    div.boy-card .stButton > button,
    div
    div.boy-card .stButton > button:hover,
    div

    div.girl-card .stButton > button,
    div
    div.girl-card .stButton > button:hover,
    div

    /* --- SPECTRE DE DÉGRADÉ CONTINU DE LA ZONE 1 À LA ZONE 10 (HAUTE SPÉCIFICITÉ) --- */
    div.z-color-0 .stButton > button, div
    div.z-color-1 .stButton > button, div
    div.z-color-2 .stButton > button, div
    div.z-color-3 .stButton > button, div
    div.z-color-4 .stButton > button, div
    div.z-color-5 .stButton > button, div
    div.z-color-6 .stButton > button, div
    div.z-color-7 .stButton > button, div
    div.z-color-8 .stButton > button, div
    div.z-color-9 .stButton > button, div

    .zone-badge-wrap .stButton > button, .zone-badge-wrap button {
        height: 75px !important;
        font-size: 30px !important; height: 95px !important;
        font-weight: 900 !important;
        border-radius: 20px !important;
        color: #FFFFFF !important;
        border-bottom: 6px solid rgba(0,0,0,0.4) !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
    }
    .zone-badge-wrap .stButton > button:hover, .zone-badge-wrap button:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 0 15px 35px rgba(255, 255, 255, 0.3) !important;
    }


    /* --- BOUTONS UTILISATEURS GARÇONS (BLEU OCÉAN / CYAN) --- */
    button[aria-label*="Damien"], div[data-testid="stButton"] button[aria-label*="Damien"],
button[aria-label*="Anthony"], div[data-testid="stButton"] button[aria-label*="Anthony"],
button[aria-label*="Jonathan"], div[data-testid="stButton"] button[aria-label*="Jonathan"],
button[aria-label*="Thomas"], div[data-testid="stButton"] button[aria-label*="Thomas"],
button[aria-label*="Gaspard"], div[data-testid="stButton"] button[aria-label*="Gaspard"],
button[aria-label*="Dimitri"], div[data-testid="stButton"] button[aria-label*="Dimitri"],
button[aria-label*="Frédéric"], div[data-testid="stButton"] button[aria-label*="Frédéric"] {
        background: linear-gradient(135deg, #0284C7 0%, #1E3A8A 100%) !important;
        border: 3px solid #38BDF8 !important;
        border-bottom: 7px solid #0369A1 !important;
        color: #FFFFFF !important;
        font-size: 30px !important; height: 95px !important;
        font-weight: 900 !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.45) !important;
    }

    /* --- BOUTONS UTILISATEURS FILLES (ROSE MAGENTA / PINK) --- */
    button[aria-label*="Audrey"], div[data-testid="stButton"] button[aria-label*="Audrey"],
button[aria-label*="Mariia"], div[data-testid="stButton"] button[aria-label*="Mariia"],
button[aria-label*="Céline"], div[data-testid="stButton"] button[aria-label*="Céline"],
button[aria-label*="Nathalie"], div[data-testid="stButton"] button[aria-label*="Nathalie"] {
        background: linear-gradient(135deg, #9D174D 0%, #DB2777 50%, #F472B6 100%) !important;
        border: 3px solid #F472B6 !important;
        border-bottom: 7px solid #831843 !important;
        color: #FFFFFF !important;
        font-size: 30px !important; height: 95px !important;
        font-weight: 900 !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 25px rgba(219, 39, 119, 0.45) !important;
    }

    /* --- DEGRADES DES ZONES LOGISTIQUES 1 A 10 --- */
    
button[aria-label*="Zone 1"], div[data-testid="stButton"] button[aria-label*="Zone 1"] {
    background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
    border: 3px solid #38BDF8 !important;
    border-bottom: 7px solid #0369A1 !important;
    color: #FFFFFF !important;
    font-size: 30px !important; height: 95px !important;
    font-weight: 900 !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
}

button[aria-label*="Zone 2"], div[data-testid="stButton"] button[aria-label*="Zone 2"] {
    background: linear-gradient(135deg, #0284C7 0%, #0D9488 100%) !important;
    border: 3px solid #2DD4BF !important;
    border-bottom: 7px solid #0D9488 !important;
    color: #FFFFFF !important;
    font-size: 30px !important; height: 95px !important;
    font-weight: 900 !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
}

button[aria-label*="Zone 3"], div[data-testid="stButton"] button[aria-label*="Zone 3"] {
    background: linear-gradient(135deg, #0D9488 0%, #059669 100%) !important;
    border: 3px solid #34D399 !important;
    border-bottom: 7px solid #059669 !important;
    color: #FFFFFF !important;
    font-size: 30px !important; height: 95px !important;
    font-weight: 900 !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
}

button[aria-label*="Zone 4"], div[data-testid="stButton"] button[aria-label*="Zone 4"] {
    background: linear-gradient(135deg, #059669 0%, #16A34A 100%) !important;
    border: 3px solid #4ADE80 !important;
    border-bottom: 7px solid #16A34A !important;
    color: #FFFFFF !important;
    font-size: 30px !important; height: 95px !important;
    font-weight: 900 !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
}

button[aria-label*="Zone 5"], div[data-testid="stButton"] button[aria-label*="Zone 5"] {
    background: linear-gradient(135deg, #16A34A 0%, #CA8A04 100%) !important;
    border: 3px solid #FACC15 !important;
    border-bottom: 7px solid #CA8A04 !important;
    color: #FFFFFF !important;
    font-size: 30px !important; height: 95px !important;
    font-weight: 900 !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
}

button[aria-label*="Zone 6"], div[data-testid="stButton"] button[aria-label*="Zone 6"] {
    background: linear-gradient(135deg, #CA8A04 0%, #EA580C 100%) !important;
    border: 3px solid #FB923C !important;
    border-bottom: 7px solid #EA580C !important;
    color: #FFFFFF !important;
    font-size: 30px !important; height: 95px !important;
    font-weight: 900 !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
}

button[aria-label*="Zone 7"], div[data-testid="stButton"] button[aria-label*="Zone 7"] {
    background: linear-gradient(135deg, #EA580C 0%, #E11D48 100%) !important;
    border: 3px solid #FB7185 !important;
    border-bottom: 7px solid #E11D48 !important;
    color: #FFFFFF !important;
    font-size: 30px !important; height: 95px !important;
    font-weight: 900 !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
}

button[aria-label*="Zone 8"], div[data-testid="stButton"] button[aria-label*="Zone 8"] {
    background: linear-gradient(135deg, #E11D48 0%, #C026D3 100%) !important;
    border: 3px solid #E879F9 !important;
    border-bottom: 7px solid #C026D3 !important;
    color: #FFFFFF !important;
    font-size: 30px !important; height: 95px !important;
    font-weight: 900 !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
}

button[aria-label*="Zone 9"], div[data-testid="stButton"] button[aria-label*="Zone 9"] {
    background: linear-gradient(135deg, #C026D3 0%, #9333EA 100%) !important;
    border: 3px solid #C084FC !important;
    border-bottom: 7px solid #9333EA !important;
    color: #FFFFFF !important;
    font-size: 30px !important; height: 95px !important;
    font-weight: 900 !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
}

button[aria-label*="Zone 10"], div[data-testid="stButton"] button[aria-label*="Zone 10"] {
    background: linear-gradient(135deg, #9333EA 0%, #4C1D95 100%) !important;
    border: 3px solid #A855F7 !important;
    border-bottom: 7px solid #4C1D95 !important;
    color: #FFFFFF !important;
    font-size: 30px !important; height: 95px !important;
    font-weight: 900 !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
}



    /* ========================================== MARKEUR DÉDIÉ COULEURS BOYS / GIRLS / ZONES ========================================== */
    /* GARÇONS : BLEU OCÉAN & CYAN NÉON IMPÉRIAL */
    div:has(.boy-marker) + div button,
    div:has(.boy-marker) + div div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #0284C7 0%, #1E3A8A 100%) !important;
        border: 3px solid #38BDF8 !important;
        border-bottom: 7px solid #0369A1 !important;
        color: #FFFFFF !important;
        font-size: 30px !important; height: 95px !important;
        font-weight: 900 !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 25px rgba(2, 132, 199, 0.5) !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.6) !important;
    }
    div:has(.boy-marker) + div button:hover,
    div:has(.boy-marker) + div div[data-testid="stButton"] button:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 0 15px 35px rgba(56, 189, 248, 0.8) !important;
        border-color: #7DD3FC !important;
    }

    /* FILLES : ROSE MAGENTA FLUO & FUCHSIA PRESTIGE */
    div:has(.girl-marker) + div button,
    div:has(.girl-marker) + div div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #BE185D 0%, #DB2777 50%, #F472B6 100%) !important;
        border: 3px solid #F472B6 !important;
        border-bottom: 7px solid #9D174D !important;
        color: #FFFFFF !important;
        font-size: 30px !important; height: 95px !important;
        font-weight: 900 !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 25px rgba(219, 39, 119, 0.5) !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.6) !important;
    }
    div:has(.girl-marker) + div button:hover,
    div:has(.girl-marker) + div div[data-testid="stButton"] button:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 0 15px 35px rgba(244, 114, 182, 0.8) !important;
        border-color: #FBCFE8 !important;
    }

    /* ZONES 1 À 10 : SPECTRE DE DÉGRADÉ CONTINU */
    div:has(.zone-marker-0) + div button { background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important; border: 3px solid #38BDF8 !important; border-bottom: 7px solid #075985 !important; }
    div:has(.zone-marker-1) + div button { background: linear-gradient(135deg, #0284C7 0%, #0D9488 100%) !important; border: 3px solid #2DD4BF !important; border-bottom: 7px solid #0F766E !important; }
    div:has(.zone-marker-2) + div button { background: linear-gradient(135deg, #0D9488 0%, #059669 100%) !important; border: 3px solid #34D399 !important; border-bottom: 7px solid #047857 !important; }
    div:has(.zone-marker-3) + div button { background: linear-gradient(135deg, #059669 0%, #16A34A 100%) !important; border: 3px solid #4ADE80 !important; border-bottom: 7px solid #15803D !important; }
    div:has(.zone-marker-4) + div button { background: linear-gradient(135deg, #16A34A 0%, #CA8A04 100%) !important; border: 3px solid #FACC15 !important; border-bottom: 7px solid #A16207 !important; }
    div:has(.zone-marker-5) + div button { background: linear-gradient(135deg, #CA8A04 0%, #EA580C 100%) !important; border: 3px solid #FB923C !important; border-bottom: 7px solid #C2410C !important; }
    div:has(.zone-marker-6) + div button { background: linear-gradient(135deg, #EA580C 0%, #E11D48 100%) !important; border: 3px solid #FB7185 !important; border-bottom: 7px solid #BE123C !important; }
    div:has(.zone-marker-7) + div button { background: linear-gradient(135deg, #E11D48 0%, #C026D3 100%) !important; border: 3px solid #E879F9 !important; border-bottom: 7px solid #A21CAF !important; }
    div:has(.zone-marker-8) + div button { background: linear-gradient(135deg, #C026D3 0%, #9333EA 100%) !important; border: 3px solid #C084FC !important; border-bottom: 7px solid #7E22CE !important; }
    div:has(.zone-marker-9) + div button { background: linear-gradient(135deg, #9333EA 0%, #4C1D95 100%) !important; border: 3px solid #A855F7 !important; border-bottom: 7px solid #3B0764 !important; }

    div[class*="zone-marker-"] + div button {
        height: 75px !important;
        font-size: 30px !important; height: 95px !important;
        font-weight: 900 !important;
        border-radius: 18px !important;
        color: #FFFFFF !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4) !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.6) !important;
    }


    /* --- BOUTONS D'AUDIT (OUI = VERT, NON = ROUGE, N/A = BLEU) --- */
    button[aria-label*="OUI"], div[data-testid="stButton"] button[aria-label*="OUI"] {
        background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important;
        border: 3px solid #34D399 !important;
        border-bottom: 8px solid #047857 !important;
        color: #FFFFFF !important;
        font-size: 28px !important;
        font-weight: 900 !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 25px rgba(16, 185, 129, 0.5) !important;
    }

    button[aria-label*="NON"], div[data-testid="stButton"] button[aria-label*="NON"] {
        background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%) !important;
        border: 3px solid #FCA5A5 !important;
        border-bottom: 8px solid #991B1B !important;
        color: #FFFFFF !important;
        font-size: 28px !important;
        font-weight: 900 !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 25px rgba(239, 68, 68, 0.5) !important;
    }

    button[aria-label*="N/A"], div[data-testid="stButton"] button[aria-label*="N/A"] {
        background: linear-gradient(135deg, #1D4ED8 0%, #3B82F6 100%) !important;
        border: 3px solid #93C5FD !important;
        border-bottom: 8px solid #1E40AF !important;
        color: #FFFFFF !important;
        font-size: 28px !important;
        font-weight: 900 !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.5) !important;
    }


    /* --- SÉLECTEURS DE PROTECTION HYBRIDES (ARIA-LABEL + HAS MARKER) --- */
    
    /* BOUTONS HOMMES (VRAI BLEU OCÉAN / CYAN NÉON) */
    div:has(.boy-marker) + div button,
    div:has(.boy-marker) + div div[data-testid="stButton"] button,
    button[aria-label*="Damien"], button[aria-label*="Anthony"], button[aria-label*="Jonathan"],
    button[aria-label*="Thomas"], button[aria-label*="Gaspard"], button[aria-label*="Dimitri"], button[aria-label*="Frédéric"] {
        background: linear-gradient(135deg, #0284C7 0%, #1E3A8A 100%) !important;
        border: 3px solid #38BDF8 !important;
        border-bottom: 8px solid #0369A1 !important;
        color: #FFFFFF !important;
        font-size: 32px !important;
        font-weight: 900 !important;
        height: 100px !important;
        border-radius: 20px !important;
        box-shadow: 0 12px 30px rgba(2, 132, 199, 0.6) !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.8) !important;
        letter-spacing: 1px !important;
    }
    
    /* BOUTONS FEMMES (VRAI ROSE MAGENTA / FUCHSIA) */
    div:has(.girl-marker) + div button,
    div:has(.girl-marker) + div div[data-testid="stButton"] button,
    button[aria-label*="Audrey"], button[aria-label*="Mariia"], button[aria-label*="Céline"], button[aria-label*="Nathalie"] {
        background: linear-gradient(135deg, #BE185D 0%, #DB2777 50%, #F472B6 100%) !important;
        border: 3px solid #F472B6 !important;
        border-bottom: 8px solid #9D174D !important;
        color: #FFFFFF !important;
        font-size: 32px !important;
        font-weight: 900 !important;
        height: 100px !important;
        border-radius: 20px !important;
        box-shadow: 0 12px 30px rgba(219, 39, 119, 0.6) !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.8) !important;
        letter-spacing: 1px !important;
    }

    /* SPECTRE DÉGRADÉ CONTINU ZONES 1 À 10 */
    div:has(.zone-marker-0) + div button, button[aria-label*="Zone 1"] { background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important; border: 3px solid #38BDF8 !important; border-bottom: 8px solid #075985 !important; font-size: 32px !important; font-weight: 900 !important; height: 100px !important; color: #FFF !important; }
    div:has(.zone-marker-1) + div button, button[aria-label*="Zone 2"] { background: linear-gradient(135deg, #0284C7 0%, #0D9488 100%) !important; border: 3px solid #2DD4BF !important; border-bottom: 8px solid #0F766E !important; font-size: 32px !important; font-weight: 900 !important; height: 100px !important; color: #FFF !important; }
    div:has(.zone-marker-2) + div button, button[aria-label*="Zone 3"] { background: linear-gradient(135deg, #0D9488 0%, #059669 100%) !important; border: 3px solid #34D399 !important; border-bottom: 8px solid #047857 !important; font-size: 32px !important; font-weight: 900 !important; height: 100px !important; color: #FFF !important; }
    div:has(.zone-marker-3) + div button, button[aria-label*="Zone 4"] { background: linear-gradient(135deg, #059669 0%, #16A34A 100%) !important; border: 3px solid #4ADE80 !important; border-bottom: 8px solid #15803D !important; font-size: 32px !important; font-weight: 900 !important; height: 100px !important; color: #FFF !important; }
    div:has(.zone-marker-4) + div button, button[aria-label*="Zone 5"] { background: linear-gradient(135deg, #16A34A 0%, #CA8A04 100%) !important; border: 3px solid #FACC15 !important; border-bottom: 8px solid #A16207 !important; font-size: 32px !important; font-weight: 900 !important; height: 100px !important; color: #FFF !important; }
    div:has(.zone-marker-5) + div button, button[aria-label*="Zone 6"] { background: linear-gradient(135deg, #CA8A04 0%, #EA580C 100%) !important; border: 3px solid #FB923C !important; border-bottom: 8px solid #C2410C !important; font-size: 32px !important; font-weight: 900 !important; height: 100px !important; color: #FFF !important; }
    div:has(.zone-marker-6) + div button, button[aria-label*="Zone 7"] { background: linear-gradient(135deg, #EA580C 0%, #E11D48 100%) !important; border: 3px solid #FB7185 !important; border-bottom: 8px solid #BE123C !important; font-size: 32px !important; font-weight: 900 !important; height: 100px !important; color: #FFF !important; }
    div:has(.zone-marker-7) + div button, button[aria-label*="Zone 8"] { background: linear-gradient(135deg, #E11D48 0%, #C026D3 100%) !important; border: 3px solid #E879F9 !important; border-bottom: 8px solid #A21CAF !important; font-size: 32px !important; font-weight: 900 !important; height: 100px !important; color: #FFF !important; }
    div:has(.zone-marker-8) + div button, button[aria-label*="Zone 9"] { background: linear-gradient(135deg, #C026D3 0%, #9333EA 100%) !important; border: 3px solid #C084FC !important; border-bottom: 8px solid #7E22CE !important; font-size: 32px !important; font-weight: 900 !important; height: 100px !important; color: #FFF !important; }
    div:has(.zone-marker-9) + div button, button[aria-label*="Zone 10"] { background: linear-gradient(135deg, #9333EA 0%, #4C1D95 100%) !important; border: 3px solid #A855F7 !important; border-bottom: 8px solid #581C87 !important; font-size: 32px !important; font-weight: 900 !important; height: 100px !important; color: #FFF !important; }

    /* BOUTONS VOTE AUDIT (🟢 OUI = VERT, 🔴 NON = ROUGE, 🔵 N/A = BLEU) */
    div:has(.vote-marker-oui) + div button, button[aria-label*="OUI"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        border: 3px solid #34D399 !important;
        border-bottom: 8px solid #047857 !important;
        color: #FFFFFF !important;
        font-size: 30px !important;
        font-weight: 900 !important;
        height: 90px !important;
    }
    div:has(.vote-marker-non) + div button, button[aria-label*="NON"] {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%) !important;
        border: 3px solid #FCA5A5 !important;
        border-bottom: 8px solid #B91C1C !important;
        color: #FFFFFF !important;
        font-size: 30px !important;
        font-weight: 900 !important;
        height: 90px !important;
    }
    div:has(.vote-marker-na) + div button, button[aria-label*="N/A"] {
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%) !important;
        border: 3px solid #93C5FD !important;
        border-bottom: 8px solid #1E40AF !important;
        color: #FFFFFF !important;
        font-size: 30px !important;
        font-weight: 900 !important;
        height: 90px !important;
    }


    /* --- STYLE CASE EXPLICATION DE L'ÉTAPE 5S --- */
    .question-expl-box {
        background: rgba(14, 116, 144, 0.25) !important;
        border-left: 5px solid #38BDF8 !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        margin-top: 12px !important;
        font-size: 1.05rem !important;
        color: #E2E8F0 !important;
        line-height: 1.5 !important;
    }

    /* --- STYLE BOUTON AJOUTER UN COMMENTAIRE --- */
    .add-comment-btn-wrap button {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%) !important;
        border: 2px dashed #38BDF8 !important;
        color: #38BDF8 !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        height: 60px !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        margin-top: 10px !important;
        margin-bottom: 10px !important;
    }
    .add-comment-btn-wrap button:hover {
        background: #334155 !important;
        color: #FFFFFF !important;
        border-color: #7DD3FC !important;
    }

    /* --- CSS NOTIFICATION VISUELLE ET SONORE (ÉCLAIR + BOÎTE 📦) --- */
    .step-vote-overlay {
        position: fixed !important;
        top: 20px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        z-index: 999999 !important;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.98)) !important;
        border-width: 3px !important;
        border-style: solid !important;
        border-radius: 22px !important;
        padding: 14px 28px !important;
        display: flex !important;
        align-items: center !important;
        gap: 16px !important;
        pointer-events: none !important;
        animation: flashPop 2.0s ease-out forwards !important;
    }

    .smiley-bounce-anim {
        font-size: 2.5rem !important;
        animation: smileyPop 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }

    @keyframes smileyPop {
        0% { transform: scale(0.2) rotate(-30deg); opacity: 0; }
        60% { transform: scale(1.3) rotate(10deg); opacity: 1; }
        100% { transform: scale(1.0) rotate(0deg); opacity: 1; }
    }

    .step-flash-overlay {
        position: fixed !important;
        top: 20px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        z-index: 999999 !important;
        background: linear-gradient(135deg, rgba(14, 82, 158, 0.95), rgba(15, 23, 42, 0.95)) !important;
        border: 3px solid #38BDF8 !important;
        box-shadow: 0 10px 40px rgba(56, 189, 248, 0.6), 0 0 20px rgba(255, 255, 255, 0.4) !important;
        border-radius: 20px !important;
        padding: 12px 25px !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        pointer-events: none !important;
        animation: flashPop 1.8s ease-out forwards !important;
    }

    @keyframes flashPop {
        0% { opacity: 0; transform: translate(-50%, -40px) scale(0.7); }
        15% { opacity: 1; transform: translate(-50%, 0px) scale(1.1); }
        30% { transform: translate(-50%, 0px) scale(1.0); }
        80% { opacity: 1; transform: translate(-50%, 0px) scale(1.0); }
        100% { opacity: 0; transform: translate(-50%, -30px) scale(0.9); }
    }

    .falling-box-anim {
        font-size: 2.2rem !important;
        animation: boxDrop 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }

    @keyframes boxDrop {
        0% { transform: translateY(-50px) rotate(-20deg); opacity: 0; }
        100% { transform: translateY(0) rotate(0deg); opacity: 1; }
    }

    .lightning-flash-anim {
        font-size: 2rem !important;
        animation: flashLightning 0.6s ease-in-out infinite alternate !important;
    }

    @keyframes flashLightning {
        0% { transform: scale(1); filter: drop-shadow(0 0 2px #FACC15); }
        100% { transform: scale(1.3); filter: drop-shadow(0 0 10px #FACC15); }
    }

    .step-valid-badge {
        font-size: 1.15rem !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
        letter-spacing: 2px !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.8) !important;
    }

    .final-save-overlay {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.98)) !important;
        border: 3px solid #F59E0B !important;
        box-shadow: 0 15px 50px rgba(245, 158, 11, 0.5) !important;
        border-radius: 22px !important;
        padding: 25px !important;
        text-align: center !important;
        margin-bottom: 25px !important;
        animation: finalPop 1s ease-out !important;
    }

    .final-save-box {
        font-size: 2.5rem !important;
        margin-bottom: 10px !important;
    }

    .final-save-title {
        font-size: 1.6rem !important;
        font-weight: 900 !important;
        color: #FACC15 !important;
        letter-spacing: 2px !important;
    }

    .final-save-sub {
        font-size: 1.1rem !important;
        color: #38BDF8 !important;
        font-weight: 700 !important;
        margin-top: 6px !important;
    }


    /* Force high contrast dark navy background with bright white text for all text areas and inputs */
    div[data-baseweb="textarea"], 
    div[data-baseweb="textarea"] textarea, 
    div[data-baseweb="input"], 
    div[data-baseweb="input"] input,
    textarea, 
    input {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border: 2px solid #38BDF8 !important;
        border-radius: 12px !important;
        caret-color: #38BDF8 !important;
    }

    div[data-baseweb="textarea"] textarea:focus, 
    div[data-baseweb="input"] input:focus,
    textarea:focus, 
    input:focus {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-color: #F59E0B !important;
        box-shadow: 0 0 15px rgba(245, 158, 11, 0.5) !important;
    }

    .stTextArea label, .stTextInput label {
        color: #38BDF8 !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
    }

</style>



""", unsafe_allow_html=True)

components.html("""<script>
(function() {
    if (!parent.window.globalAudioCtx) {
        parent.window.globalAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    function unlockAudio() {
        if (parent.window.globalAudioCtx && parent.window.globalAudioCtx.state === 'suspended') {
            parent.window.globalAudioCtx.resume();
        }
    }
    parent.window.addEventListener('click', unlockAudio, { once: true });
    parent.window.addEventListener('touchstart', unlockAudio, { once: true });
})();
</script>""", height=0, width=0)

# Affichage permanent du titre principal
# Top header removed per user request

if st.session_state.get("test_mode", False):
    st.markdown("<div class='test-badge'>🧪 SESSION DE TEST ACTIVE – ENREGISTREMENTS ISOLÉS</div>", unsafe_allow_html=True)


# ========================================== ÉCRAN DE CONNEXION MULTI-ÉTAPES (ETAPES 0 à 3)
# ========================================== ÉCRAN 0 : ACCUEIL ET LOGO 5S FLOTTANT AVEC EXPLOSION
if not st.session_state.get("user_authenticated", False):
    
    # ÉCRAN DE L'EXPLOSION LORS DU CLIC SUR ENTRER
    if st.session_state.get("show_explosion", False):
        import time
        import random
        
        # Génération dynamique de 45 particules explosives en 3D
        particles_html = "<div class='explosion-overlay'><div class='explosion-core-flash'></div>"
        symbols = ["✨", "💥", "🌟", "⚡", "⭐", "📦", "👑", "🎯", "🔥", "🚀", "💫", "🏆"]
        
        for i in range(48):
            sym = random.choice(symbols)
            angle = (i / 48.0) * 360.0
            dist = random.randint(280, 750)
            import math
            rad = math.radians(angle)
            tx = int(math.cos(rad) * dist)
            ty = int(math.sin(rad) * dist)
            rot = random.randint(-540, 540)
            particles_html += f"<div class='particle-3d' style='--tx: {tx}px; --ty: {ty}px; --rot: {rot}deg;'>{sym}</div>"
            
        particles_html += "</div>"
        st.markdown(particles_html, unsafe_allow_html=True)
        
        # Pause de 1.1s pour voir l'explosion éclater à l'écran
        time.sleep(1.1)
        st.session_state.show_explosion = False
        st.session_state.auth_step = 1
        st.rerun()

    auth_step = st.session_state.get("auth_step", 0)
    
    # ÉTAPE 0 : ACCUEIL AVEC LOGO 5S FLOTTANT 3D
    if auth_step == 0:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='user-id-badge-3d'>✨ BIENVENUE CHEZ MASSILLY ✨</div>", unsafe_allow_html=True)
        
        # Le Grand Logo 5S Flottant 3D
        st.markdown("""
        <div class='logo-5s-3d-floating'>
            <div class='logo-5s-3d-text'>✨ 5S LOGISTIQUE ✨</div>
            <div style='font-size: 1.45rem; font-weight: 800; color: #38BDF8; letter-spacing: 5px; text-transform: uppercase; margin-top: 15px;'>
                SEIRI • SEITON • SEISO • SEIKETSU • SHITSUKE
            </div>
            <div style='font-size: 1.1rem; color: #94A3B8; margin-top: 12px; font-weight: 600; letter-spacing: 1.5px;'>
                MÉTHODE D'EXCELLENCE OPÉRATIONNELLE MASSILLY
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
        if st.button("🚀 ENTRER DANS L'APPLICATION 5S", use_container_width=True):
            st.session_state.show_explosion = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    # ÉTAPE 1 : CHOIX DU RÔLE
    elif auth_step == 1:
        st.markdown("<div class='user-id-badge-3d'>📋 SÉLECTIONNEZ VOTRE RÔLE</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px; font-weight: bold;'>Choisissez votre profil d'accès :</p>", unsafe_allow_html=True)
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            if st.button("🎯 Sponsor de zone", use_container_width=True):
                st.session_state.user_role = "Sponsor de zone"
                st.session_state.auth_step = 2
                st.rerun()
        with col_r2:
            if st.button("🔍 Référent 5S", use_container_width=True):
                st.session_state.user_role = "Référent 5S"
                st.session_state.auth_step = 2
                st.rerun()
        with col_r3:
            if st.button("⚙️ Administrateur", use_container_width=True):
                st.session_state.user_role = "Éditeur (Méthodes / Alternant)"
                st.session_state.auth_step = 2
                st.rerun()
                
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
        if st.button("⬅️ Retour à l'accueil", use_container_width=True):
            st.session_state.auth_step = 0
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
                # ÉTAPE 2 : CHOIX DE L'UTILISATEUR (BLEU GARÇON / ROSE FILLE)
    elif auth_step == 2:
        st.markdown("<div class='user-id-badge-3d'>👤 SÉLECTION DE L'UTILISATEUR</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 18px; color: #CBD5E1; font-weight: 700;'>Cliquez sur votre prénom pour continuer :</p>", unsafe_allow_html=True)

        PERSONNES_BADGES = [
            {"prenom": "Damien", "full": "Damien Labbé", "icon": "⚡", "gender": "boy"},
            {"prenom": "Audrey", "full": "Audrey Sordet", "icon": "🎯", "gender": "girl"},
            {"prenom": "Anthony", "full": "Anthony Duplessis", "icon": "📦", "gender": "boy"},
            {"prenom": "Jonathan", "full": "Jonathan Mele", "icon": "🚚", "gender": "boy"},
            {"prenom": "Thomas", "full": "Thomas Collin", "icon": "📋", "gender": "boy"},
            {"prenom": "Gaspard", "full": "Gaspard Sommereux", "icon": "🥫", "gender": "boy"},
            {"prenom": "Mariia", "full": "Mariia Leliukh", "icon": "🏭", "gender": "girl"},
            {"prenom": "Céline", "full": "Céline Hereng", "icon": "📑", "gender": "girl"},
            {"prenom": "Dimitri", "full": "Dupasquier Dimitri", "icon": "⚙️", "gender": "boy"},
            {"prenom": "Frédéric", "full": "Frédéric Bouvy", "icon": "🔧", "gender": "boy"},
            {"prenom": "Nathalie", "full": "Nathalie Berthelin", "icon": "🛡️", "gender": "girl"}
        ]

        # Grille 2 colonnes tactile de badges
        col_p1, col_p2 = st.columns(2)
        for idx, p in enumerate(PERSONNES_BADGES):
            target_col = col_p1 if idx % 2 == 0 else col_p2
            marker_cls = "boy-marker" if p["gender"] == "boy" else "girl-marker"
            with target_col:
                st.markdown(f"<div class='{marker_cls}'></div>", unsafe_allow_html=True)
                lbl = f"{p['icon']}  {p['prenom']}"
                if st.button(lbl, key=f"p_badge_{idx}", use_container_width=True):
                    st.session_state.user_name = p['full']
                    st.session_state.auth_step = 3
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
        if st.button("⬅️ Retour au choix du rôle", use_container_width=True):
            st.session_state.auth_step = 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ÉTAPE 3 : SÉLECTION DE LA ZONE (AVEC DESCRIPTIONS DE ZONE COMPLÈTES)
    elif auth_step == 3:
        st.markdown("<div class='user-id-badge-3d'>📍 SÉLECTION DE LA ZONE LOGISTIQUE</div>", unsafe_allow_html=True)
        st.info(f"Profil actif : **{st.session_state.get('user_name', '')}** ({st.session_state.get('user_role', '')})")
        st.markdown("<p style='text-align: center; font-size: 18px; color: #CBD5E1; font-weight: 700;'>Consultez les descriptions et sélectionnez votre zone :</p>", unsafe_allow_html=True)

        ZONES_BADGES = [
            {"key": "Zone 1", "icon": "🎞️"},
            {"key": "Zone 2", "icon": "🖥️"},
            {"key": "Zone 3", "icon": "🚛"},
            {"key": "Zone 4", "icon": "📋"},
            {"key": "Zone 5", "icon": "🥫"},
            {"key": "Zone 6", "icon": "🏗️"},
            {"key": "Zone 7", "icon": "📦"},
            {"key": "Zone 8", "icon": "⚙️"},
            {"key": "Zone 9", "icon": "🧪"},
            {"key": "Zone 10", "icon": "☣️"}
        ]

        col_z1, col_z2 = st.columns(2)
        for idx, z in enumerate(ZONES_BADGES):
            target_col = col_z1 if idx % 2 == 0 else col_z2
            z_info = ZONES_MASSILLY.get(z["key"], {})
            z_label = z_info.get("label", z["key"])
            z_sponsor = z_info.get("sponsor", "")
            with target_col:
                st.markdown(f"<div class='zone-marker-{idx}'></div>", unsafe_allow_html=True)
                lbl = f"{z['icon']}  {z_label}"
                if st.button(lbl, key=f"z_badge_{idx}", use_container_width=True):
                    st.session_state.pending_zone = z["key"]
                    st.session_state.auth_step = 4 # Étape de confirmation!
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
        if st.button("⬅️ Retour à la sélection de l'utilisateur", use_container_width=True):
            st.session_state.auth_step = 2
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ÉTAPE 4 : CONFIRMATION AVANT LANCEMENT DU DIAGNOSTIC TERRAIN
    elif auth_step == 4:
        target_zone = st.session_state.get("pending_zone", "Zone 1")
        sponsor_name = ZONES_MASSILLY.get(target_zone, {}).get("sponsor", "Sponsor")
        zone_label = ZONES_MASSILLY.get(target_zone, {}).get("label", target_zone)

        st.markdown("<div class='user-id-badge-3d'>📋 CONFIRMATION DE L'AUDIT</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #1E293B, #0F172A); border: 3px solid #38BDF8; border-radius: 20px; padding: 25px; text-align: center; margin-bottom: 25px;'>
            <div style='font-size: 1.2rem; color: #38BDF8; font-weight: 800; letter-spacing: 3px; text-transform: uppercase;'>VISITE 5S PRÊTE</div>
            <div style='font-size: 2rem; font-weight: 900; color: #FFFFFF; margin-top: 10px;'>📍 {zone_label}</div>
            <div style='font-size: 1.1rem; color: #CBD5E1; margin-top: 8px;'>Auditeur : <b>{st.session_state.get('user_name', '')}</b> ({st.session_state.get('user_role', '')})</div>
            <div style='font-size: 1.1rem; color: #F59E0B; margin-top: 4px;'>Sponsor Responsable : <b>{sponsor_name}</b></div>
        </div>
        """, unsafe_allow_html=True)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
            if st.button("🚀 COMMENCER LE DIAGNOSTIC TERRAIN", use_container_width=True):
                st.session_state.user_zone = target_zone
                st.session_state.user_authenticated = True
                st.session_state.audit_started = True
                st.session_state.current_q_idx = 0
                st.session_state.answers = {}
                st.session_state.auth_step = 0
                st.session_state.portal_shown = False
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with col_c2:
            st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
            if st.button("⬅️ RETOUR AU MENU / CHANGER DE ZONE", use_container_width=True):
                st.session_state.auth_step = 3
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ========================================== APPLICATION PRINCIPALE (UTILISATEUR CONNECTÉ)
else:
    col_u1, col_u2 = st.columns([4, 1])
    with col_u1:
        st.markdown(
            f"👤 **{st.session_state.get('user_name', '')}** ({st.session_state.get('user_role', '')}) | Zone active : **{ZONES_MASSILLY[st.session_state.get('user_zone', 'Zone 1')]['label']}**"
        )
    with col_u2:
        st.markdown("<div class='small-btn-container'>", unsafe_allow_html=True)
        if st.button("🔄 Changer d'utilisateur", use_container_width=True):
            st.session_state.user_authenticated = False
            st.session_state.auth_step = 0
            st.session_state.audit_started = False
            st.session_state.current_q_idx = 0
            st.session_state.answers = {}
            st.session_state.portal_shown = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
            
    st.markdown("---")

    # Vérification du rôle Administrateur vs Utilisateur Terrain
    is_admin = (st.session_state.get('user_role', '') in ["Éditeur (Méthodes / Alternant)", "Administrateur"])

    if is_admin:
        onglets = ["📋 Saisie d'Audit terrain", "📊 Analyse & Historique (Admin)", "🗺️ Rappel des Standards"]
        menu_actif = st.radio("Menu de Commandement Administrateur :", onglets, horizontal=True, key="menu_actif")
        st.markdown("---")
    else:
        menu_actif = "📋 Saisie d'Audit terrain"

    # ========================================== SECTION : SAISIE D'AUDIT COMPORTEMENTAL (DIRECT TERRAIN)
    if menu_actif == "📋 Saisie d'Audit terrain":
        
        if not st.session_state.audit_started:
            st.markdown("<div class='btn-start-3d'>", unsafe_allow_html=True)
            btn_label = f"DÉMARRER UNE NOUVELLE VISITE 5S\n\n🚀 COMMENCER LE DIAGNOSTIC TECHNIQUE\n\n📍 Zone Active : {ZONES_MASSILLY[st.session_state.get('user_zone', 'Zone 1')]['label']}\nSponsor Responsable : {ZONES_MASSILLY[st.session_state.get('user_zone', 'Zone 1')]['sponsor']}"
            if st.button(btn_label, use_container_width=True):
                st.session_state.audit_started = True
                st.session_state.current_q_idx = 0
                st.session_state.answers = {}
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            idx = st.session_state.current_q_idx
            total_q = len(CRITERES_OFFICIELS)
            
            if idx < total_q:
                # Afficher la notification visuelle et sonore si une étape vient d'être validée
                last_valid = st.session_state.get("just_validated_step")
                last_vote = st.session_state.get("last_vote_type", "OUI")
                if last_valid:
                    trigger_vote_fx(last_valid, last_vote)
                    st.session_state["just_validated_step"] = None
                crit = CRITERES_OFFICIELS[idx]
                pct_prog = int(((idx + 1) / total_q) * 100)
                
                st.progress(pct_prog / 100.0)
                
                # 1. CARTE PRINCIPALE DE LA QUESTION AVEC DESCRIPTIONS COMPLETES (EN HAUT)
                check_body = crit.get('check_txt', crit['txt'])
                expl_html = f"<div class='question-expl-box'>{crit.get('expl', '')}</div>" if crit.get('expl') else ""
                
                st.markdown(f"""
                <div class='question-card-high-contrast'>
                    <div class='question-step-badge'>Étape {idx + 1} sur {total_q}</div>
                    <div class='question-cat-title'>{crit['cat']}</div>
                    <div class='question-check-header'>🔍 Je vérifie :</div>
                    <div class='question-check-body'>{check_body}</div>
                    {expl_html}
                    <div class='question-order-prompt'>👉 Est-ce que tout est en ordre ?</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 2. BOUTONS GÉANTS DE VOTE (AU MILIEU)
                c_v1, c_v2, c_v3 = st.columns(3)
                with c_v1:
                    st.markdown("<div class='vote-btn-oui'></div>", unsafe_allow_html=True)
                    if st.button("🟢 OUI", use_container_width=True, key=f"btn_oui_{idx}"):
                        st.session_state.answers[crit["id"]] = "OUI"
                        st.session_state[f"asking_why_{crit['id']}"] = False
                        st.session_state["just_validated_step"] = idx + 1
                        st.session_state["last_vote_type"] = "OUI"
                        log_click_event(f"VOTE_OUI_Étape_{idx+1}", crit["cat"])
                        st.session_state.current_q_idx += 1
                        st.rerun()
                with c_v2:
                    st.markdown("<div class='vote-btn-non'></div>", unsafe_allow_html=True)
                    if st.button("🔴 NON", use_container_width=True, key=f"btn_non_{idx}"):
                        st.session_state.answers[crit["id"]] = "NON"
                        st.session_state[f"asking_why_{crit['id']}"] = True
                        st.session_state["last_vote_type"] = "NON"
                        log_click_event(f"VOTE_NON_Étape_{idx+1}", crit["cat"])
                        st.rerun()
                with c_v3:
                    st.markdown("<div class='vote-btn-partiel'></div>", unsafe_allow_html=True)
                    if st.button("🟠 PARTIEL", use_container_width=True, key=f"btn_partiel_{idx}"):
                        st.session_state.answers[crit["id"]] = "PARTIELLEMENT"
                        st.session_state[f"asking_why_{crit['id']}"] = True
                        st.session_state["last_vote_type"] = "PARTIELLEMENT"
                        log_click_event(f"VOTE_PARTIEL_Étape_{idx+1}", crit["cat"])
                        st.rerun()

                # 3. BOUTON RETOUR QUESTION PRÉCÉDENTE
                st.markdown("<br>", unsafe_allow_html=True)
                if idx > 0:
                    st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
                    if st.button("⬅️ Question précédente", use_container_width=True):
                        st.session_state.current_q_idx -= 1
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                # 4. CASE COMMENTAIRE DE PLACEMENT BAS (TOUT EN BAS DE L'ÉCRAN)
                asking_why = st.session_state.get(f"asking_why_{crit['id']}", False)
                existing_comment = st.session_state.answers.get(f"{crit['id']}_comment", "")
                
                # Permettre aussi d'ouvrir le commentaire optionnellement
                manual_com_key = f"manual_com_open_{crit['id']}"
                
                if asking_why or st.session_state.get(manual_com_key, False) or existing_comment:
                    st.markdown("""
                    <div class='why-box-container'>
                        <div class='why-box-title'>⚠️ Pourquoi ? Qu'est-ce qui n'est pas conforme ou partiel ?</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    why_input = st.text_area(
                        f"✍️ Saisissez votre remarque (Étape {idx+1}) :",
                        value=existing_comment,
                        key=f"input_why_{crit['id']}",
                        height=100
                    )
                    
                    col_why1, col_why2 = st.columns(2)
                    with col_why1:
                        st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
                        if st.button("🚀 VALIDER ET CONTINUER", use_container_width=True, key=f"btn_val_why_{idx}"):
                            if why_input.strip():
                                st.session_state.answers[f"{crit['id']}_comment"] = why_input.strip()
                            else:
                                st.session_state.answers.pop(f"{crit['id']}_comment", None)
                            st.session_state[f"asking_why_{crit['id']}"] = False
                            st.session_state[manual_com_key] = False
                            st.session_state["just_validated_step"] = idx + 1
                            log_click_event(f"VALIDATION_COMMENTAIRE_Étape_{idx+1}", why_input.strip())
                            st.session_state.current_q_idx += 1
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                    with col_why2:
                        st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
                        if st.button("⏩ AUCUN COMMENTAIRE À FAIRE (Passer)", use_container_width=True, key=f"btn_pass_why_{idx}"):
                            st.session_state[f"asking_why_{crit['id']}"] = False
                            st.session_state[manual_com_key] = False
                            st.session_state["just_validated_step"] = idx + 1
                            log_click_event(f"PASSER_COMMENTAIRE_Étape_{idx+1}", crit["cat"])
                            st.session_state.current_q_idx += 1
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💬 Ajouter un commentaire optionnel", key=f"btn_open_opt_com_{idx}", use_container_width=True):
                        st.session_state[manual_com_key] = True
                        st.rerun()

            else:
                st.success("🎉 Questionnaire terminé ! Saisissez vos observations ci-dessous :")
                
                t_oui = sum(1 for v in st.session_state.answers.values() if v == "OUI")
                t_non = sum(1 for v in st.session_state.answers.values() if v == "NON")
                t_na = sum(1 for v in st.session_state.answers.values() if v == "N/A")
                score = t_oui
                total_ev = 15 - t_na
                pct = int((score / total_ev) * 100) if total_ev > 0 else 0
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Score Conforme", f"{score}/{total_ev}")
                m2.metric("Taux de Conformité", f"{pct}%")
                m3.metric("Non-Conformités (NON)", f"{t_non}")
                m4.metric("Non Applicables (N/A)", f"{t_na}")
                
                st.markdown("---")
                st.markdown("### 📝 Observations terrain & Actions")
                obs = st.text_area("Remarques ou écarts constatés :")
                act = st.text_area("Actions correctives immédiates :")
                
                col_fin1, col_fin2 = st.columns(2)
                with col_fin1:
                    st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
                    if st.button("⬅️ Modifier les réponses", use_container_width=True):
                        st.session_state.current_q_idx = 0
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                with col_fin2:
                    st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
                    if st.button("💾 VALIDER & ENREGISTRER L'AUDIT 5S", use_container_width=True):
                        trigger_final_save_fx()
                        
                        # Assemblage de tous les commentaires d'étapes (1 à 15)
                        step_comments_list = []
                        for c in CRITERES_OFFICIELS:
                            c_id = c["id"]
                            c_val = st.session_state.answers.get(c_id, "Non répondu")
                            c_com = st.session_state.answers.get(f"{c_id}_comment", "").strip()
                            if c_com:
                                step_comments_list.append(f"[{c['cat']} - {c_val}] : {c_com}")
                                
                        obs_parts = []
                        if step_comments_list:
                            obs_parts.append("💬 COMMENTAIRES DES ÉTAPES :\n" + "\n".join(step_comments_list))
                        if obs.strip():
                            obs_parts.append("📝 REMARQUES GLOBALES FINALES :\n" + obs.strip())
                            
                        final_obs = "\n\n".join(obs_parts) if obs_parts else "Aucune observation"
                        final_act = act.strip() if act.strip() else "Aucune action"
                        
                        audit_record = {
                            "Date": get_paris_now_str(),
                            "Zone": ZONES_MASSILLY[st.session_state.user_zone]["label"],
                            "Sponsor": ZONES_MASSILLY[st.session_state.user_zone]["sponsor"],
                            "Auditeur": st.session_state.user_name,
                            "Role": st.session_state.user_role,
                            "Score_Total": f"{score:.1f}",
                            "Pourcentage": pct,
                            "Observations": final_obs,
                            "Actions_Correctives": final_act
                        }
                        
                        # Enregistrement individuel de chaque étape + chaque commentaire d'étape
                        for c in CRITERES_OFFICIELS:
                            c_id = c["id"]
                            audit_record[c_id] = st.session_state.answers.get(c_id, "Non répondu")
                            audit_record[f"{c_id}_comment"] = st.session_state.answers.get(f"{c_id}_comment", "")
                            
                        ok, err = sauvegarder_audit_local(audit_record)
                        log_click_event("ENREGISTREMENT_FINAL_AUDIT", f"Score: {score}/15 ({pct}%) | Obs: {len(final_obs)} chars")
                        
                        st.session_state.audit_started = False
                        st.session_state.current_q_idx = 0
                        st.session_state.answers = {}
                        
                        if ok:
                            st.success("✅ Audit et l'ensemble de ses commentaires enregistrés avec succès dans Google Sheets et CSV !")
                        else:
                            st.warning(f"⚠️ Audit sauvegardé localement dans le fichier CSV (GSheets : {err})")
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

    # ========================================== ONGLET 2 : HISTORIQUE & STATISTIQUES
    elif menu_actif == "📊 Analyse & Historique":
        st.markdown("### 📊 Historique des Audits 5S Logistique")
        
        # Section Outils Admin / Test Connexion Google Sheets
        if st.session_state.get("user_role") == "Éditeur (Méthodes / Alternant)":
            with st.expand_container() if hasattr(st, 'expand_container') else st.expander("🛠️ OUTILS ADMINISTRATEUR & CONNEXION GOOGLE SHEETS"):
                st.markdown("#### Diagnostic de liaison Google Sheets")
                if st.button("🔌 TESTER LA CONNEXION GOOGLE SHEETS", use_container_width=True):
                    ok, err = sauvegarder_audit_local({
                        "Date": get_paris_now_str(),
                        "Zone": "TEST_CONNEXION",
                        "Sponsor": "SYSTEM",
                        "Auditeur": st.session_state.get('user_name', 'TEST_ADMIN'),
                        "Role": st.session_state.get('user_role', 'ADMIN'),
                        "Score_Total": 15,
                        "Pourcentage": 100,
                        "Observations": "Test de connexion manuel depuis le panneau Administrateur",
                        "Actions_Correctives": "Aucune"
                    })
                    if ok:
                        st.success("✅ Connexion Google Sheets fonctionnelle ! L'audit de test a été enregistré.")
                    else:
                        st.error(f"❌ Échec de connexion : {err}")
        
        df_hist = charger_audits()
        if not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.info("Aucun audit enregistré pour le moment.")

    # ========================================== ONGLET 3 : RAPPEL DES STANDARDS
    elif menu_actif == "🗺️ Rappel des Standards":
        st.markdown("### 🗺️ Carte des 10 Zones & Standards Massilly")
        for z_key, z_val in ZONES_MASSILLY.items():
            st.markdown(f"**{z_val['label']}** — *Sponsor : {z_val['sponsor']}*")
