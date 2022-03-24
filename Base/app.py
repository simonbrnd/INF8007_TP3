from re import I
import pandas as pd
from flask import Flask, render_template, request, redirect
from datetime import datetime
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
    
    nbInterventionsDf = interventions.drop(columns=["DATE_INCIDENT", "CATÉGORIE", "QUART_TRAVAIL"]).groupby("PDQ").count()
    nbInterventionsDf = nbInterventionsDf.rename(columns={'ID_INTERVENTION':'NB_INTERVENTION'})
    nbInterventionsParPDQ = nbInterventionsDf.to_dict()

    interventionsParPoste = pdq.set_index('PDQ').join(nbInterventionsDf)

    PDQ = list(nbInterventionsDf.index)
    catIntervention = json.dumps(categorie.set_index("LIBELLÉ").squeeze().to_dict(),ensure_ascii=False)
    emplacementsPDQ = json.dumps(pdq.set_index("PDQ").squeeze().to_dict(),ensure_ascii=False)

    lastId = interventions["ID_INTERVENTION"].values[-1]

    return (interventionsParPoste, nbInterventionsParPDQ, DateMin, DateMax, PDQ, categorie, qdt, catIntervention, emplacementsPDQ, lastId)


def valid_intervention_number(id, interventions_pd) :
    #Regarder si l'id intervention est inscrit dans le fichier, utile pour les onglet remove et modify
    interventions_pd["ID_INTERVENTION"] = interventions_pd["ID_INTERVENTION"].apply(lambda x: str(x))
    interventions_pd = interventions_pd.set_index("ID_INTERVENTION")
    validInterventionNb = id in interventions_pd.index
    return validInterventionNb


@app.route('/', methods=['POST', 'GET'])
def index():
    # Initialisation
    (interventionsParPoste, nbInterventionsParPDQ, DateMin, DateMax, PDQ, categorie, qdt, catIntervention, emplacementsPDQ, lastId) = compute_vars_for_rending_template()
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
                            lastId=lastId,
                            invalid = None,
                            val=json.dumps(False),
                            modifyNoIntervention=json.dumps(None),
                            modifyInfos=None)


@app.route("/add", methods=['POST', 'GET']) 
def add() :
    # Méthode pour ajouter un rapport, compléter les données et afficher une pop-up
    if request.method == 'POST' and len(request.form) > 0 :
        interventions_file = open(file=INTERVENTIONS_FILE_PATH, mode='r', encoding='UTF-8')
        last_line = interventions_file.readlines()[-1]
        new_id = int(last_line.split("\t")[0]) + 1
        print("new id :", new_id)
        interventions_file = open(file=INTERVENTIONS_FILE_PATH, mode='a', encoding='UTF-8')
        interventions_file.write(f"{new_id}\t{request.form['add_date_incident']}\t{request.form['add_cat_intervention']}\t{request.form['add_pdq_nb']}\t{request.form['add_quart']}\n")
        interventions_file.close()
        print("written")

        (interventionsParPoste, nbInterventionsParPDQ, DateMin, DateMax, PDQ, categorie, qdt, catIntervention, emplacementsPDQ, lastId) = compute_vars_for_rending_template()

        return render_template("add.html",
                        interventionsparPoste=interventionsParPoste, 
                        nbInterventionsParPDQ=nbInterventionsParPDQ,
                        DateMin=DateMin,
                        DateMax=DateMax,
                        PDQ=PDQ,
                        cat=categorie,
                        Quart=qdt,
                        catIntervention=catIntervention,
                        emplacementsPDQ=emplacementsPDQ,
                        lastId=lastId,
                        invalid=None,
                        validModify=json.dumps(False),
                        modifyNoIntervention=None,
                        modifyInfos=None)

    return redirect("/#nav-add")



@app.route("/modify", methods=['POST'])
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

        (interventionsParPoste, nbInterventionsParPDQ, DateMin, DateMax, PDQ, categorie, qdt, catIntervention, emplacementsPDQ, lastId) = compute_vars_for_rending_template()

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
                                lastId=lastId,
                                invalid=id_to_modify,
                                validModify=json.dumps(validModify),
                                modifyNoIntervention=json.dumps(modifyNoIntervention),
                                modifyInfos=line)


if __name__ == "__main__":
    app.run(host='localhost', port=5555, debug=False)