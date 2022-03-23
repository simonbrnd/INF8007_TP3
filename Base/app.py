import pandas as pd
from flask import Flask, render_template, request, redirect
from datetime import datetime
import json

app = Flask(__name__)

INTERVENTIONS_FILE_PATH = 'data/interventions.tsv'
PDQ_FILE_PATH = 'data/pdq.csv'
CATEGORIE_FILE_PATH = 'data/catégoriesInterventions.csv'
QDT_FILE_PATH = 'data/quarts_travail.csv'

@app.route('/', methods=['POST', 'GET'])
def base_tp3():

    interventions = pd.read_csv(INTERVENTIONS_FILE_PATH, sep="\t")
    
    Date_incident = pd.to_datetime(interventions["DATE_INCIDENT"])
    
    pdq = pd.read_csv(PDQ_FILE_PATH, sep=";")
    categorie = pd.read_csv(CATEGORIE_FILE_PATH, sep=";")
    qdt = pd.read_csv(QDT_FILE_PATH, sep=";")
    
    nbInterventionsDf = interventions.drop(columns=["DATE_INCIDENT", "CATÉGORIE", "QUART_TRAVAIL"]).groupby("PDQ").count()
    nbInterventionsDf = nbInterventionsDf.rename(columns={'ID_INTERVENTION':'NB_INTERVENTION'})
    #catDict={}
    #for row in categorie.itertuples()
    #print(json.dumps(categorie.set_index("LIBELLÉ").squeeze().to_dict(),ensure_ascii=False))
    interventionsParPoste = pdq.set_index('PDQ').join(nbInterventionsDf)


    return render_template('Base_TP3.html', interventionsparPoste=interventionsParPoste, nbInterventionsParPDQ=nbInterventionsDf.to_dict(),DateMin=Date_incident.min(),DateMax=Date_incident.max().strftime("%Y-%m-%d"),PDQ=list(nbInterventionsDf.index),cat=categorie,Quart=qdt,catIntervention=json.dumps(categorie.set_index("LIBELLÉ").squeeze().to_dict(),ensure_ascii=False))

if __name__ == "__main__":
    app.run(host='localhost', port=5555, debug=False)