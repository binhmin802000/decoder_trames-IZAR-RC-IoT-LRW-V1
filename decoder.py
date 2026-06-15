from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Tuple, Union
import re

BASE_TIME = datetime(2012, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
FRAME_TYPE_NAMES = {1: "DS40_I", 4: "DS40_2S", 9: "DS40_OQ", 63: "DS40_E"}
FLOW_DURATION_MAP = {0:"Aucune persistance",1:"0 < durée < 5 min",2:"5 min ≤ durée < 15 min",3:"15 min ≤ durée < 60 min",4:"60 min ≤ durée < 3 h",5:"3 h ≤ durée < 6 h",6:"6 h ≤ durée < 12 h",7:"12 h ≤ durée < 24 h",8:"24 h ≤ durée < 2 jours",9:"2 jours ≤ durée < 4 jours",10:"4 jours ≤ durée < 8 jours",11:"8 jours ≤ durée < 15 jours",12:"15 jours ≤ durée < 30 jours",13:"30 jours ≤ durée < 90 jours",14:"90 jours ≤ durée < 180 jours",15:"≥ 180 jours"}
DS40_OQ_ALARMS = {0:"Backflow impactant",1:"Persistance de débit en cours",4:"Overflow",5:"Fraude - champ magnétique détecté",6:"Fraude - module retiré",9:"Batterie faible",10:"Horloge module mise à jour",11:"Module reconfiguré",13:"Duty cycle",14:"Échec d'acquisition"}
DS40_E_CAUSES = {1:"Fraude magnétique",2:"Retrait du module radio",3:"Backflow niveau 2"}
DS40_E_ALARMS = {4:"Overflow",8:"Température basse / risque de gel",11:"Batterie faible",12:"Horloge module mise à jour",15:"Reconfiguration",20:"Fin de reset horloge",24:"Duty cycle",26:"Fraude magnétique",27:"Retrait du module radio",28:"Défaut d'acquisition",30:"Backflow niveau 2",33:"Fin persistance débit nul",36:"Persistance de débit en cours",37:"Persistance débit impactant en cours"}
LORA_TX_POWER = {0:'20 dBm',1:'14 dBm',2:'11 dBm',3:'8 dBm',4:'5 dBm',5:'2 dBm'}
LORA_DR = {0:'LoRa SF12/125 kHz',1:'LoRa SF11/125 kHz',2:'LoRa SF10/125 kHz',3:'LoRa SF9/125 kHz',4:'LoRa SF8/125 kHz',5:'LoRa SF7/125 kHz',6:'LoRa SF7/250 kHz',7:'FSK 50 kbps'}
EC1_TABLE: Dict[int, Union[Tuple[int, int], str]] = {0:(0,0),1:(1,1),2:(2,2),3:(3,3),4:(4,4),5:(5,5),6:(6,6),7:(7,7),8:(8,8),9:(9,9),10:(10,11),11:(12,13),12:(14,15),13:(16,17),14:(18,19),15:(20,21),16:(22,23),17:(24,25),18:(26,27),19:(28,29),20:(30,34),21:(35,39),22:(40,44),23:(45,49),24:(50,54),25:(55,59),26:(60,64),27:(65,69),28:(70,74),29:(75,79),30:(80,84),31:(85,89),32:(90,94),33:(95,99),34:(100,104),35:(105,109),36:(110,114),37:(115,119),38:(120,124),39:(125,129),40:(130,134),41:(135,139),42:(140,144),43:(145,149),44:(150,154),45:(155,159),46:(160,164),47:(165,169),48:(170,174),49:(175,179),50:(180,184),51:(185,189),52:(190,194),53:(195,199),54:(200,209),55:(210,219),56:(220,229),57:(230,239),58:(240,249),59:(250,259),60:(260,269),61:(270,279),62:(280,289),63:(290,299),64:(300,309),65:(310,319),66:(320,329),67:(330,339),68:(340,349),69:(350,359),70:(360,369),71:(370,379),72:(380,389),73:(390,399),74:(400,419),75:(420,439),76:(440,459),77:(460,479),78:(480,499),79:(500,519),80:(520,539),81:(540,559),82:(560,579),83:(580,599),84:(600,619),85:(620,639),86:(640,659),87:(660,679),88:(680,699),89:(700,719),90:(720,739),91:(740,759),92:(760,779),93:(780,799),94:(800,839),95:(840,879),96:(880,919),97:(920,959),98:(960,999),99:(1000,1039),100:(1040,1079),101:(1080,1119),102:(1120,1159),103:(1160,1199),104:(1200,1239),105:(1240,1279),106:(1280,1319),107:(1320,1359),108:(1360,1399),109:(1400,1439),110:(1440,1479),111:(1480,1519),112:(1520,1559),113:(1560,1599),114:(1600,1679),115:(1680,1759),116:(1760,1839),117:(1840,1919),118:(1920,1999),119:(2000,2079),120:(2080,2159),121:(2160,2239),122:(2240,2319),123:(2320,2399),124:(2400,2479),125:(2480,2559),126:(2560,2639),127:(2640,2719),128:(2720,2799),129:(2800,2879),130:(2880,2959),131:(2960,3039),132:(3040,3119),133:(3120,3199),134:(3200,3359),135:(3360,3519),136:(3520,3679),137:(3680,3839),138:(3840,3999),139:(4000,4159),140:(4160,4319),141:(4320,4479),142:(4480,4639),143:(4640,4799),144:(4800,4959),145:(4960,5119),146:(5120,5279),147:(5280,5439),148:(5440,5599),149:(5600,5759),150:(5760,5919),151:(5920,6079),152:(6080,6239),153:(6240,6399),154:(6400,6719),155:(6720,7039),156:(7040,7359),157:(7360,7679),158:(7680,7999),159:(8000,8319),160:(8320,8639),161:(8640,8959),162:(8960,9279),163:(9280,9599),164:(9600,9919),165:(9920,10239),166:(10240,10559),167:(10560,10879),168:(10880,11199),169:(11200,11519),170:(11520,11839),171:(11840,12159),172:(12160,12479),173:(12480,12799),174:(12800,13439),175:(13440,14079),176:(14080,14719),177:(14720,15359),178:(15360,15999),179:(16000,16639),180:(16640,17279),181:(17280,17919),182:(17920,18559),183:(18560,19199),184:(19200,19839),185:(19840,20479),186:(20480,21119),187:(21120,21759),188:(21760,22399),189:(22400,23039),190:(23040,23679),191:(23680,24319),192:(24320,24959),193:(24960,25599),194:(25600,26879),195:(26880,28159),196:(28160,29439),197:(29440,30719),198:(30720,31999),199:(32000,33279),200:(33280,34559),201:(34560,35839),202:(35840,37119),203:(37120,38399),204:(38400,39679),205:(39680,40959),206:(40960,42239),207:(42240,43519),208:(43520,44799),209:(44800,46079),210:(46080,47359),211:(47360,48639),212:(48640,49919),213:(49920,51199),214:(51200,53759),215:(53760,56319),216:(56320,58879),217:(58880,61439),218:(61440,63999),219:(64000,66559),220:(66560,69119),221:(69120,71679),222:(71680,74239),223:(74240,76799),224:(76800,79359),225:(79360,81919),226:(81920,84479),227:(84480,87039),228:(87040,89599),229:(89600,92159),230:(92160,94719),231:(94720,97279),232:(97280,99839),233:(99840,102399),234:(102400,107519),235:(107520,112639),236:(112640,117759),237:(117760,122879),238:(122880,127999),239:(128000,133119),240:(133120,138239),241:(138240,143359),242:(143360,148479),243:(148480,153599),244:(153600,158719),245:(158720,163839),246:(163840,168959),247:(168960,174079),248:(174080,179199),249:(179200,184319),250:(184320,189439),251:(189440,194559),252:(194560,199679),253:(199680,204799),254:'Overflow',255:'Anomaly'}

def clean_hex(s: str) -> bytes:
    if not s or not s.strip(): raise ValueError("la chaîne hexadécimale est vide")
    s = s.replace('0x','').replace('0X','')
    s = re.sub(r'[^0-9A-Fa-f]', '', s)
    if len(s) % 2 != 0: raise ValueError("nombre impair de caractères hexadécimaux")
    return bytes.fromhex(s)

def bytes_to_hex(b: bytes) -> str: return ' '.join(f'{x:02X}' for x in b)
def u16_le(b: bytes, o: int) -> int: return int.from_bytes(b[o:o+2], 'little', signed=False)
def s16_le(b: bytes, o: int) -> int: return int.from_bytes(b[o:o+2], 'little', signed=True)
def u32_le(b: bytes, o: int) -> int: return int.from_bytes(b[o:o+4], 'little', signed=False)
def s32_le(b: bytes, o: int) -> int: return int.from_bytes(b[o:o+4], 'little', signed=True)
def s8(v: int) -> int: return v - 256 if v >= 128 else v

def pulse_weight_for_meter_key(meter_key: int):
    return {1:1,2:1,3:1,4:1,5:1,7:1,6:10,8:10,9:100,10:1000,11:100}.get(meter_key, 'Réservé')

def parse_header(word: int) -> Dict[str, Any]:
    return {'raw_word': word, 'raw_hex_le': f'{word:04X}', 'meter_key': word & 0x0F, 'fw_major': (word >> 4) & 0x03, 'fw_minor': (word >> 6) & 0x0F, 'frame_type': (word >> 10) & 0x3F}

def decode_timestamp(seconds_since_2012: int) -> str: return (BASE_TIME + timedelta(seconds=seconds_since_2012)).isoformat()
def bits_set(value: int, labels: Dict[int, str], bit_count: int = 16) -> List[str]: return [name for bit, name in labels.items() if value & (1 << bit)]

def decode_ec1(code: int) -> Any:
    mapping = EC1_TABLE.get(code)
    if mapping is None: return None
    if isinstance(mapping, str): return mapping
    return mapping[0]

def add_ec1_fields(prefix: str, code: int) -> Dict[str, Any]:
    return {f'{prefix}_real_value': decode_ec1(code)}

def decode_ds40_oq(payload: bytes, meter_key: int) -> Dict[str, Any]:
    if len(payload) < 40: raise ValueError('DS40_OQ attendu sur 40 octets (payload en clair)')
    ts = u32_le(payload,2); alarms = u16_le(payload,6); cfg = payload[8]; dfq_low = cfg & 0x0F; midnight_index = u32_le(payload,9)
    low16 = u16_le(payload,13); high4 = payload[15] & 0x0F; volume_20b = low16 | (high4 << 16)
    if volume_20b == 0xBFFFF: volume_delta = 'Positive Overflow'
    elif volume_20b == 0xC0000: volume_delta = 'Negative Overflow'
    elif volume_20b >= 0xC0001: volume_delta = volume_20b - (1 << 20)
    else: volume_delta = volume_20b
    dfq_ongoing = (payload[15] >> 4) & 0x0F; qh0 = payload[16] & 0x1F
    quarter_hours = [s16_le(payload,17+2*i) for i in range(8)]
    pulse_weight = pulse_weight_for_meter_key(meter_key)
    result = {'timestamp_seconds_since_2012': ts, 'timestamp_utc': decode_timestamp(ts), 'micro_alarms_raw': alarms, 'micro_alarms_active': bits_set(alarms, DS40_OQ_ALARMS), 'index_configuration_raw': cfg, 'flow_persistence_code': dfq_low, 'flow_persistence_label': FLOW_DURATION_MAP.get(dfq_low,'Inconnu'), 'midnight_index_pulses': midnight_index, 'midnight_index_liters': midnight_index * pulse_weight if isinstance(pulse_weight,int) else None, 'consumption_0h_to_xh_pulses': volume_delta, 'ongoing_flow_persistence_code': dfq_ongoing, 'ongoing_flow_persistence_label': FLOW_DURATION_MAP.get(dfq_ongoing,'Inconnu'), 'quarter_hour_start_code': qh0, 'quarter_hourly_pulses': quarter_hours, 'temp_max_c': s8(payload[38]), 'temp_min_c': s8(payload[39])}
    result.update(add_ec1_fields('qmin_current_day', payload[33])); result.update(add_ec1_fields('qmin_previous_day', payload[34])); result.update(add_ec1_fields('qmax_previous_day', payload[35])); result.update(add_ec1_fields('cumulative_backflow', payload[36])); result.update(add_ec1_fields('backflow_occurrences', payload[37]))
    return result

def decode_ds40_i(payload: bytes, meter_key: int) -> Dict[str, Any]:
    if len(payload) < 40: raise ValueError('DS40_I attendu sur 40 octets (payload en clair)')
    ts = u32_le(payload,2)
    return {'timestamp_seconds_since_2012':ts, 'timestamp_utc':decode_timestamp(ts), 'hourly_consumptions_pulses_h_minus_1_to_h_minus_16':[s16_le(payload,6+2*i) for i in range(16)], 'temp_max_c':s8(payload[38]), 'temp_min_c':s8(payload[39])}

def decode_ds40_2s(payload: bytes, meter_key: int) -> Dict[str, Any]:
    if len(payload) < 26: raise ValueError('DS40_2S attendu sur au moins 26 octets (payload en clair)')
    ts = u32_le(payload,2); dr_byte = payload[7]; tx_power=(dr_byte>>4)&0x0F; dr=dr_byte&0x0F; uplink_counter=(payload[8]<<4)|((payload[9]>>4)&0x0F); downlink_counter_code=((payload[9]&0x0F)<<4)|((payload[10]>>4)&0x0F); rp=payload[11]
    return {'timestamp_seconds_since_2012':ts, 'timestamp_utc':decode_timestamp(ts), 'energy_consumed_percent_approx':payload[6]*0.4, 'tx_power_code':tx_power, 'tx_power_label':LORA_TX_POWER.get(tx_power,'Inconnu'), 'data_rate_code':dr, 'data_rate_label':LORA_DR.get(dr,'Inconnu'), 'uplink_counter_code':uplink_counter, 'downlink_counter_code':downlink_counter_code, 'config_changes_since_last_ds40_2s':payload[10]&0x0F, 'network_bandwidth_n_parameter':(rp>>4)&0x0F, 'retries_per_transmission':rp&0x0F, 'non_applicative_transmissions_percent_approx':payload[12]*0.4, 'additional_active_channels_count':(payload[13]>>3)&0x1F, 'default_channel_mask_bits_0_2':payload[13]&0x07, 'radio_receiver_active_seconds':u16_le(payload,14)&0x3FFF, 'session_loss_remaining_frames':payload[24] if len(payload)>24 else None, 'force_join_request_remaining_days':payload[25] if len(payload)>25 else None}

def decode_ds40_e(payload: bytes, meter_key: int) -> Dict[str, Any]:
    if len(payload) < 40: raise ValueError('DS40_E attendu sur 40 octets (payload en clair)')
    ts=u32_le(payload,2); event_cause=payload[6]; alarms=int.from_bytes(payload[7:12],'little',signed=False); repetition=payload[33]
    result={'timestamp_seconds_since_2012':ts,'timestamp_utc':decode_timestamp(ts),'event_cause_raw':event_cause,'event_cause_active':bits_set(event_cause,DS40_E_CAUSES,bit_count=8),'alarms_raw':alarms,'alarms_active':bits_set(alarms,DS40_E_ALARMS,bit_count=40),'flow_persistence_low_nibble':payload[21]&0x0F,'flow_persistence_low_label':FLOW_DURATION_MAP.get(payload[21]&0x0F,'Inconnu'),'flow_persistence_high_nibble':(payload[22]>>4)&0x0F,'flow_persistence_high_label':FLOW_DURATION_MAP.get((payload[22]>>4)&0x0F,'Inconnu'),'event_repetition_raw':repetition,'repeat_cycle_disabled':bool((repetition>>2)&0x01),'repeat_index':repetition&0x03,'current_index_t0_pulses':u32_le(payload,36)}
    result.update(add_ec1_fields('qmin_in_progress', payload[12])); result.update(add_ec1_fields('qmax_in_progress', payload[14])); result.update(add_ec1_fields('backflow_number', payload[16])); result.update(add_ec1_fields('backflow_volume', payload[17]))
    return result

def decode_ds40_o_oms4(payload: bytes) -> Dict[str, Any]:
    if len(payload)<14: raise ValueError('DS40_O_OMS4 attendu sur 14 octets (payload en clair)')
    vif=payload[7]; pulse_per={0x13:'1 L/pulse',0x14:'10 L/pulse',0x15:'100 L/pulse',0x16:'1000 L/pulse'}.get(vif,'Inconnu'); alarm_byte=payload[13]; alarms=[]
    if alarm_byte & (1<<1): alarms.append('Overflow')
    if alarm_byte & (1<<3): alarms.append('Fraude - champ magnétique détecté')
    if alarm_byte & (1<<4): alarms.append('Fraude - module retiré')
    if alarm_byte & (1<<5): alarms.append('Backflow impactant')
    return {'dif_0':payload[0], 'vif_1':payload[1], 'timestamp_raw_hex':bytes_to_hex(payload[2:6]), 'dif_6':payload[6], 'vif_7':vif, 'pulse_weight_label':pulse_per, 'current_index_pulses_signed':s32_le(payload,8), 'manufacturer_data_header':payload[12], 'alarms_raw':alarm_byte, 'alarms_active':alarms}

def decode_payload(payload: bytes, fport: int | None = None) -> Dict[str, Any]:
    if fport == 20 and len(payload) == 14: return {'frame_name':'DS40_O_OMS4','header':{'meter_key':None,'fw_major':None,'fw_minor':None,'frame_type':None},'raw_payload_hex':bytes_to_hex(payload),'decoded':decode_ds40_o_oms4(payload)}
    if len(payload)<2: raise ValueError('payload trop court')
    header=parse_header(u16_le(payload,0)); frame_type=header['frame_type']; meter_key=header['meter_key']; frame_name=FRAME_TYPE_NAMES.get(frame_type,f'INCONNU_{frame_type}')
    if frame_type == 9: decoded=decode_ds40_oq(payload,meter_key)
    elif frame_type == 1: decoded=decode_ds40_i(payload,meter_key)
    elif frame_type == 4: decoded=decode_ds40_2s(payload,meter_key)
    elif frame_type == 63: decoded=decode_ds40_e(payload,meter_key)
    else: raise ValueError(f'type de trame non pris en charge dans cette version : {frame_type}')
    return {'frame_name':frame_name,'header':header,'raw_payload_hex':bytes_to_hex(payload),'decoded':decoded}

def payload_to_table(result: Dict[str, Any]):
    rows=[{'Section':'Trame','Champ':'Type','Valeur':result['frame_name']}]
    header=result.get('header',{})
    for key,label in [('meter_key','Meter Key'),('fw_major','FW major'),('fw_minor','FW minor'),('frame_type','Frame type')]:
        if header.get(key) is not None: rows.append({'Section':'En-tête','Champ':label,'Valeur':header.get(key)})
    for k,v in result['decoded'].items(): rows.append({'Section':'Payload','Champ':k,'Valeur':v})
    return rows
