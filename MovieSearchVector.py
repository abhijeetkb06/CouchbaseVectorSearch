from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.exceptions import CouchbaseException
import streamlit as st
import json
from sentence_transformers import SentenceTransformer
from datetime import timedelta
from couchbase.options import SearchOptions
import couchbase.search as search
from couchbase.vector_search import VectorQuery, VectorSearch


model = SentenceTransformer('all-MiniLM-L6-v2')

def vectorize_text(text):

    return model.encode(text).tolist()

def connect_to_capella():
 
    try:
        cluster = Cluster('couchbases://cb.vo0u9a3drcc0wods.cloud.couchbase.com',
                          ClusterOptions(PasswordAuthenticator('admin', 'Password@P1')))
        cluster.wait_until_ready(timedelta(seconds=5))
        bucket = cluster.bucket('movie_bucket')
        return bucket
    except CouchbaseException as e:
        st.error(f"Failed to connect to Couchbase: {e}")
        return None

def load_sample_data():
    
    with open('data/MovieSample.json', 'r') as sample_data:
        movie_arr = json.load(sample_data)
    return movie_arr

def insert_into_capella(movie_arr, bucket):
   
    if not bucket:
        return
    try:
        for item in movie_arr:
            key = item['title']
            item['vector'] = vectorize_text(item['description'])
            bucket.default_collection().upsert(key, item)
        st.success(f"Loaded {len(movie_arr)} sample movies into the database.")
    except CouchbaseException as e:
        st.error(f"Failed to load sample data into Couchbase: {e}")

def perform_vector_search(bucket, query_vector):
    
    if not bucket:
        return
    search_index = 'vectorSearchIndex'
    try:
        search_req = search.SearchRequest.create(search.MatchNoneQuery()).with_vector_search(
            VectorSearch.from_vector_query(
                VectorQuery('vector', query_vector, num_candidates=5)
            )
        )
        result = bucket.default_scope().search(search_index, search_req, SearchOptions(limit=5, fields=["title", "description", "poster_url"]))
        return result
    except CouchbaseException as e:
        st.error(f"Vector search failed: {e}")
        return None

def search_movie(bucket):
    st.subheader("Search for Movies")
    query = st.text_input("Enter search terms related to the movie:")
    if query:
        query_vector = vectorize_text(query)
        results = perform_vector_search(bucket, query_vector)
        if results and results.rows():
            for row in results.rows():
                # Accessing fields directly from the search result
                title = row.fields.get('title', 'No Title')
                description = row.fields.get('description', 'No Description')
                poster_url = row.fields.get('poster_url', None)
                score = getattr(row, 'score', None)  

                st.subheader(f"{title}" + (f" (Score: {score:.4f})" if score else ""))
                if poster_url:
                    st.image(poster_url, width=200)
                st.write(f"Description: {description}")
                st.markdown("---")
        else:
            st.write("No movies found matching your search criteria.")

def main():
    # st.title("Movie Search Powered By Couchbase Vector Search")
    st.markdown("""
    <style>
    .title-font {
        font-size: 28px;
        font-weight: bold;
    }
    .powered-font {
        color: red;
        font-size: 20px;
    }
    </style>
    <div>
        <span class="title-font">Movie Search</span><br>
        <span class="powered-font">Powered By Couchbase Vector Search</span>
    </div>
    """, unsafe_allow_html=True)

    bucket = connect_to_capella()
    if bucket:
        sample_data = load_sample_data()
        insert_into_capella(sample_data, bucket)
        search_movie(bucket)

if __name__ == "__main__":
    main()
