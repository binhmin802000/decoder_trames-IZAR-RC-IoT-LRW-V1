
import json
import streamlit as st
from decoder import (
    clean_hex, bytes_to_hex, decode_payload, payload_to_table,
    FRAME_TYPE_NAMES, pulse_weight_for_meter_key
)


st.set_page_config(page_title="Décodeur IZAR LRZ102"
    ,page_icon="📡"
    , layout="wide")


st.title("📡 Décodeur de trames LoRaWAN IZAR RC IoT DIEHL V1 `@MyVision`")
st.markdown("Outil de qualification.Cette première version décode **le payload applicatif déjà déchiffré** des trames métier")



with st.expander("💡 Informations sur différents types de trames"):
    st.markdown(
    """
- **DS40_OQ** (index minuit + nightline): `cette trame contient notamment : l’index de minuit, la nightline, les micro-alarmes, la persistence de débit, 8 valeurs de consommation quart d’heure, le qmin/qmax, le backflow et les températures min/max.`
- **DS40_I** (consommations horaires): `Cette trame contient les consommations horaires de H-1 à H-16, ainsi que les températures min/max`
- **DS40_2S** (statistiques): `Cette trame contient les statistiques radio/LoRaWAN : énergie consommée, puissance TX, data rate, compteurs uplink/downlink, retries, ratio de transmissions non applicatives, canaux actifs, temps de réception radio, etc`
- **DS40_E** (événements) : `Cette trame contient les causes d’alarme, les alarmes présentes, les valeurs métier au moment de l’événement (Qmin/Qmax, backflow, persistence, index courant à t0, etc.).`
- **DS40_O_OMS4** (trame d'installation) **si le payload est déjà en clair** : `La trame d’installation (port 20) contient notamment le timestamp, le pulse weight (via VIF), l’index courant, et les alarmes spécifiques`

> ⚠️ Important : d'après la spécification, **tout le payload est chiffré**, et les **clés de déchiffrement** sont fournies dans un autre document / transfert de clés. Sans ce fichier de clés, on ne peut pas garantir le décodage d'une **trame LoRaWAN chiffrée brute**. Cette V1 est donc conçue pour décoder le **payload applicatif en clair**.
"""
)

with st.expander("💡 Format attendu et Port FP"):
    st.markdown(
        """
Collez une chaîne hexadécimale, par exemple :

- avec espaces : `41 24 00 00 AA BB CC DD`
- sans espaces : `41240000AABBCCDD`
- avec préfixe : `0x41240000AABBCCDD`

Indique le FPort :

- pour les trames périodiques (**DS40_OQ**, **DS40_I**, **DS40_2S**) : `183` 
- pour les trames événement (**DS40_E**) : `184` 
- pour la trame d’installation (**DS40_O_OMS4**) : `20` 

Vous pouvez aussi indiquer le **FPort** pour aider à distinguer certaines trames.
        """
    )

col1, col2 = st.columns([2, 1])
with col1:
    hex_input = st.text_area(
        "**Payload applicatif (hex)**",
        height=180,
        placeholder="Exemple : 41 24 00 00 00 00 01 00 ..."
    )
with col2:
    fport = st.number_input("FPort (optionnel)", min_value=0, max_value=255, value=183, step=1)
    show_raw = st.checkbox("Afficher les détails techniques", value=True)

if st.button("Décoder", type="primary"):
    try:
        raw = clean_hex(hex_input)
        result = decode_payload(raw, fport=fport)

        st.success(f"Trame reconnue : {result['frame_name']}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Type", result["frame_name"])
        c2.metric("Meter Key", result["header"]["meter_key"])
        c3.metric("Poids impulsion", f"{pulse_weight_for_meter_key(result['header']['meter_key'])} L/pulse")
        c4.metric("Taille payload", f"{len(raw)} octets")

        st.subheader("Valeurs décodées")
        st.dataframe(payload_to_table(result), use_container_width=True, hide_index=True)

        if show_raw:
            st.subheader("Détails techniques")
            st.json(result)

    except Exception as e:
        st.error(f"Décodage impossible : {e}")
        st.info(
            "Vérifiez que vous avez collé le **payload applicatif déjà déchiffré**. "
            "Si vous avez collé une trame LoRaWAN chiffrée brute, il faudra les clés et la règle de déchiffrement associée."
        )

