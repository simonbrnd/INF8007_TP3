import pandas as pd

interventions = pd.read_csv('../data/interventions.tsv', sep="\t")
pdq = pd.read_csv('../data/pdq.csv')
quartsTravail = pd.read_csv('../data/quarts_travail.csv')

nbInterventionsDf = interventions.drop(columns=["DATE_INCIDENT", "CATÉGORIE", "QUART_TRAVAIL"]).groupby("PDQ").count().to_dict()
nbInterventionsDict = {str(key): str(value) for key, value in nbInterventionsDf["ID_INTERVENTION"].items()}