import pickle
import os
import pandas as pd
import json
from .models import *

# Load from file
def TopItemForUser(userId,n):
    print(os.getcwd())
    pkl_filename = "svd_model.pkl"
    with open(pkl_filename, 'rb') as file:
        pickle_model = pickle.load(file)

    #unique item id in the dataset
    df_item = pd.DataFrame.from_records(Item.objects.all().values('title', 'price', 'large_image_url', 'asin','slug'))
    df_item = df_item.reset_index()
    df_item['Estimate_Score'] = df_item['asin'].apply(lambda x: pickle_model.predict(userId, x).est)

    df_item = df_item.sort_values('Estimate_Score', ascending=False)

    df_item = df_item[:n]
    print(df_item.head(15))
    # parsing the DataFrame in json format.
    json_records = df_item.reset_index().to_json(orient='records')
    data = []
    data = json.loads(json_records)
    return data