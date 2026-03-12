import ast
import numpy as np
import pandas as pd
import os 
import tensorflow as tf
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer




import os

# Get path relative to the current file
DATA_DIR = os.path.dirname(os.path.abspath(__file__))










def convert(obj):
    if isinstance(obj, list):
        return obj
    if pd.isna(obj) or obj == "":
        return []

    try:
        return [i['name'] for i in ast.literal_eval(obj)]
    except:
        return []


def convert_cast(obj):
    if isinstance(obj, list):
        return obj[:5]
    if pd.isna(obj) or obj == "":
        return []

    try:
        return [i['name'] for i in ast.literal_eval(obj)[:5]]
    except:
        return []


def convert_crew(obj):
    if pd.isna(obj) or obj == "":
        return []

    if isinstance(obj, list):
        data = obj
    else:
        try:
            data = ast.literal_eval(obj)
        except:
            return []

    for i in data:
        if isinstance(i, dict) and i.get('job') == 'Director':
            return [i.get('name')]
    
    return []

    for i in data:
        if i.get('job') == 'Director':
            return [i.get('name')]
    return []


def clean_column(col):
    return col.apply(
        lambda x: np.nan
        if (
            x == 0 or
            x == "" or
            x==[] or x=="[]" or 
            (isinstance(x, (list, str)) and len(x) == 0)
        )
        else x
    )



def preprocessing():
    
    movies=pd.read_csv(os.path.join(DATA_DIR, 'tmdb_movies_api.csv'))
    movies_crew=pd.read_csv(os.path.join(DATA_DIR, 'tmdb_credits_api.csv'))   
    movies_data= movies.merge(movies_crew, on='title')

    




    movies_data = movies_data[
    (movies_data['vote_average'] > 0.0) &
    (movies_data['genres'].apply(len) > 2) & (movies_data['keywords'].apply(len) > 2) & movies_data['original_language'].isin(['hi', 'mr','en'])
    ]
    
    df=movies_data[['genres','movie_id','title','overview','cast','crew','keywords']].copy()
   
    for col in df.columns:
        df[col] = clean_column(df[col])

    df=df.dropna()
    df = df.reset_index(drop=True)
    df[['genres','cast','crew','keywords']] = df[['genres','cast','crew','keywords']].fillna("[]")   
    df['genres']=df['genres'].apply(convert)
    df['keywords']=df['keywords'].apply(convert)
    df['crew']=df['crew'].apply(convert_crew)
    df['cast']=df['cast'].apply(convert_cast)
    df['overview']=df['overview'].apply(
    lambda x: x.split() if isinstance(x, str) else [])

    movies = df[['movie_id', 'title','cast','genres','overview']].copy()

    df['genres']=df['genres'].apply(lambda x :[i.replace(" ","") for i in x])
    df['cast']=df['cast'].apply(lambda x :[i.replace(" ","") for i in x])
    df['crew']=df['crew'].apply(lambda x :[i.replace(" ","") for i in x])
    #collecting alls collumns to single tags
    
    df['tags'] = df['genres'] + df['cast'] +df['overview']+ df['crew']
    df['tags']=df['tags'].apply(lambda x : " ".join(x))
    df['tags']=df['tags'].apply(lambda x : x.lower())
    
    # Returning both the original DataFrame with tags and the movies DataFrame for the API
    return df, movies

def get_similarity(df):

    ps = PorterStemmer()

    def stem(text):
        return " ".join([ps.stem(word) for word in text.split()])

    df['tags'] = df['tags'].apply(stem)

    cv = CountVectorizer(max_features=5000, stop_words='english',ngram_range=(1,2))

    vectors = cv.fit_transform(df['tags']).toarray()

    # normalize safely
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    vectors = vectors / norms

    movie_tensor = tf.convert_to_tensor(vectors, dtype=tf.float32)

    return movie_tensor, cv

