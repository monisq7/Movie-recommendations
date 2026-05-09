import pickle
import requests
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# -------------------------------
# LOAD DATA
# -------------------------------

@st.cache_resource
def load_data():
    movies = pickle.load(open('movie_list.pkl', 'rb'))
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    new = pickle.load(open('movie_data.pkl', 'rb'))
    return movies, similarity, new

movies, similarity, new = load_data()

API_KEY = "8265bd1679663a7ea12ac168da84d2e8"

# -------------------------------
# FETCH MOVIE DETAILS
# -------------------------------

def fetch_movie_details(movie_id):

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"

    try:
        response = requests.get(url)
        data = response.json()

        poster_path = data.get("poster_path")
        poster = (
            f"https://image.tmdb.org/t/p/w500/{poster_path}"
            if poster_path
            else "https://via.placeholder.com/500x750?text=No+Image"
        )

        return {
            "poster": poster,
            "rating": data.get("vote_average", "N/A"),
            "overview": data.get("overview", "No overview available."),
            "release_date": data.get("release_date", "Unknown")
        }

    except:
        return {
            "poster": "https://via.placeholder.com/500x750?text=Error",
            "rating": "N/A",
            "overview": "Error fetching details",
            "release_date": "Unknown"
        }

# -------------------------------
# RECOMMEND MOVIES
# -------------------------------

def recommend(movie):

    index = movies[movies['title'] == movie].index[0]

    distances = sorted(
        list(enumerate(similarity[index])),
        reverse=True,
        key=lambda x: x[1]
    )

    recommended_movies = []

    for i in distances[1:6]:

        movie_id = movies.iloc[i[0]].movie_id
        details = fetch_movie_details(movie_id)

        recommended_movies.append({
            "title": movies.iloc[i[0]].title,
            "poster": details["poster"],
            "rating": details["rating"],
            "overview": details["overview"],
            "release_date": details["release_date"]
        })

    return recommended_movies

# -------------------------------
# CAST BASED RECOMMENDATION
# -------------------------------

def recommend_by_cast(cast_name):

    filtered = new[
        new['cast'].str.contains(
            cast_name,
            case=False,
            na=False
        )
    ]

    filtered = filtered.sort_values(
        by='popularity',
        ascending=False
    ).head(5)

    return filtered[['title', 'popularity']]

# -------------------------------
# UI
# -------------------------------

st.title("🎬 AI Movie Recommender System")
st.markdown("Find similar movies instantly!")

tabs = st.tabs(["🎥 Movie Recommendation", "⭐ Cast Recommendation"])

# -------------------------------
# MOVIE TAB
# -------------------------------

with tabs[0]:

    movie_list = movies['title'].values

    selected_movie = st.selectbox(
        "Search Movie",
        movie_list
    )

    if st.button("Recommend Movies"):

        with st.spinner("Fetching recommendations..."):

            recommendations = recommend(selected_movie)

            cols = st.columns(5)

            for idx, movie in enumerate(recommendations):

                with cols[idx]:

                    st.image(movie["poster"])

                    st.subheader(movie["title"])

                    st.write(f"⭐ Rating: {movie['rating']}")

                    st.caption(
                        movie["overview"][:120] + "..."
                    )

# -------------------------------
# CAST TAB
# -------------------------------

with tabs[1]:

    new['cast'] = new['cast'].astype(str)

    cast_names = (
        new['cast']
        .dropna()
        .str.split(',')
        .explode()
        .str.strip()
        .unique()
    )

    selected_cast = st.selectbox(
        "Select Actor/Actress",
        sorted(cast_names)
    )

    if st.button("Show Cast Movies"):

        results = recommend_by_cast(selected_cast)

        st.subheader(
            f"Popular Movies by {selected_cast}"
        )

        st.dataframe(results)