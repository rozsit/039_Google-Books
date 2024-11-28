import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from googleapiclient.discovery import build
import streamlit as st
import os
# from dotenv import load_dotenv
import warnings

# Set wider page layout for the Streamlit app
st.set_page_config(page_title="Google Books Analysis", layout="wide")

warnings.filterwarnings("ignore", category=FutureWarning)

# load .env files
# load_dotenv()

# API-key
os.environ["GOOGLE_BOOKS_API_KEY"] == st.secrets["GOOGLE_BOOKS_API_KEY"]
API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

# Function to fetch books from Google Books API


def fetch_books(query, max_results=40):
    """
    Fetches book data from Google Books API.
    """
    service = build("books", "v1", developerKey=API_KEY)
    request = service.volumes().list(q=query, maxResults=max_results)
    response = request.execute()

    items = response.get("items", [])
    books = []
    for item in items:
        volume_info = item.get("volumeInfo", {})
        books.append({
            "Title": volume_info.get("title"),
            "Authors": ", ".join(volume_info.get("authors", ["Unknown"])),
            "Published Date": volume_info.get("publishedDate"),
            "Categories": ", ".join(volume_info.get("categories", ["None"])),
            "Ratings": volume_info.get("averageRating"),
            "Page Count": volume_info.get("pageCount"),
        })
    return pd.DataFrame(books)


# Load data
@st.cache_data
def load_data():
    categories = ["Machine Learning", "Python Programming",
                  "Data Science", "Data Analysis", "Data Engineering"]
    all_books = pd.DataFrame()

    for category in categories:
        books = fetch_books(category)
        books["Category"] = category
        all_books = pd.concat([all_books, books], ignore_index=True)

    # Data Cleaning
    all_books["Published Year"] = pd.to_datetime(
        all_books["Published Date"], errors="coerce").dt.year
    all_books["Ratings"] = pd.to_numeric(all_books["Ratings"], errors="coerce")
    all_books["Page Count"] = pd.to_numeric(
        all_books["Page Count"], errors="coerce")
    return all_books


# App title and subtitle
st.title("📚 Exploratory Analysis of Popular Google Books 📚")
st.markdown("""
This app allows you to:
- Explore data from popular book categories such as Machine Learning, Python Programming, Data Science, Data Analysis and Data Engineering.
- Visualize key metrics like ratings, page counts, and publication years using interactive plots.
- Identify trends and insights, including the most prolific authors and top categories.
""")

# Load data
with st.spinner("Fetching data..."):
    all_books = load_data()

# Sidebar Filters
st.sidebar.header("Filter Data")

categories = all_books["Category"].unique()

selected_category = st.sidebar.multiselect(
    "Select Categories",
    options=categories,
    default=categories.tolist()
)

# If no categories are selected, reset to the first category
if not selected_category:
    st.sidebar.warning(
        "At least one category must be selected. Resetting to default.")
    selected_category = [categories[0]]

min_year = int(all_books["Published Year"].min())
max_year = int(all_books["Published Year"].max())

selected_year_range = st.sidebar.slider(
    "Select Published Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

filtered_data = all_books[
    (all_books["Category"].isin(selected_category)) &
    (all_books["Published Year"] >= selected_year_range[0]) &
    (all_books["Published Year"] <= selected_year_range[1])
]


# Show Dataframe
st.header("Google Books Dataset")
st.dataframe(filtered_data)

# Summary Statistics
st.header("Summary Statistics")
st.write(filtered_data.describe(include="all").transpose())

# Visualizations
st.header("Visualizations")

# 1. Ratings Distribution by Category (Plotly Box Plot)
fig = px.box(
    filtered_data,
    x="Category",
    y="Ratings",
    color="Category",
    title="Ratings Distribution by Category",
    labels={"Ratings": "Average Rating"},
    points="all"
)
fig.update_layout(
    width=1200,
    height=600,
    title_x=0.4,
    title_font_size=20
)
st.plotly_chart(fig)

# 2. Page Count Distribution (Plotly Histogram)
fig = px.histogram(
    filtered_data,
    x="Page Count",
    color="Category",
    nbins=20,
    title="Page Count Distribution",
    labels={"Page Count": "Number of Pages"},
    opacity=0.6
)
fig.update_layout(
    width=1200,
    height=600,
    title_x=0.4,
    title_font_size=20
)
st.plotly_chart(fig)

# 3. Published Year vs Ratings (Scatter Plot)
fig = px.scatter(
    filtered_data,
    x="Published Year",
    y="Ratings",
    color="Category",
    size="Page Count",
    title="Published Year vs Ratings",
    labels={"Published Year": "Year", "Ratings": "Average Rating"}
)
fig.update_layout(
    width=1200,
    height=600,
    title_x=0.4,
    title_font_size=20
)
st.plotly_chart(fig)

# 4. Top Authors by Number of Books (Plotly Bar Plot)
top_authors = filtered_data["Authors"].value_counts().head(8)

top_authors_sorted = top_authors.sort_values(ascending=True)
truncated_author_names = [
    name if len(name) <= 40 else name[:37] + "..."
    for name in top_authors_sorted.index
]

fig = px.bar(
    x=top_authors_sorted.values,
    y=truncated_author_names,
    title="Top 10 Authors by Number of Books",
    labels={"x": "Number of Books", "y": "Author"},
    orientation="h"
)
fig.update_layout(
    width=1200,
    height=600,
    title_x=0.4,
    title_font_size=20
)
st.plotly_chart(fig)


# 5. Missing Values Heatmap (Plotly Heatmap)
columns = filtered_data.columns
rows = list(range(len(filtered_data)))

fig = go.Figure(data=go.Heatmap(
    z=filtered_data.isnull().astype(int),
    x=columns,
    y=rows,
    colorscale="ice",
    showscale=True
))
fig.update_layout(
    width=1200,
    height=600,
    title="Missing Data Heatmap",
    title_x=0.4,
    title_font_size=20,
    xaxis_title="Columns",
    yaxis_title="Rows",
    xaxis=dict(tickangle=45)
)
st.plotly_chart(fig)
