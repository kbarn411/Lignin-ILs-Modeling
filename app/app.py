from pywebio import start_server
from pywebio.platform.tornado_http import start_server as start_http_server
from pywebio import start_server as start_ws_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import *
from pywebio.pin import *
import joblib
import pandas as pd
from mordred import Calculator
from mordred.Autocorrelation import AATSC, MATS
from mordred.Chi import Chi
from mordred.MolecularDistanceEdge import MolecularDistanceEdge
from rdkit import Chem
import math
import xgboost

def predict_yield():
    """Prediction of lignin extraction yield with ionic liquid"""
    put_markdown("# Predict yield of lignin extraction with ionic liquid")

    info = input_group("Enter the details about the IL and process",[
    input('Provide percentage of hemicellulose in biomass sample', name='perc_hemicellulose', type='float', value=19.8),

    input('Provide temperature in deg. Celsius', name='temp', type='float', value=90),
    input('Provide time in hours', name='time', type='float', value=24),
    input('Provide concentration of ionic liquid', name='IL_concentration', type='float',  value=1.0),

    input('Provide SMILES for cation of IL', name='smi_cat',  value='OCC[N+](C)(C)C'),
    input('Provide SMILES for anion of IL', name='smi_ani', value='NCC(=O)[O-]'),
    ])
    confirm = actions('Predict yield!', ['predict', 'cancel'])

    if confirm == 'predict':
        try:
            put_text(f"Calculation in progress...")
            result_to_print = predict(info)
            
            put_text(f"""Prediction for 
                     percentage of hemicellulose: {info['perc_hemicellulose']}, 
                     IL cation: {info['smi_cat']}, IL anion: {info['smi_ani']},
                     temperature: {info['temp']}, time: {info['time']}, IL concentration: {info['IL_concentration']}""")
            put_text(f"Predicted lignin extraction yield: {result_to_print:.1f} %")
        except (SyntaxError, TypeError) as e:
            put_text("Incorrect data")
            put_text(e)
        finally:
            pass
    put_button("Return to first screen", onclick=start) #lambda : run_js('window.location.reload()'))

def predict(info):
    # while True:
    #     changed = pin_wait_change('perc_hemicellulose', 'temp', 'time', 'IL_concentration', 'smi_cat', 'smi_ani')
        model = joblib.load('xgb_model.joblib')
        # with use_scope('integ', clear=True):
        calc_c = Calculator([
            AATSC(3, 'i'),
            MATS(3, 'pe'),
            Chi('path', 5, 'd', True)
        ], ignore_3D=True)
        calc_a = Calculator([
            MolecularDistanceEdge(1, 1, 'O')
        ], ignore_3D=True)
        smi_cat_str = str(info['smi_cat'])
        smi_ani_str = str(info['smi_ani'])
        descs_cat = calc_c.pandas([Chem.MolFromSmiles(smi_cat_str)], nproc=1)
        descs_ani = calc_a.pandas([Chem.MolFromSmiles(smi_ani_str)], nproc=1)
        desc_c1 = float(descs_cat['AATSC3i'].values[0])
        if math.isnan(desc_c1): desc_c1 = -0.2257644075526302
        desc_c2 = float(descs_cat['MATS3pe'].values[0])
        if math.isnan(desc_c2): desc_c2 = -0.17342505347089532
        desc_c3 = float(descs_cat['AXp-5d'].values[0])
        if math.isnan(desc_c3): desc_c3 = 0.11160256837383413
        desc_a1 = float(descs_ani['MDEO-11'].values[0])
        if math.isnan(desc_a1): desc_a1 = 0.972900796515524

        input_dict = {
            'c_mordred_AATSC3i' : [(desc_c1 + 0.4352925459641111) / (-0.1518963344947402 + 0.4352925459641111)],
            'c_mordred_MATS3pe' : [(desc_c2 + 0.2787736716308144) / (-0.0667995963594728 + 0.2787736716308144)],
            'c_mordred_AXp-5d' : [(desc_c3 - 0.1019655064280505) / (0.1443375672974064 - 0.1019655064280505)],
            'a_mordred_MDEO-11' : [(desc_a1 - 0.499) / (3 - 0.499)],
            'perc_hemicellulose' : [(info['perc_hemicellulose'] - 17.5) / (33.35 - 17.5)],
            'il_conc' : [(info['IL_concentration'] - 0.008) / (-0.152 - 0.008)],
            'temp' : [(info['temp'] - 50) / (240 - 50)],
            'time' : [(info['time'] - 0.03333) / (72 - 0.03333)],
        }
        input_df = pd.DataFrame.from_dict(input_dict)
        result = model.predict(input_df)
        result_to_print = round(result[0], 3) * 100
        return result_to_print

def start():
    predict_yield()

if __name__ == '__main__':
    start()