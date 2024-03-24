# Author: Abhijeet Behera
# Date: 2024-03-23
# Description: This is a demo of vector search using Couchbase Vector search.

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

# Initialize the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

def vectorize_text(text):
    return model.encode(text).tolist()

def connect_to_capella():
    # Couchbase connection string input through Streamlit UI
    cluster = Cluster('couchbases://cb.9xzsafdettnx3-b.cloud.couchbase.com',
                      ClusterOptions(PasswordAuthenticator('admin', 'Password@P1')))
        # Wait until the cluster is ready for use.
    cluster.wait_until_ready(timedelta(seconds=5))
    bucket = cluster.bucket('movie_bucket')
    return bucket


def load_sample_data():
    with open('data/MovieSample.json', 'r') as sample_data:
        movie_arr = json.load(sample_data)
    return movie_arr

def insert_into_capella(movie_arr, bucket):
    for item in movie_arr:
        key = item['title']
        item['vector'] = vectorize_text(item['description'])
        bucket.default_collection().upsert(key, item)
    st.success(f"Loaded {len(movie_arr)} sample movies into the database.")

def search_movie(bucket):
    st.title("Movie Search App Powered by Vector Search")
    query = st.text_input("Enter search terms related to the movie:")
    if query:
        query_vector = vectorize_text(query)
        results = perform_vector_search(bucket, query_vector)
        print("Search results:", results) 
        for row in results.rows():
                # Use row.id to fetch the document from Couchbase
                doc = bucket.default_collection().get(row.id)
                if doc:
                    # Extract title and description from the document
                    doc_content = doc.content_as[dict]
                    title = doc_content.get('title', 'No Title')
                    description = doc_content.get('description', 'No Description')
                    score = row.score  # Extract the search score

                    # Display title, description, and score in Streamlit
                    st.subheader(f"{title} (Score: {score:.4f})")  # Format score to 4 decimal places
                    st.write(f"Description: {description}")
        # for row in results.rows():
        #     print("Found row ID: {}".format(row.id))
        # if results:
        #     for result in results:
        #         title = result.fields['title']
        #         description = result.fields['description']
        #         st.subheader(title)
        #         st.write(f"Description: {description}")

def perform_vector_search(bucket, query_vector):
    search_index = 'vector'
    try:
        search_req = search.SearchRequest.create(search.MatchNoneQuery()).with_vector_search(
            VectorSearch.from_vector_query(
                VectorQuery('vector', query_vector, num_candidates=5)
            )
        )
        result = bucket.default_scope().search(search_index, search_req, SearchOptions(limit=13,fields=["description","title"]))
        # for row in result.rows():
        #     print("Found row: {}".format(row))
        #     print("Reported total rows: {}".format(
        # result.metadata().metrics().total_rows()))
        return result
    except CouchbaseException as e:
        st.error(f"Vector search failed: {e}")
        return None


def main():
    bucket = connect_to_capella()
    if bucket:
        sample_data = load_sample_data()
        insert_into_capella(sample_data, bucket)
        search_movie(bucket)

if __name__ == "__main__":
    main()

