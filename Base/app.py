from re import I
import pandas as pd
from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta
import time
import json

app = Flask(__name__)

INTERVENTIONS_FILE_PATH = 'data/interventions.tsv'
PDQ_FILE_PATH = 'data/pdq.csv'
CATEGORIE_FILE_PATH = 'data/catégoriesInterventions.csv'
QDT_FILE_PATH = 'data/quarts_travail.csv'


def compute_vars_for_rending_template() :
    # Fonction appelée pour recalculer l'ensemble des variables avant un render_template
    interventions = pd.read_csv(INTERVENTIONS_FILE_PATH, sep="\t")
    Date_incident = pd.to_datetime(interventions["DATE_INCIDENT"])
    DateMin=Date_incident.min()
    DateMax=Date_incident.max().strftime("%Y-%m-%d")
    
    pdq = pd.read_csv(PDQ_FILE_PATH, sep=";")
    categorie = pd.read_csv(CATEGORIE_FILE_PATH, sep=";")
    qdt = pd.read_csv(QDT_FILE_PATH, sep=";")

    current_datetime = datetime.now()
    current_hour_in_seconds = current_datetime.hour*3600 + current_datetime.minute*60 + current_datetime.second
    if current_hour_in_seconds >= 60  and current_hour_in_seconds <= 28859 :
        current_quart = "nuit"
    elif current_hour_in_seconds <= 59  or current_hour_in_seconds >= 57660 :
        current_quart = "soir"
    else :
        current_quart = "jour"
    
    print("Current quart :", current_quart)

    nbInterventionsDf = interventions.drop(columns=["DATE_INCIDENT", "CATÉGORIE", "QUART_TRAVAIL"]).groupby("PDQ").count()
    nbInterventionsDf = nbInterventionsDf.rename(columns={'ID_INTERVENTION':'NB_INTERVENTION'})
    nbInterventionsParPDQ = nbInterventionsDf.to_dict()

    interventionsParPoste = pdq.set_index('PDQ').join(nbInterventionsDf)

    PDQ = list(nbInterventionsDf.index)
    catIntervention = json.dumps(categorie.set_index("LIBELLÉ").squeeze().to_dict(),ensure_ascii=False)
    emplacementsPDQ = json.dumps(pdq.set_index("PDQ").squeeze().to_dict(),ensure_ascii=False)

    return (interventionsParPoste, nbInterventionsParPDQ, DateMin, DateMax, PDQ, categorie, qdt, catIntervention, emplacementsPDQ, current_quart)


def valid_intervention_number(id, interventions_pd) :
    #Regarder si l'id intervention est inscrit dans le fichier, utile pour les onglet remove et modify
    interventions_pd["ID_INTERVENTION"] = interventions_pd["ID_INTERVENTION"].apply(lambda x: str(x))
    interventions_pd = interventions_pd.set_index("ID_INTERVENTION")
    validInterventionNb = id in interventions_pd.index
    return validInterventionNb


@app.route('/', methods=['POST', 'GET'])
def index():
    print("Index function called")
    # Initialisation
    (interventionsParPoste, nbInterventionsParPDQ, DateMin, DateMax, PDQ, categorie, qdt, catIntervention, emplacementsPDQ, current_quart) = compute_vars_for_rending_template()
    return render_template('Base_TP3.html', 
                            interventionsparPoste=interventionsParPoste, 
                            nbInterventionsParPDQ=nbInterventionsParPDQ,
                            DateMin=DateMin,
                            DateMax=DateMax,
                            PDQ=PDQ,
                            cat=categorie,
                            Quart=qdt,
                            catIntervention=catIntervention,
                            emplacementsPDQ=emplacementsPDQ,
                            invalid = None,
                            val=json.dumps(False),
                            modifyNoIntervention=json.dumps(None),
                            modifyInfos=None,
                            currentQuart = current_quart)


@app.route("/?add_pdq_nb=<int:pdq_id>&add_cat_intervention=<string:cat>&add_date_incident=<string:intervention_date>&add_quart=<string:quart>&add-new-intervention=#nav-add", methods=['GET']) 
def add(pdq_id, cat, intervention_date, quart) :
    print("Into the add method !")
    # Méthode pour ajouter un rapport, compléter les données et renvoyer vers le template pour afficher la pop-up
    if request.method == 'GET' :
        print("GET !")
        interventions_file = open(file=INTERVENTIONS_FILE_PATH, mode='r', encoding='UTF-8')
        last_line = interventions_file.readlines()[-1]
        new_id = int(last_line.split("\t")[0]) + 1
        print("new id :", new_id)
        interventions_file = open(file=INTERVENTIONS_FILE_PATH, mode='a', encoding='UTF-8')
        interventions_file.write(f"{new_id}\t{intervention_date}\t{cat}\t{pdq_id}\t{quart}\n")
        interventions_file.close()
        print("written")
        return render_template("add.html", lastId=new_id)


"""@app.route("/modify", methods=['POST'])
def modify() :
    if request.method == 'POST' and len(request.form) > 0 :
        id_to_modify = request.form['modify_no_intervention']
        interventions_pd = pd.read_csv(INTERVENTIONS_FILE_PATH, sep="\t")
        validModify = valid_intervention_number(id_to_modify, interventions_pd)

        print("Valid number? :", validModify)

        if validModify :
            file = "Base_TP3.html"
            modifyNoIntervention = id_to_modify
            interventions_pd = interventions_pd.set_index("ID_INTERVENTION")
            line = interventions_pd.loc[id_to_modify]
            print("Id to modify :", id_to_modify)
            print(type(id_to_modify))

        else :
            file = "error_modify.html" 
            modifyNoIntervention = None
            line = None

        (interventionsParPoste, nbInterventionsParPDQ, DateMin, DateMax, PDQ, categorie, qdt, catIntervention, emplacementsPDQ) = compute_vars_for_rending_template()

        return render_template(file,
                                interventionsparPoste=interventionsParPoste, 
                                nbInterventionsParPDQ=nbInterventionsParPDQ,
                                DateMin=DateMin,
                                DateMax=DateMax,
                                PDQ=PDQ,
                                cat=categorie,
                                Quart=qdt,
                                catIntervention=catIntervention,
                                emplacementsPDQ=emplacementsPDQ,
                                invalid=id_to_modify,
                                validModify=json.dumps(validModify),
                                modifyNoIntervention=json.dumps(modifyNoIntervention),
                                modifyInfos=line)
"""

if __name__ == "__main__":
    app.run(host='localhost', port=5555, debug=False)