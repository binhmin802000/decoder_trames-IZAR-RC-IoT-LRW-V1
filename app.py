import streamlit as st
import hmac
from pathlib import Path

from decoder import clean_hex, decode_payload, payload_to_table, pulse_weight_for_meter_key
from security import decrypt_mode8_frame, derive_fields_from_wmbus_address


# ============================================================
# Authentification simple du portail
# ============================================================

def check_password(username: str, password: str) -> bool:
    """
    Vérifie l'identifiant et le mot de passe depuis .streamlit/secrets.toml.
    """

    try:
        passwords = st.secrets["passwords"]
    except Exception:
        st.error(
            "❌ Fichier secrets.toml introuvable ou mal configuré. "
            "Vérifie le fichier .streamlit/secrets.toml."
        )
        return False

    if username not in passwords:
        return False

    expected_password = passwords[username]

    return hmac.compare_digest(password, expected_password)


def login_page() -> None:
    """
    Affiche la page de connexion.
    """
    st.markdown("## 🔐 Connexion au portail")
    st.info("Veuillez vous connecter pour accéder au portail de décodage.")

    username = st.text_input("Identifiant")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter", type="primary"):
        if check_password(username, password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.success("✅ Connexion réussie")
            st.rerun()
        else:
            st.session_state["authenticated"] = False
            st.error("❌ Identifiant ou mot de passe incorrect")


def require_login() -> None:
    """
    Bloque l'accès au portail tant que l'utilisateur n'est pas connecté.
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        login_page()
        st.stop()


# ============================================================
# Configuration Streamlit
# ============================================================

st.set_page_config(
    page_title="Décodeur IZAR LRZ102 V2.1",
    page_icon="📡",
    layout="wide"
)

# Le portail est bloqué ici tant que l'utilisateur n'est pas connecté
require_login()


# ============================================================
# Bandeau principal
# ============================================================

st.markdown(
    """
<style>
.block-container {padding-top: 1.2rem;}
.hero {
    padding: 1rem 1.2rem;
    border-radius: 14px;
    background: #0f172a;
    color: white;
    margin-bottom: 1rem;
}
</style>

<div class="hero">
    <h2>📡 Décodeur IZAR LRZ102 V2.1</h2>
    <p>Déchiffrement Mode 8 + décodage métier + restitution EC1 + dépôt documentaire local.</p>
</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# Sidebar / Navigation
# ============================================================

with st.sidebar:
    st.header("Navigation")

    st.success(f"Connecté : {st.session_state.get('username', '')}")

    if st.button("Se déconnecter"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

    st.markdown("---")

    mode = st.radio(
        "Choisis un module",
        [
            "Déchiffrer + décoder",
            "Décoder payload clair",
            "Dépôt de documents",
            "Aide",
        ],
        index=0,
    )


# ============================================================
# Module 1 : Déchiffrer + décoder
# ============================================================

if mode == "Déchiffrer + décoder":
    st.subheader("🔐 Déchiffrer une trame sécurisée Mode 8")

    c1, c2 = st.columns([2, 1])

    with c1:
        frame_hex = st.text_area("Trame sécurisée hexadécimale", height=160)

    with c2:
        mac_len = st.selectbox("Longueur MAC", [4, 2], index=0)
        fport = st.number_input("FPort", min_value=0, max_value=255, value=183)
        show_tech = st.checkbox("Afficher détails techniques", value=True)

    k1, k2 = st.columns(2)

    with k1:
        enc_key_hex = st.text_input("Clé AES chiffrement (16 octets)")

    with k2:
        kmac1_key_hex = st.text_input("Clé KMAC1 (16 octets)")

    source = st.radio(
        "Champs IV/MAC",
        ["Saisie manuelle", "Adresse wMBus déjà formatée"],
        index=0
    )

    derived = None

    if source == "Saisie manuelle":
        a, b, c, d = st.columns(4)

        with a:
            manufacturer_hex = st.text_input("Manufacturer", value="5322")

        with b:
            identification_hex = st.text_input("Identification", placeholder="78124096")

        with c:
            version_hex = st.text_input("Version", placeholder="35")

        with d:
            device_type_hex = st.text_input("Device type", value="07")

    else:
        addr = st.text_input(
            "Adresse wMBus",
            placeholder="53 22 78 12 40 96 35 07"
        )

        if addr:
            try:
                derived = derive_fields_from_wmbus_address(clean_hex(addr))
                st.info(str(derived))
            except Exception as e:
                st.error(f"Adresse wMBus invalide : {e}")

    if st.button("🚀 Déchiffrer puis décoder", type="primary"):
        try:
            # ------------------------------------------------------------
            # 1. Préparation des champs nécessaires à l'IV / MAC
            # ------------------------------------------------------------
            if source == "Saisie manuelle":
                manufacturer = clean_hex(manufacturer_hex)
                identification = clean_hex(identification_hex)
                version = clean_hex(version_hex)
                device_type = clean_hex(device_type_hex)
            else:
                if not derived:
                    raise ValueError("Adresse wMBus non renseignée")

                manufacturer = clean_hex(derived["manufacturer_hex"])
                identification = clean_hex(derived["identification_hex"])
                version = clean_hex(derived["version_hex"])
                device_type = clean_hex(derived["device_type_hex"])

            # ------------------------------------------------------------
            # 2. Conversion de la trame en bytes + affichage diagnostic
            # ------------------------------------------------------------
            frame_bytes = clean_hex(frame_hex)

            st.subheader("🔍 Contrôle de la trame saisie")
            st.write(f"Longueur totale : **{len(frame_bytes)} octets**")

            if mac_len == 4 and len(frame_bytes) >= 4:
                st.write(
                    f"MAC détecté : `{frame_bytes[-4:].hex(' ').upper()}`"
                )
            elif mac_len == 2 and len(frame_bytes) >= 2:
                st.write(
                    f"MAC détecté : `{frame_bytes[-2:].hex(' ').upper()}`"
                )

            if len(frame_bytes) < 20:
                st.error("❌ Trame trop courte : elle est probablement tronquée.")
                st.stop()

            # ------------------------------------------------------------
            # 3. Déchiffrement Mode 8
            # ------------------------------------------------------------
            res = decrypt_mode8_frame(
                frame_bytes,
                clean_hex(enc_key_hex),
                clean_hex(kmac1_key_hex),
                manufacturer,
                identification,
                version,
                device_type,
                mac_len
            )

            # ------------------------------------------------------------
            # 4. Afficher le résultat du déchiffrement
            # ------------------------------------------------------------
            st.success("✅ Déchiffrement terminé")

            s1, s2, s3, s4 = st.columns(4)

            s1.metric("CTR", str(res["ctr_value"]))
            s2.metric("MAC reçu", res["mac_received_hex"])
            s3.metric("MAC calculé", res["mac_calculated_hex"])
            s4.metric("MAC valide", "Oui" if res["mac_valid"] else "Non")

            st.subheader("Payload déchiffré")
            st.code(res["decrypted_payload_hex"], language="text")

            # ------------------------------------------------------------
            # 5. Bloquer si MAC invalide
            # ------------------------------------------------------------
            if not res["mac_valid"]:
                st.error(
                    "❌ MAC invalide : le décodage métier est bloqué pour éviter "
                    "d'afficher des valeurs fausses."
                )

                st.info(
                    "Causes possibles : trame tronquée, mauvaise longueur MAC, "
                    "mauvaise clé KMAC1, mauvaise clé AES, mauvais Manufacturer, "
                    "mauvaise Identification, mauvaise Version ou mauvais Device type."
                )

                st.stop()

            # ------------------------------------------------------------
            # 6. Tentative de décodage métier LRZ102
            # ------------------------------------------------------------
            try:
                decoded = decode_payload(res["decrypted_payload"], fport=fport)

                st.success(f"✅ Trame métier reconnue : {decoded['frame_name']}")

                m1, m2, m3, m4 = st.columns(4)

                m1.metric("Type", decoded["frame_name"])
                m2.metric("Meter Key", decoded["header"].get("meter_key"))
                m3.metric("MAC valide", "Oui" if res["mac_valid"] else "Non")
                m4.metric("Taille payload", len(res["decrypted_payload"]))

                st.dataframe(
                    payload_to_table(decoded),
                    use_container_width=True,
                    hide_index=True
                )

            except Exception as decode_error:
                st.warning(
                    "⚠️ Déchiffrement effectué, mais le payload déchiffré "
                    "n'est pas reconnu comme une trame métier LRZ102 supportée."
                )

                st.info(f"Détail décodage métier : {decode_error}")

            # ------------------------------------------------------------
            # 7. Détails techniques optionnels
            # ------------------------------------------------------------
            if show_tech:
                st.subheader("Détails techniques du déchiffrement")
                st.json(res)

        except Exception as e:
            st.error(f"Erreur : {e}")


# ============================================================
# Module 2 : Décoder payload clair
# ============================================================

elif mode == "Décoder payload clair":
    st.subheader("📨 Décoder un payload applicatif déjà en clair")

    c1, c2 = st.columns([2, 1])

    with c1:
        payload_hex = st.text_area("Payload clair hexadécimal", height=160)

    with c2:
        fport = st.number_input(
            "FPort",
            min_value=0,
            max_value=255,
            value=183,
            key="fport_clear"
        )
        show_json = st.checkbox("Afficher JSON", value=True)

    if st.button("Décoder", type="primary"):
        try:
            raw = clean_hex(payload_hex)
            decoded = decode_payload(raw, fport=fport)

            st.success(f"Trame reconnue : {decoded['frame_name']}")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Type", decoded["frame_name"])
            col2.metric("Meter Key", decoded["header"].get("meter_key"))
            col3.metric(
                "Poids impulsion",
                f"{pulse_weight_for_meter_key(decoded['header'].get('meter_key'))} L/pulse"
            )
            col4.metric("Taille", f"{len(raw)} octets")

            st.dataframe(
                payload_to_table(decoded),
                use_container_width=True,
                hide_index=True
            )

            if show_json:
                st.json(decoded)

        except Exception as e:
            st.error(f"Erreur : {e}")


# ============================================================
# Module 3 : Dépôt de documents
# ============================================================

elif mode == "Dépôt de documents":
    st.subheader("📁 Dépôt de documents")

    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    uploaded_files = st.file_uploader(
        "Choisir un ou plusieurs fichiers",
        type=[
            "pdf",
            "docx",
            "doc",
            "xlsx",
            "xls",
            "csv",
            "txt",
            "png",
            "jpg",
            "jpeg",
        ],
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            safe_name = Path(uploaded_file.name).name
            file_path = upload_dir / safe_name

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"✅ Fichier déposé : {safe_name}")

    st.markdown("---")
    st.subheader("📄 Fichiers déjà déposés")

    files = sorted([p for p in upload_dir.glob("*") if p.is_file()])

    if not files:
        st.info("Aucun fichier déposé pour le moment.")
    else:
        for file in files:
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"📎 {file.name}")

            with col2:
                with open(file, "rb") as f:
                    st.download_button(
                        "Télécharger",
                        f,
                        file_name=file.name,
                        key=f"download_{file.name}"
                    )


# ============================================================
# Module 4 : Aide
# ============================================================

else:
    st.subheader("ℹ️ Aide")

    st.markdown(
        """
### Version V2.1

- Module de déchiffrement Mode 8 via `security.py`
- Module de décodage métier via `decoder.py`
- Restitution EC1 simplifiée : uniquement les champs `*_real_value`
- Dépôt documentaire local dans le dossier `uploads/`

### Différents types de trame

- **DS40_OQ** : index minuit + nightline  
- **DS40_I** : consommations horaires H-1 à H-16  
- **DS40_2S** : statistiques radio / LoRaWAN  
- **DS40_E** : événements / alarmes  
- **DS40_O_OMS4** : trame d'installation, port 20, si payload déjà en clair  

### Remarque

En local, les documents restent dans ton dossier projet.  
Sur Streamlit Cloud, ce stockage peut être temporaire.
"""
    )
