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
    
    nbInterventionsDf = interventions.drop(columns=["DATE_INCIDENT", "CATÉGORIE", "QUART_TRAVAIL"]).groupby("PDQ").count()
    nbInterventionsDf = nbInterventionsDf.rename(columns={'ID_INTERVENTION':'NB_INTERVENTION'})
    nbInterventionsParPDQ = nbInterventionsDf.to_dict()

    interventionsParPoste = pdq.set_index('PDQ').join(nbInterventionsDf)

    catIntervention = json.dumps(categorie.set_index("LIBELLÉ").squeeze().to_dict(),ensure_ascii=False)
    emplacementsPDQ = json.dumps(pdq.set_index("PDQ").squeeze().to_dict(),ensure_ascii=False)

    return (interventionsParPoste, nbInterventionsParPDQ, DateMin, DateMax, pdq, categorie, qdt, catIntervention, emplacementsPDQ, current_quart)


def valid_intervention_number(id) :
    #Regarder si l'id intervention est inscrit dans le fichier, utile pour les onglet remove et modify
    interventions_pd = pd.read_csv(INTERVENTIONS_FILE_PATH, sep="\t")
    interventions_pd["ID_INTERVENTION"] = interventions_pd["ID_INTERVENTION"].apply(lambda x: str(x))
    interventions_pd = interventions_pd.set_index("ID_INTERVENTION")
    validInterventionNb = id in interventions_pd.index
    return validInterventionNb

# Méthode pour ajouter un rapport, compléter les données et renvoyer vers le template pour afficher la pop-up
def add(url) :
    print("Into the add method !")
    # Découpage du path pour récupérer l'ensemble des informations
    split_url = url.split("=")
    pdq_id = split_url[1].split("&")[0]
    cat = split_url[2].split("&")[0].replace("+", " ")
    intervention_date = split_url[3].split("&")[0]
    quart = split_url[4].split("&")[0]
    # Ajout du nouvel élément
    interventions_file = open(file=INTERVENTIONS_FILE_PATH, mode='r', encoding='UTF-8')
    last_line = interventions_file.readlines()[-1]
    new_id = int(last_line.split("\t")[0]) + 1
    interventions_file = open(file=INTERVENTIONS_FILE_PATH, mode='a', encoding='UTF-8')
    interventions_file.write(f"{new_id}\t{intervention_date}\t{cat}\t{pdq_id}\t{quart}\n")
    interventions_file.close()
    print("written")
    return {"ID_INTERVENTION" : new_id}, "add"


def modify(url) :
    # On récupère l'id requêté
    id = request.url.split("modify_no_intervention=")[-1].split("&")[0]
    interventions_pd = pd.read_csv(INTERVENTIONS_FILE_PATH, sep="\t")

    # 1ère étape
    if not "/?update-intervention" in request.url :

        # Cas d'un id invalide
        if not valid_intervention_number(id) :
            return {"ID_INTERVENTION" : id}, "invalid_modify"
        # Cas d'un id valide
        else :
            print("This is a valid modification, infos will appear")
            categorie_pd = pd.read_csv(CATEGORIE_FILE_PATH, sep=";")
            pdq_pd = pd.read_csv(PDQ_FILE_PATH, sep=";")
            interventions_pd = pd.merge(interventions_pd, categorie_pd, how='left', left_on='CATÉGORIE', right_on='LIBELLÉ')
            interventions_pd = pd.merge(interventions_pd, pdq_pd, how='left', left_on='PDQ', right_on='PDQ')
            interventions_pd = interventions_pd.set_index("ID_INTERVENTION")
            modifyInfos = interventions_pd.loc[int(id)].to_dict()
            modifyInfos["ID_INTERVENTION"] = id
            print("Modify infos :", modifyInfos)
            return modifyInfos, "valid_modify"


    # Cas de la soumission après la 1ère étape, on transforme nos données 
    else :
        split_url = url.split("=")
        interventions_pd.loc[interventions_pd.ID_INTERVENTION == int(id), 'DATE_INCIDENT'] = split_url[3].split("&")[0]
        interventions_pd.loc[interventions_pd.ID_INTERVENTION == int(id), 'CATÉGORIE'] = split_url[4].split("&")[0].replace("%20", " ").replace("%2F", "/")
        interventions_pd.loc[interventions_pd.ID_INTERVENTION == int(id), 'PDQ'] = split_url[5].split("&")[0]
        interventions_pd.loc[interventions_pd.ID_INTERVENTION == int(id), 'QUART_TRAVAIL'] = split_url[6]

        print(interventions_pd.loc[interventions_pd.ID_INTERVENTION == int(id)])

        # Rewrite the df
        interventions_pd.to_csv(INTERVENTIONS_FILE_PATH, sep="\t", index=False)

        return {"ID_INTERVENTION" : str(id)}, "modify_done"


def remove(url) :
    interventions_pd = pd.read_csv(INTERVENTIONS_FILE_PATH, sep="\t")
    # 1ère étape : recherche d'un numéro de rapport
    if "remove_no_intervention" in url :
        id = url.split("remove_no_intervention=")[1].split("&")[0]
        # Cas d'un id invalide
        if not valid_intervention_number(id) :
            return {"ID_INTERVENTION" : id}, "invalid_remove"
        # Cas d'un id valid
        else :
            print("This is a valid remove, infos will appear")
            pdq_pd = pd.read_csv(PDQ_FILE_PATH, sep=";")
            interventions_pd = pd.merge(interventions_pd, pdq_pd, how='left', left_on='PDQ', right_on='PDQ')
            interventions_pd = interventions_pd.set_index("ID_INTERVENTION")
            removeInfos = interventions_pd.loc[int(id)].to_dict()
            removeInfos["ID_INTERVENTION"] = id
            print("Remove Infos :", removeInfos)
            return removeInfos, "valid_remove"

    # 2ème étape : suppression de l'id valide
    elif "no_intervention_to_remove" in url :
        id = url.split("no_intervention_to_remove=")[1].split("&")[0]
        interventions_pd.drop(interventions_pd[interventions_pd['ID_INTERVENTION'] == int(id)].index, inplace = True)
        interventions_pd.to_csv(INTERVENTIONS_FILE_PATH, sep="\t", index=False)
        
        return {"ID_INTERVENTION" : id}, "remove_done"

@app.route('/', methods=['POST', 'GET'])
def index():
    # Mode et templateValue par défault
    mode = None
    templateValue = None

    # Ajouter un incident 
    if "add_pdq_nb" in request.url :
        templateValue, mode = add(request.url)

    # Modifier un incident
    elif "modify_no_intervention" in request.url :
        templateValue, mode = modify(request.url) 

    # Supprimer un incident
    elif "remove" in request.url :
        templateValue, mode = remove(request.url)

    # Recalcul de l'ensemble des valeurs du template    
    (interventionsParPoste, nbInterventionsParPDQ, DateMin, DateMax, pdq, categorie, qdt, catIntervention, emplacementsPDQ, current_quart) = compute_vars_for_rending_template()

    return render_template('Base_TP3.html', 
                            interventionsparPoste=interventionsParPoste, 
                            nbInterventionsParPDQ=nbInterventionsParPDQ,
                            DateMin=DateMin,
                            DateMax=DateMax,
                            pdq=pdq,
                            cat=categorie,
                            Quart=qdt,
                            catIntervention=catIntervention,
                            emplacementsPDQ=emplacementsPDQ,
                            currentQuart = current_quart,
                            mode=mode,
                            templateValue=templateValue)


if __name__ == "__main__":
    app.run(host='localhost', port=5555, debug=True)