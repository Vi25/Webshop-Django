#import all the necessary packages.
from PIL import Image
import requests
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import warnings
# from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import math
import time
import re
import os
# import seaborn as sns
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
import sklearn.metrics as metrics
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import pairwise_distances
from matplotlib import gridspec
from scipy.sparse import hstack
import plotly
import plotly.figure_factory as ff
from plotly.graph_objs import Scatter, Layout
from .models import *

plotly.offline.init_notebook_mode(connected=True)
warnings.filterwarnings("ignore")


stop_words = set(stopwords.words('english'))
data = pd.DataFrame()

def nlp_preprocessing(total_text, index, column):
    if type(total_text) is not int:
        string = ""
        for words in total_text.split():
            # remove the special chars in review like '"#$@!%^&*()_+-~?>< etc.
            word = ("".join(e for e in words if e.isalnum()))
            # Conver all letters to lower-case
            word = word.lower()
            # stop-word removal
            if not word in stop_words:
                string += word + " "
        data[column][index] = string

def n_containing(word):
    # return the number of documents which had the given word
    return sum(1 for blob in data['title'] if word in blob.split())

def idf(word):
    # idf = log(#number of docs / #number of docs which had the given word)
    return math.log(data.shape[0] / (n_containing(word)))


def find_doc_id(text):
    string = ""
    for words in text.split():
        # remove the special chars in review like '"#$@!%^&*()_+-~?>< etc.
        word = ("".join(e for e in words if e.isalnum()))
        # Conver all letters to lower-case
        word = word.lower()
        # stop-word removal
        if not word in stop_words:
            string += word + " "

    doc_id = -1
    for i in range(data['title'].shape[0]):
        if data['title'].iloc[i] == string:
            doc_id = i
    return doc_id

def recommendation(Iname, num_results, models_name):
    # data = pd.DataFrame(list(Item.objects.all()))
    global data
    data = pd.DataFrame.from_records(Item.objects.all().values('title', 'price', 'large_image_url','id','slug'))

    #     data = pd.DataFrame.from_records(
    #         Item.objects.all(), columns=['title', 'price', 'large_image_url']
    #     )

    # NLTK download stop words. [RUN ONLY ONCE]
    # nltk.download('stopwords')
    for index, row in data.iterrows():
        nlp_preprocessing(row['title'], index, 'title')

    doc_id = find_doc_id(Iname)

    if models_name == 'BoW':
        title_vectorizer = CountVectorizer()
        title_features = title_vectorizer.fit_transform(data['title'])
        pairwise_dist = pairwise_distances(title_features, title_features[doc_id])
    elif models_name == 'tf-idf':
        tfidf_title_vectorizer = TfidfVectorizer(min_df=0)
        tfidf_title_features = tfidf_title_vectorizer.fit_transform(data['title'])
        pairwise_dist = pairwise_distances(tfidf_title_features, tfidf_title_features[doc_id])
    elif models_name == 'idf':
        idf_title_vectorizer = CountVectorizer()
        idf_title_features = idf_title_vectorizer.fit_transform(data['title'])

        # we need to convert the values into float
        idf_title_features = idf_title_features.astype(np.float)

        for i in idf_title_vectorizer.vocabulary_.keys():
            # for every word in whole corpus we will find its idf value
            idf_val = idf(i)

            # to calculate idf_title_features we need to replace the count values with the idf values of the word
            # idf_title_features[:, idf_title_vectorizer.vocabulary_[i]].nonzero()[0] will return all documents in which the word i present
            for j in idf_title_features[:, idf_title_vectorizer.vocabulary_[i]].nonzero()[0]:
                # we replace the count values of word i in document j with  idf_value of word i
                # idf_title_features[doc_id, index_of_word_in_courpus] = idf value of word
                idf_title_features[j, idf_title_vectorizer.vocabulary_[i]] = idf_val

        pairwise_dist = pairwise_distances(idf_title_features, idf_title_features[doc_id])



    # np.argsort will return indices of the smallest distances
    indices = np.argsort(pairwise_dist.flatten())[0:num_results + 1]

    # data frame indices of the smallest distace's
    df_indices = list(data.index[indices])

    dict_item = {}
    for i in range(1, len(indices)):
        # we will pass 1. doc_id, 2. title1, 3. title2, url, model
        dict_item[i] = {'id': data['id'].loc[df_indices[i]], 'title': data['title'].loc[df_indices[i]], 'price': data['price'].loc[df_indices[i]], 'large_image_url': data['large_image_url'].loc[df_indices[i]],'slug': data['slug'].loc[df_indices[i]] }


    del data, doc_id, df_indices
    return dict_item





