from couchbase.cluster import Cluster, ClusterOptions
from couchbase.auth import PasswordAuthenticator
from sentence_transformers import SentenceTransformer
import streamlit as st
import couchbase.search as search
from couchbase.options import SearchOptions
from couchbase.vector_search import VectorQuery, VectorSearch

# Initialize the vectorization model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Function to vectorize text
def vectorize_text(text):
    return model.encode(text).tolist()

# Couchbase connection setup
def connect_to_couchbase():
    cluster = Cluster('couchbases://<your_cluster_url>',
                      ClusterOptions(PasswordAuthenticator('<your_username>', '<your_password>')))
    bucket = cluster.bucket('<your_bucket_name>')
    return bucket

# Function to load sample data into Couchbase
def load_sample_data(bucket):
    # Assuming the function to load and check if data already exists is implemented elsewhere
    # This is a simplified version to focus on the data loading
   sample_movies = [
                {
                    "title": "Inception",
                    "description": "A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into the mind of a CEO.",
                    "genre": ["Action", "Adventure", "Sci-Fi"]
                },
                {
                    "title": "The Shawshank Redemption",
                    "description": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
                    "genre": ["Drama"]
                },
                {
                    "title": "The Godfather",
                    "description": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
                    "genre": ["Crime", "Drama"]
                },
                {
                    "title": "Pulp Fiction",
                    "description": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
                    "genre": ["Crime", "Drama"]
                },
                {
                    "title": "The Dark Knight",
                    "description": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
                    "genre": ["Action", "Crime", "Drama"]
                },
                {
                    "title": "Forrest Gump",
                    "description": "The presidencies of Kennedy and Johnson, the Vietnam War, the Watergate scandal and other historical events unfold from the perspective of an Alabama man with an IQ of 75, whose only desire is to be reunited with his childhood sweetheart.",
                    "genre": ["Drama", "Romance"]
                },
                {
                    "title": "Fight Club",
                    "description": "An insomniac office worker and a devil-may-care soap maker form an underground fight club that evolves into much more.",
                    "genre": ["Drama"]
                },
                {
                    "title": "Psycho",
                    "description": "A Phoenix secretary embezzles forty thousand dollars from her employer's client, goes on the run, and checks into a remote motel run by a young man under the domination of his mother.",
                    "genre": ["Horror", "Mystery", "Thriller"]
                },
                {
                    "title": "Parasite",
                    "description": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
                    "genre": ["Comedy", "Drama", "Thriller"]
                },
                {
                    "title": "La La Land",
                    "description": "While navigating their careers in Los Angeles, a pianist and an actress fall in love while attempting to reconcile their aspirations for the future.",
                    "genre": ["Comedy", "Drama", "Music"]
                },
                {
                    "title": "The Matrix",
                    "description": "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",
                    "genre": ["Action", "Sci-Fi"]
                },
                {
                    "title": "Titanic",
                    "description": "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic.",
                    "genre": ["Drama", "Romance"]
                },
                {
                    "title": "Jurassic Park",
                    "description": "During a preview tour, a theme park suffers a major power breakdown that allows its cloned dinosaur exhibits to run amok.",
                    "genre": ["Adventure", "Sci-Fi", "Thriller"]
                },
                {
                    "title": "The Silence of the Lambs",
                    "description": "A young F.B.I. cadet must receive the help of an incarcerated and manipulative cannibal killer to help catch another serial killer, a madman who skins his victims.",
                    "genre": ["Crime", "Drama", "Thriller"]
                },
                {
                    "title": "Se7en",
                    "description": "Two detectives, a rookie and a veteran, hunt a serial killer who uses the seven deadly sins as his motives.",
                    "genre": ["Crime", "Drama", "Mystery"]
                },
                {
                    "title": "It's a Wonderful Life",
                    "description": "An angel is sent from Heaven to help a desperately frustrated businessman by showing him what life would have been like if he had never existed.",
                    "genre": ["Drama", "Family", "Fantasy"]
                },
                {
                    "title": "Whiplash",
                    "description": "A promising young drummer enrolls at a cut-throat music conservatory where his dreams of greatness are mentored by an instructor who will stop at nothing to realize a student's potential.",
                    "genre": ["Drama", "Music"]
                },
                {
                    "title": "The Prestige",
                    "description": "After a tragic accident, two stage magicians engage in a battle to create the ultimate illusion while sacrificing everything they have to outwit each other.",
                    "genre": ["Drama", "Mystery", "Sci-Fi"]
                },
                {
                    "title": "Gladiator",
                    "description": "A former Roman General sets out to exact vengeance against the corrupt emperor who murdered his family and sent him into slavery.",
                    "genre": ["Action", "Adventure", "Drama"]
                },
                {
                    "title": "Interstellar",
                    "description": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
                    "genre": ["Adventure", "Drama", "Sci-Fi"]
                }
            ]

    # Check if the data is already loaded to avoid duplication
if bucket.default_collection().exists('Inception')['exists']:
        st.info("Sample data already loaded.")
else:
        for movie in sample_movies:
            movie['vector'] = vectorize_text(movie['description'])
            key = movie['title']  # Use the movie title as the document key
            bucket.default_collection().upsert(key, movie)
        st.success(f"Loaded {len(sample_movies)} sample movies into the database.")

# Couchbase vector search functionality
def search_movies(bucket, query_vector):
    search_index = '<your_vector_search_index>'
    search_req = search.SearchRequest.create(search.MatchNoneQuery()).with_vector_search(
        VectorSearch.from_vector_query(
            VectorQuery('vector', query_vector, num_candidates=5)
        )
    )
    result = bucket.default_scope().search(search_index, search_req, SearchOptions(fields=['title', 'description']))
    return [hit.fields for hit in result.hits]

# Streamlit UI components
def main():
    st.title("Movie Search App Powered by Vector Search")

    # Couchbase Connection
    bucket = connect_to_couchbase()

    # Load sample data into Couchbase
    load_sample_data(bucket)

    # Movie Search Section
    query = st.text_input("Enter search terms related to the movie:")
    if query:
        query_vector = vectorize_text(query)
        results = search_movies(bucket, query_vector)
        
        for result in results:
            st.subheader(result['title'])
            st.write(f"Description: {result['description']}")
            st.markdown("---")

if __name__ == "__main__":
    main()
