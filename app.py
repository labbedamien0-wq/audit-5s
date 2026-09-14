import streamlit.components.v1 as components

# Injection du système audio universel ultra-instantané
components.html("""
<script>
(function() {
    var pWin = window.parent || window;
    if (!pWin.globalAudioCtx) {
        try {
            pWin.globalAudioCtx = new (pWin.AudioContext || pWin.webkitAudioContext)();
        } catch(e) {}
    }
    
    function playInstantBip() {
        try {
            var ctx = pWin.globalAudioCtx || new (window.AudioContext || window.webkitAudioContext)();
            if (ctx.state === 'suspended') { ctx.resume(); }
            var now = ctx.currentTime;
            var notes = [523.25, 659.25, 783.99];
            notes.forEach(function(freq, i) {
                var osc = ctx.createOscillator();
                var gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(freq, now + i * 0.07);
                gain.gain.setValueAtTime(0.25, now + i * 0.07);
                gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.07 + 0.22);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now + i * 0.07);
                osc.stop(now + i * 0.07 + 0.22);
            });
        } catch(e) {}
    }
    
    function handleGlobalClick(e) {
        var target = e.target;
        if (!target) return;
        var text = (target.innerText || target.textContent || '').toUpperCase();
        if (text.includes('OUI') || text.includes('NON') || text.includes('PARTIEL') || text.includes('VALIDER') || text.includes('DÉMARRER') || text.includes('ENTRER')) {
            playInstantBip();
        }
    }
    
    pWin.document.removeEventListener('click', handleGlobalClick, true);
    pWin.document.addEventListener('click', handleGlobalClick, true);
    pWin.document.removeEventListener('touchstart', handleGlobalClick, true);
    pWin.document.addEventListener('touchstart', handleGlobalClick, true);
})();
</script>
""", height=0, width=0)

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
    page_title="Massilly - Audit 5S Mobile v79",
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
st.session_state.setdefault("layout_mode", "smartphone")
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

    # Dual Audio Engine: Native HTML5 Audio Tag (Base64 WAV) + Web Audio API synthesis for 100% fail-safe playback
    b64_audio = "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"
    js_code = f"""<audio autoplay style='display:none;' src='data:audio/wav;base64,{b64_audio}'></audio>
    <script>
    (function(){{
        try {{
            var pWin = window.parent || window;
            if (!pWin.globalAudioCtx || pWin.globalAudioCtx.state === 'closed') {{
                pWin.globalAudioCtx = new (pWin.AudioContext || pWin.webkitAudioContext)();
            }}
            var ctx = pWin.globalAudioCtx;
            if (ctx.state === 'suspended') {{ ctx.resume(); }}
            var notes = [523.25, 659.25, 783.99];
            var now = ctx.currentTime;
            notes.forEach(function(freq, i){{
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
            }});
        }} catch(e) {{}}
    }})();
    </script>"""
    components.html(js_code, height=0, width=0)
    
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
        
        # Sélecteur d'interface Smartphone vs PC
        mode_choice = st.radio("📱 Mode d'affichage d'interface :", ["📱 Smartphone (1 Colonne)", "💻 PC / Tablette (2 Colonnes)"], index=0 if st.session_state.get("layout_mode") == "smartphone" else 1, horizontal=True, key="mode_selector_radio")
        st.session_state["layout_mode"] = "smartphone" if "Smartphone" in mode_choice else "pc"
        st.markdown("<p style='text-align: center; font-size: 18px; color: #CBD5E1; font-weight: 700;'>Sélectionnez votre zone :</p>", unsafe_allow_html=True)

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

        current_mode = st.session_state.get("layout_mode", "smartphone")
        
        if current_mode == "smartphone":
            # Affichage séquentiel strict (1 colonne : Zone 1 à Zone 10)
            for idx, z in enumerate(ZONES_BADGES):
                z_info = ZONES_MASSILLY.get(z["key"], {})
                z_label = z_info.get("label", z["key"])
                st.markdown(f"<div class='zone-marker-{idx}'></div>", unsafe_allow_html=True)
                lbl = f"{z['icon']}  {z_label}"
                if st.button(lbl, key=f"z_badge_sp_{idx}", use_container_width=True):
                    st.session_state.pending_zone = z["key"]
                    st.session_state.auth_step = 4
                    st.rerun()
        else:
            # Affichage PC / Tablette par rangées (Zone 1 & 2, Zone 3 & 4...)
            for i in range(0, len(ZONES_BADGES), 2):
                col_z1, col_z2 = st.columns(2)
                for offset, col_target in enumerate([col_z1, col_z2]):
                    idx = i + offset
                    if idx < len(ZONES_BADGES):
                        z = ZONES_BADGES[idx]
                        z_info = ZONES_MASSILLY.get(z["key"], {})
                        z_label = z_info.get("label", z["key"])
                        with col_target:
                            st.markdown(f"<div class='zone-marker-{idx}'></div>", unsafe_allow_html=True)
                            lbl = f"{z['icon']}  {z_label}"
                            if st.button(lbl, key=f"z_badge_pc_{idx}", use_container_width=True):
                                st.session_state.pending_zone = z["key"]
                                st.session_state.auth_step = 4
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
                        st.session_state["just_validated_step"] = idx + 1
                        st.session_state["last_vote_type"] = "NON"
                        log_click_event(f"VOTE_NON_Étape_{idx+1}", crit["cat"])
                        st.rerun()
                with c_v3:
                    st.markdown("<div class='vote-btn-partiel'></div>", unsafe_allow_html=True)
                    if st.button("🟠 PARTIEL", use_container_width=True, key=f"btn_partiel_{idx}"):
                        st.session_state.answers[crit["id"]] = "PARTIELLEMENT"
                        st.session_state[f"asking_why_{crit['id']}"] = True
                        st.session_state["just_validated_step"] = idx + 1
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
                            log_click_event(f"VALIDATION_COMMENTAIRE_Étape_{idx+1}", why_input.strip())
                            st.session_state.current_q_idx += 1
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                    with col_why2:
                        st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
                        if st.button("⏩ AUCUN COMMENTAIRE À FAIRE (Passer)", use_container_width=True, key=f"btn_pass_why_{idx}"):
                            st.session_state[f"asking_why_{crit['id']}"] = False
                            st.session_state[manual_com_key] = False
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
