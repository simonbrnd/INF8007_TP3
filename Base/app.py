import pandas as pd
from flask import Flask, render_template, request, redirect


app = Flask(__name__)

INTERVENTIONS_FILE_PATH = 'data/interventions.tsv'
PDQ_FILE_PATH = 'data/pdq.csv'

@app.route('/', methods=['POST', 'GET'])
def base_tp3():

    interventions = pd.read_csv(INTERVENTIONS_FILE_PATH, sep="\t")
    pdq = pd.read_csv(PDQ_FILE_PATH, sep=";")

    nbInterventionsDf = interventions.drop(columns=["DATE_INCIDENT", "CATÉGORIE", "QUART_TRAVAIL"]).groupby("PDQ").count()
    nbInterventionsDf = nbInterventionsDf.rename(columns={'ID_INTERVENTION':'NB_INTERVENTION'})
    interventionsParPoste = pdq.set_index('PDQ').join(nbInterventionsDf)

    print(interventionsParPoste)

    return render_template('Base_TP3.html', interventionsparPoste=interventionsParPoste)

if __name__ == "__main__":
    app.run(host='localhost', port=5555, debug=False)