import json
from typing import Dict, Any

# Soglie di frequenza cardiaca separate per sesso e fasce d'età
# Soglie basate su linee guida cliniche:
# - Differenza M/F: soglie femminili leggermente più alte (+5 bpm)
# Fasce di età:
#   <18, 18-25, 26-40, 41-60, 60+
THRESHOLDS = {
    'M': {
        '<18': {
            'bradicardia_critica': 40,
            'bradicardia': 70,
            'normale_min': 70,
            'normale_max': 100,
            'tachicardia': 100,
            'tachicardia_moderata': 120,
            'tachicardia_critica': 150
        },
        '18-25': {
            'bradicardia_critica': 40,
            'bradicardia': 60,
            'normale_min': 60,
            'normale_max': 100,
            'tachicardia': 100,
            'tachicardia_moderata': 120,
            'tachicardia_critica': 150
        },
        '26-40': {
            'bradicardia_critica': 40,
            'bradicardia': 60,
            'normale_min': 60,
            'normale_max': 100,
            'tachicardia': 100,
            'tachicardia_moderata': 120,
            'tachicardia_critica': 150
        },
        '41-60': {
            'bradicardia_critica': 40,
            'bradicardia': 60,
            'normale_min': 60,
            'normale_max': 100,
            'tachicardia': 100,
            'tachicardia_moderata': 120,
            'tachicardia_critica': 150
        },
        '60+': {
            'bradicardia_critica': 40,
            'bradicardia': 60,
            'normale_min': 60,
            'normale_max': 100,
            'tachicardia': 100,
            'tachicardia_moderata': 120,
            'tachicardia_critica': 150
        }
    },
    'F': {
        '<18': {
            'bradicardia_critica': 45,
            'bradicardia': 75,
            'normale_min': 75,
            'normale_max': 105,
            'tachicardia': 105,
            'tachicardia_moderata': 125,
            'tachicardia_critica': 155
        },
        '18-25': {
            'bradicardia_critica': 45,
            'bradicardia': 65,
            'normale_min': 65,
            'normale_max': 105,
            'tachicardia': 105,
            'tachicardia_moderata': 125,
            'tachicardia_critica': 155
        },
        '26-40': {
            'bradicardia_critica': 45,
            'bradicardia': 65,
            'normale_min': 65,
            'normale_max': 105,
            'tachicardia': 105,
            'tachicardia_moderata': 125,
            'tachicardia_critica': 155
        },
        '41-60': {
            'bradicardia_critica': 45,
            'bradicardia': 65,
            'normale_min': 65,
            'normale_max': 105,
            'tachicardia': 105,
            'tachicardia_moderata': 125,
            'tachicardia_critica': 155
        },
        '60+': {
            'bradicardia_critica': 45,
            'bradicardia': 65,
            'normale_min': 65,
            'normale_max': 105,
            'tachicardia': 105,
            'tachicardia_moderata': 125,
            'tachicardia_critica': 155
        }
    }
}


def get_age_group(age: int) -> str:
    if age < 18:
        return '<18'
    elif age <= 25:
        return '18-25'
    elif age <= 40:
        return '26-40'
    elif age <= 60:
        return '41-60'
    else:
        return '60+'


def analyze_hr(bpm_mean: float, thresholds: Dict[str, float]) -> str:
    if bpm_mean < thresholds['bradicardia_critica']:
        return 'severe_bradycardia'
    if bpm_mean < thresholds['bradicardia']:
        return 'moderate_bradycardia'
    if thresholds['normale_min'] <= bpm_mean <= thresholds['normale_max']:
        return 'normal'
    if thresholds['tachicardia'] < bpm_mean <= thresholds['tachicardia_moderata']:
        return 'tachicardia'
    if thresholds['tachicardia_moderata'] < bpm_mean <= thresholds['tachicardia_critica']:
        return 'moderate_tachycardia'
    if bpm_mean > thresholds['tachicardia_critica']:
        return 'severe_tachycardia'
    return 'null'


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    if isinstance(event, str):
        event = json.loads(event)

    patient_id  = event.get('patient_id')
    age      = event.get('age')
    sex      = event.get('sex', '').upper()
    bpm_mean = event.get('bpm_mean')
    bpm_values = event.get('bpm_values')
    ts = event.get('ts')

    if not patient_id or age is None or sex not in THRESHOLDS or bpm_mean is None:
        raise ValueError("Occorrono patient_id, age, sex ('M'/'F') e bpm_mean validi")

    age_group = get_age_group(age)
    thresholds = THRESHOLDS[sex][age_group]
    anomaly = analyze_hr(bpm_mean, thresholds)

    return {
        'patient_id':    patient_id,
        'age':        age,
        'sex':        sex,
        'age_group':  age_group,
        'bpm_mean':   str(bpm_mean),
        'bpm_values': str(bpm_values),
        'anomaly':    anomaly,
        'ts': ts
    }
