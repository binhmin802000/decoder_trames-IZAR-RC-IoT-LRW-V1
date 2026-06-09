
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Tuple
import re

BASE_TIME = datetime(2012, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

FRAME_TYPE_NAMES = {
    1: "DS40_I",
    4: "DS40_2S",
    9: "DS40_OQ",
    63: "DS40_E",
}

FLOW_DURATION_MAP = {
    0: "Aucune persistance",
    1: "0 < durée < 5 min",
    2: "5 min ≤ durée < 15 min",
    3: "15 min ≤ durée < 60 min",
    4: "60 min ≤ durée < 3 h",
    5: "3 h ≤ durée < 6 h",
    6: "6 h ≤ durée < 12 h",
    7: "12 h ≤ durée < 24 h",
    8: "24 h ≤ durée < 2 jours",
    9: "2 jours ≤ durée < 4 jours",
    10: "4 jours ≤ durée < 8 jours",
    11: "8 jours ≤ durée < 15 jours",
    12: "15 jours ≤ durée < 30 jours",
    13: "30 jours ≤ durée < 90 jours",
    14: "90 jours ≤ durée < 180 jours",
    15: "≥ 180 jours",
}

DS40_OQ_ALARMS = {
    0: "Backflow impactant",
    1: "Persistance de débit en cours",
    4: "Overflow",
    5: "Fraude - champ magnétique détecté",
    6: "Fraude - module retiré",
    9: "Batterie faible",
    10: "Horloge module mise à jour",
    11: "Module reconfiguré",
    13: "Duty cycle",
    14: "Échec d'acquisition",
}

DS40_E_CAUSES = {
    1: "Fraude magnétique",
    2: "Retrait du module radio",
    3: "Backflow niveau 2",
}

DS40_E_ALARMS = {
    4: "Overflow",
    8: "Température basse / risque de gel",
    11: "Batterie faible",
    12: "Horloge module mise à jour",
    15: "Reconfiguration",
    20: "Fin de reset horloge",
    24: "Duty cycle",
    26: "Fraude magnétique",
    27: "Retrait du module radio",
    28: "Défaut d'acquisition",
    30: "Backflow niveau 2",
    33: "Fin persistance débit nul",
    36: "Persistance de débit en cours",
    37: "Persistance débit impactant en cours",
}

LORA_TX_POWER = {0: '20 dBm', 1: '14 dBm', 2: '11 dBm', 3: '8 dBm', 4: '5 dBm', 5: '2 dBm'}
LORA_DR = {
    0: 'LoRa SF12/125 kHz', 1: 'LoRa SF11/125 kHz', 2: 'LoRa SF10/125 kHz',
    3: 'LoRa SF9/125 kHz', 4: 'LoRa SF8/125 kHz', 5: 'LoRa SF7/125 kHz',
    6: 'LoRa SF7/250 kHz', 7: 'FSK 50 kbps'
}


def clean_hex(s: str) -> bytes:
    if not s or not s.strip():
        raise ValueError("la chaîne hexadécimale est vide")
    s = s.replace('0x', '').replace('0X', '')
    s = re.sub(r'[^0-9A-Fa-f]', '', s)
    if len(s) % 2 != 0:
        raise ValueError("nombre impair de caractères hexadécimaux")
    return bytes.fromhex(s)


def bytes_to_hex(b: bytes) -> str:
    return ' '.join(f'{x:02X}' for x in b)


def u16_le(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o+2], 'little', signed=False)


def s16_le(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o+2], 'little', signed=True)


def u32_le(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o+4], 'little', signed=False)


def s32_le(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o+4], 'little', signed=True)


def s8(v: int) -> int:
    return v - 256 if v >= 128 else v


def pulse_weight_for_meter_key(meter_key: int):
    table = {
        1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 7: 1,
        6: 10, 8: 10, 9: 100, 10: 1000, 11: 100,
    }
    return table.get(meter_key, 'Réservé')


def parse_header(word: int) -> Dict[str, Any]:
    meter_key = word & 0x0F
    fw_major = (word >> 4) & 0x03
    fw_minor = (word >> 6) & 0x0F
    frame_type = (word >> 10) & 0x3F
    return {
        'raw_word': word,
        'raw_hex_le': f'{word:04X}',
        'meter_key': meter_key,
        'fw_major': fw_major,
        'fw_minor': fw_minor,
        'frame_type': frame_type,
    }


def decode_timestamp(seconds_since_2012: int) -> str:
    dt = BASE_TIME + timedelta(seconds=seconds_since_2012)
    return dt.isoformat()


def bits_set(value: int, labels: Dict[int, str], bit_count: int = 16) -> List[str]:
    out = []
    for bit, name in labels.items():
        if value & (1 << bit):
            out.append(name)
    return out


def decode_ds40_oq(payload: bytes, meter_key: int) -> Dict[str, Any]:
    if len(payload) < 40:
        raise ValueError('DS40_OQ attendu sur 40 octets (payload en clair)')
    ts = u32_le(payload, 2)
    alarms = u16_le(payload, 6)
    cfg = payload[8]
    dfq_low = cfg & 0x0F
    midnight_index = u32_le(payload, 9)

    # valeur 2.5 octets spécifique sur offsets 13,14 et nibble bas de 15
    low16 = u16_le(payload, 13)
    high4 = payload[15] & 0x0F
    volume_20b = low16 | (high4 << 16)
    if volume_20b == 0xBFFFF:
        volume_delta = 'Positive Overflow'
    elif volume_20b == 0xC0000:
        volume_delta = 'Negative Overflow'
    elif volume_20b >= 0xC0001:
        volume_delta = volume_20b - (1 << 20)
    else:
        volume_delta = volume_20b

    dfq_ongoing = (payload[15] >> 4) & 0x0F
    qh0 = payload[16] & 0x1F

    quarter_hours = [s16_le(payload, 17 + 2*i) for i in range(8)]
    qmin_ec = payload[33]
    qmin = payload[34]
    qmax = payload[35]
    rvc = payload[36]
    rna = payload[37]
    temp_max = s8(payload[38])
    temp_min = s8(payload[39])

    pulse_weight = pulse_weight_for_meter_key(meter_key)
    midnight_index_l = midnight_index * pulse_weight if isinstance(pulse_weight, int) else None

    return {
        'timestamp_seconds_since_2012': ts,
        'timestamp_utc': decode_timestamp(ts),
        'micro_alarms_raw': alarms,
        'micro_alarms_active': bits_set(alarms, DS40_OQ_ALARMS),
        'index_configuration_raw': cfg,
        'flow_persistence_code': dfq_low,
        'flow_persistence_label': FLOW_DURATION_MAP.get(dfq_low, 'Inconnu'),
        'midnight_index_pulses': midnight_index,
        'midnight_index_liters': midnight_index_l,
        'consumption_0h_to_xh_pulses': volume_delta,
        'ongoing_flow_persistence_code': dfq_ongoing,
        'ongoing_flow_persistence_label': FLOW_DURATION_MAP.get(dfq_ongoing, 'Inconnu'),
        'quarter_hour_start_code': qh0,
        'quarter_hourly_pulses': quarter_hours,
        'qmin_current_day_ec1_code': qmin_ec,
        'qmin_previous_day_ec1_code': qmin,
        'qmax_previous_day_ec1_code': qmax,
        'cumulative_backflow_ec1_code': rvc,
        'backflow_occurrences_ec1_code': rna,
        'temp_max_c': temp_max,
        'temp_min_c': temp_min,
    }


def decode_ds40_i(payload: bytes, meter_key: int) -> Dict[str, Any]:
    if len(payload) < 40:
        raise ValueError('DS40_I attendu sur 40 octets (payload en clair)')
    ts = u32_le(payload, 2)
    consumptions = [s16_le(payload, 6 + 2*i) for i in range(16)]
    return {
        'timestamp_seconds_since_2012': ts,
        'timestamp_utc': decode_timestamp(ts),
        'hourly_consumptions_pulses_h_minus_1_to_h_minus_16': consumptions,
        'temp_max_c': s8(payload[38]),
        'temp_min_c': s8(payload[39]),
    }


def decode_ds40_2s(payload: bytes, meter_key: int) -> Dict[str, Any]:
    if len(payload) < 26:
        raise ValueError('DS40_2S attendu sur au moins 26 octets (payload en clair)')
    ts = u32_le(payload, 2)
    dr_byte = payload[7]
    tx_power = (dr_byte >> 4) & 0x0F
    dr = dr_byte & 0x0F

    txc_msn = payload[8]
    txc_lsn_byte = payload[9]
    uplink_counter = ((txc_msn << 4) | ((txc_lsn_byte >> 4) & 0x0F))

    downlink_msn = txc_lsn_byte & 0x0F
    downlink_lsn = (payload[10] >> 4) & 0x0F
    downlink_counter_code = (downlink_msn << 4) | downlink_lsn
    cfg_changes = payload[10] & 0x0F

    rp = payload[11]
    n_param = (rp >> 4) & 0x0F
    retries = rp & 0x0F

    rx_dn = u16_le(payload, 14) & 0x3FFF

    return {
        'timestamp_seconds_since_2012': ts,
        'timestamp_utc': decode_timestamp(ts),
        'energy_consumed_percent_approx': payload[6] * 0.4,
        'tx_power_code': tx_power,
        'tx_power_label': LORA_TX_POWER.get(tx_power, 'Inconnu'),
        'data_rate_code': dr,
        'data_rate_label': LORA_DR.get(dr, 'Inconnu'),
        'uplink_counter_code': uplink_counter,
        'downlink_counter_code': downlink_counter_code,
        'config_changes_since_last_ds40_2s': cfg_changes,
        'network_bandwidth_n_parameter': n_param,
        'retries_per_transmission': retries,
        'non_applicative_transmissions_percent_approx': payload[12] * 0.4,
        'additional_active_channels_count': (payload[13] >> 3) & 0x1F,
        'default_channel_mask_bits_0_2': payload[13] & 0x07,
        'radio_receiver_active_seconds': rx_dn,
        'session_loss_remaining_frames': payload[24] if len(payload) > 24 else None,
        'force_join_request_remaining_days': payload[25] if len(payload) > 25 else None,
    }


def decode_ds40_e(payload: bytes, meter_key: int) -> Dict[str, Any]:
    if len(payload) < 40:
        raise ValueError('DS40_E attendu sur 40 octets (payload en clair)')
    ts = u32_le(payload, 2)
    event_cause = payload[6]
    alarms = int.from_bytes(payload[7:12], 'little', signed=False)
    repetition = payload[33]
    return {
        'timestamp_seconds_since_2012': ts,
        'timestamp_utc': decode_timestamp(ts),
        'event_cause_raw': event_cause,
        'event_cause_active': bits_set(event_cause, DS40_E_CAUSES, bit_count=8),
        'alarms_raw': alarms,
        'alarms_active': bits_set(alarms, DS40_E_ALARMS, bit_count=40),
        'qmin_in_progress_ec1_code': payload[12],
        'qmax_in_progress_ec1_code': payload[14],
        'backflow_number_ec1_code': payload[16],
        'backflow_volume_ec1_code': payload[17],
        'flow_persistence_low_nibble': payload[21] & 0x0F,
        'flow_persistence_low_label': FLOW_DURATION_MAP.get(payload[21] & 0x0F, 'Inconnu'),
        'flow_persistence_high_nibble': (payload[22] >> 4) & 0x0F,
        'flow_persistence_high_label': FLOW_DURATION_MAP.get((payload[22] >> 4) & 0x0F, 'Inconnu'),
        'event_repetition_raw': repetition,
        'repeat_cycle_disabled': bool((repetition >> 2) & 0x01),
        'repeat_index': repetition & 0x03,
        'current_index_t0_pulses': u32_le(payload, 36),
    }


def decode_ds40_o_oms4(payload: bytes) -> Dict[str, Any]:
    if len(payload) < 14:
        raise ValueError('DS40_O_OMS4 attendu sur 14 octets (payload en clair)')
    vif = payload[7]
    pulse_per = {0x13: '1 L/pulse', 0x14: '10 L/pulse', 0x15: '100 L/pulse', 0x16: '1000 L/pulse'}.get(vif, 'Inconnu')
    alarm_byte = payload[13]
    alarms = []
    if alarm_byte & (1 << 1):
        alarms.append('Overflow')
    if alarm_byte & (1 << 3):
        alarms.append('Fraude - champ magnétique détecté')
    if alarm_byte & (1 << 4):
        alarms.append('Fraude - module retiré')
    if alarm_byte & (1 << 5):
        alarms.append('Backflow impactant')
    return {
        'dif_0': payload[0],
        'vif_1': payload[1],
        'timestamp_raw_hex': bytes_to_hex(payload[2:6]),
        'dif_6': payload[6],
        'vif_7': vif,
        'pulse_weight_label': pulse_per,
        'current_index_pulses_signed': s32_le(payload, 8),
        'manufacturer_data_header': payload[12],
        'alarms_raw': alarm_byte,
        'alarms_active': alarms,
    }


def decode_payload(payload: bytes, fport: int | None = None) -> Dict[str, Any]:
    # Cas installation frame (port 20, payload en clair OMS4) : pas le même header que DS40_*
    if fport == 20 and len(payload) == 14:
        return {
            'frame_name': 'DS40_O_OMS4',
            'header': {'meter_key': None, 'fw_major': None, 'fw_minor': None, 'frame_type': None},
            'raw_payload_hex': bytes_to_hex(payload),
            'decoded': decode_ds40_o_oms4(payload),
        }

    if len(payload) < 2:
        raise ValueError('payload trop court')

    header_word = u16_le(payload, 0)
    header = parse_header(header_word)
    frame_type = header['frame_type']
    meter_key = header['meter_key']
    frame_name = FRAME_TYPE_NAMES.get(frame_type, f'INCONNU_{frame_type}')

    if frame_type == 9:
        decoded = decode_ds40_oq(payload, meter_key)
    elif frame_type == 1:
        decoded = decode_ds40_i(payload, meter_key)
    elif frame_type == 4:
        decoded = decode_ds40_2s(payload, meter_key)
    elif frame_type == 63:
        decoded = decode_ds40_e(payload, meter_key)
    else:
        raise ValueError(f'type de trame non pris en charge dans cette V1 : {frame_type}')

    return {
        'frame_name': frame_name,
        'header': header,
        'raw_payload_hex': bytes_to_hex(payload),
        'decoded': decoded,
    }


def payload_to_table(result: Dict[str, Any]):
    rows = []
    rows.append({'Section': 'Trame', 'Champ': 'Type', 'Valeur': result['frame_name']})
    header = result.get('header', {})
    for key, label in [('meter_key', 'Meter Key'), ('fw_major', 'FW major'), ('fw_minor', 'FW minor'), ('frame_type', 'Frame type')]:
        if header.get(key) is not None:
            rows.append({'Section': 'En-tête', 'Champ': label, 'Valeur': header.get(key)})
    for k, v in result['decoded'].items():
        rows.append({'Section': 'Payload', 'Champ': k, 'Valeur': v})
    return rows
