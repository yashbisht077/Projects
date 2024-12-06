import pandas as pd
import streamlit as st
import pickle
import requests
import csv

st.set_page_config(layout="wide")

# Load data from pickle file
movie_list = pickle.load(open("movie_list.pkl", "rb"))
anime_list = pickle.load(open("anime_list.pkl", "rb"))
anime_similarity = pickle.load(open("anime_similarity.pkl", "rb"))
movie_similarity = pickle.load(open("movie_similarity.pkl", "rb"))


def save_recommendations_to_csv(movieORanime, selected_movie_or_anime, recommended_movie_or_anime):
    from datetime import datetime
    # Get current datetime in the desired format
    datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_path = 'recommended.csv'

    # Create the new row to be inserted
    recommended_movie_names_str = ", ".join(recommended_movie_or_anime)
    new_row = [datetime_now, movieORanime, selected_movie_or_anime, recommended_movie_names_str]

    # Check if the file exists
    # Read all the current rows from the file
    with open(file_path, 'r', encoding='utf-8') as file:
        rows = list(csv.reader(file))

    # Insert the new row at the beginning (after the header)
    rows.insert(1, new_row)  # Insert after the header (index 1)

    # If there are more than 10 rows, keep only the latest 10
    if len(rows) > 11:  # 1 for header + 10 data rows
        rows = rows[:11]  # Keep the first 10 data rows (after the header)

    # Write the updated content back to the CSV
    with open(file_path, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Datetime', 'Movie/Anime', 'Name', 'Recommended'])  # Write the header
        writer.writerows(rows[1:])  # Write the data (skip the header)


def get_anime_recommendations(anime, num_recommendations):
    anime_index = int(anime_list[anime_list["Name"] == anime].index[0])
    top_10_similar_anime_ids = anime_similarity[anime_index]
    recommended_animes = []
    recommended_animes_posters = []
    for anime_id in top_10_similar_anime_ids[:num_recommendations]:
        vote_average = anime_list.at[anime_id,"Rating"]
        poster_url = anime_list.at[anime_id,"Image URL"]
        recommended_animes_posters.append((poster_url, vote_average))
        recommended_animes.append(anime_list.iloc[anime_id].Name)
    return recommended_animes,recommended_animes_posters


api_keys = [
    "58d20f63752ade8c6e45e49c08002a38",
    "8265bd1679663a7ea12ac168da84d2e8",
    "53070df475a34d2304aded57801fde38",
    "36107e2c5e86005819066f1aec8dca34",
    "27ce69086ff30b91cc60c0a4f465c5d1",
    "79662186f9c25ce73c5f50bcd8d95976"
]


# Function to fetch movie poster and rating based on movie_id
def fetch_movie_details(movie_id):
    url_template = "https://api.themoviedb.org/3/movie/{}?api_key={}&language=en-US"

    for api_key in api_keys:
        url = url_template.format(movie_id, api_key)

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()

                poster_path = data.get('poster_path')
                vote_average = data.get('vote_average', 'N/A')

                poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else "https://via.placeholder.com/500"

                return poster_url, vote_average

        except requests.exceptions.RequestException:
            continue

    return "https://via.placeholder.com/500", "N/A"


# Function to recommend movies based on similarity
def get_movie_recommendations(movie, num_recommendations):
    movie_index = int(movie_list[movie_list['title'] == movie].index[0])
    top_100_similar_movie_indices  = movie_similarity[movie_index]
    recommended_movies = []
    recommended_movie_posters = []
    for movie_indices in top_100_similar_movie_indices[:num_recommendations]:
        movie_id = movie_list.at[movie_indices, 'movie_id']
        poster_url, vote_average = fetch_movie_details(movie_id)
        recommended_movie_posters.append((poster_url, vote_average))
        recommended_movies.append(movie_list.iloc[movie_indices].title)
    return recommended_movies, recommended_movie_posters


# Function to recommend movies with rating filter
def get_filtered_recommendations(movie, num_recommendations, min_rating):
    movie_index = int(movie_list[movie_list['title'] == movie].index[0])
    top_100_similar_movie_indices = movie_similarity[movie_index]
    recommended_movies = []
    recommended_movie_posters = []

    min_rating = float(min_rating)
    for movie_indices in top_100_similar_movie_indices[1:]:
        try:
            movie_id = movie_list.at[movie_indices, 'movie_id']
            vote_average = float(movie_list[movie_list['movie_id'] == movie_id].iloc[0]['vote_average'])
            if vote_average >= min_rating:
                poster_url, vote_average = fetch_movie_details(movie_id)
                recommended_movie_posters.append((poster_url, vote_average))
                recommended_movies.append(movie_list.iloc[movie_indices].title)
                if len(recommended_movies) == num_recommendations:
                    break
        except IndexError:
            continue
    return recommended_movies, recommended_movie_posters



st.sidebar.title("NextBest:sparkles:")
option = st.sidebar.selectbox(
    "What would you like to explore?",
    ("Movie", "Anime"),
    index=None,
    help="Choose between movie recommendations or anime recommendations."
)

with st.expander("See History"):
    try:
        df = pd.read_csv("recommended.csv")
        if df.empty:
            st.write("No data available.")
        else:
            st.dataframe(df)

    except FileNotFoundError:
        st.write("File not found.")

if(option == "Movie"):
    st.sidebar.header("_Movie-:blue[Mate]_ :movie_camera:")
    maxRecommend = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

    # Movie selection dropdown
    selected_movie = st.sidebar.selectbox(
        "Select a Movie",
        movie_list["title"]
    )

    # Number of movies to recommend dropdown
    num_movies_to_recommend = st.sidebar.selectbox(
        "How Many Movies to Recommend",
        maxRecommend,
        help="Select how many movies you would like to be recommended."
    )
    # Rating filter toggle and rating selection
    if "filter_enabled" not in st.session_state:
        st.session_state.filter_enabled = False

    st.sidebar.checkbox(
        "Would you like to turn on or off the filter for ratings above a certain threshold?",
        key="filter_enabled"
    )
    rating_threshold = st.sidebar.selectbox(
        "Minimum Rating?",
        options=[float(x) for x in range(1, 11)],
        disabled=not st.session_state.filter_enabled,
        help="Select the minimum rating threshold (1 to 10) for the movie recommendations."
    )
    # Show recommendations on button click
    if st.sidebar.button("Show Recommendation"):
        st.sidebar.markdown("Generating your movie recommendations... :movie_camera:")
        if st.session_state.filter_enabled:
            recommended_movie_names, recommended_movie_posters = get_filtered_recommendations(selected_movie, num_movies_to_recommend, rating_threshold)
        else:
            recommended_movie_names, recommended_movie_posters = get_movie_recommendations(selected_movie, num_movies_to_recommend)

        num_recommended = len(recommended_movie_names)

        if len(recommended_movie_names) == 0 or len(recommended_movie_posters) == 0:
            st.text("No recommendations found.")
        else:
            cols = st.columns(num_recommended)
            for i in range(num_recommended):
                with cols[i]:
                    st.text(recommended_movie_names[i])
                    poster_url, vote_average = recommended_movie_posters[i]
                    st.markdown(f"Rating:star:: {vote_average}")
                    st.image(poster_url)
            save_recommendations_to_csv("Movie", selected_movie, recommended_movie_names)

elif(option == "Anime"):
    st.sidebar.header("Anime-:blue[Mate]_ :movie_camera:")
    maxRecommend = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

    # Anime selection dropdown
    selected_anime = st.sidebar.selectbox(
        "Select an Anime",
        anime_list["Name"],
        help="Pick an anime title from the list to get recommendations."
    )

    # Number of Animes to recommend dropdown
    num_animes_to_recommend = st.sidebar.selectbox(
        "How Many Animes to Recommend?",
        maxRecommend,
        help="Select how many animes you would like to be recommended."
    )
    # Show recommendations on button click
    if st.sidebar.button("Show Recommendation"):
        st.sidebar.markdown("Generating your anime recommendations... :video_camera:")
        recommended_anime_names, recommended_anime_posters = get_anime_recommendations(selected_anime, num_animes_to_recommend)

        cols = st.columns(num_animes_to_recommend)
        for i in range(num_animes_to_recommend):
            with cols[i]:
                st.text(recommended_anime_names[i])
                poster_url, vote_average = recommended_anime_posters[i]
                st.markdown(f"Rating:star:: {vote_average}")
                st.image(poster_url)
        save_recommendations_to_csv("Anime",selected_anime,recommended_anime_names)
