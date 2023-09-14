# import json

# def main():
#     # Sample data to be written to JSON file
#     data = {
#         "name": "James Doe",
#         "age": 30,
#         "city": "California"
#     }

#     # Create or overwrite a JSON file with the data
#     with open('data.json', 'w') as outfile:
#         json.dump(data, outfile, indent=4)

# if __name__ == "__main__":
#     main()



# =============================================================================
# 0.0. Libraries
import pandas as pd
import json
import requests
import numpy as np
from bs4 import BeautifulSoup
import datetime
from datetime import datetime
import time
import ast

# Flask-Related Code
# from flask import Flask, render_template, jsonify, render_template_string, request, flash
# @app.route('/')
# def hello_world():
#     return 'Hello, World!'

# =============================================================================

# 1.0. Read the reliefweb data
# --------------
start_time = time.time()
# Extract Data from API

# Define the API query
api_country_query = [
    "Afghanistan",
    "Bangladesh",
    "Bhutan",
    "Cambodia",
    "Democratic%20People's%20Republic%20of%20Korea",
    "Fiji",
    "Indonesia",
    "India",
    "Kyrgyzstan",
    "Lao%20People's%20Democratic%20Republic%20(the)",
    "Myanmar",
    "Nepal",
    "Pakistan",
    "Papua%20New%20Guinea",
    "Philippines",
    "Samoa",
    "Sri%20Lanka",
    "Tajikistan",
    "Timor-Leste",
    "Tonga",
    "Tuvalu",
]

api_country_query = "".join(
    f"&filter[conditions][0][conditions][{i}][field]=primary_country&filter[conditions][0][conditions][{i}][value]={country}"
    for i, country in enumerate(api_country_query)
)

base_url = "https://api.reliefweb.int/v1/reports?appname=apidoc&profile=full&limit=1000&filter[operator]=AND&filter[conditions][0][operator]=OR"

years = list(range(2016, 2024))

api_urls = [
    f"{base_url}{api_country_query}&filter[conditions][1][field]=date.created&filter[conditions][1][value][from]={year}-01-01T00:00:00%2B00:00&filter[conditions][1][value][to]={year}-12-31T23:59:59%2B00:00&filter[conditions][2][field]=source.shortname&filter[conditions][2][value]=WFP"
    for year in years
]

# Now load the APIs here. We have to build multiple because the limit for this API is 1,000.
reliefweb_raws = [requests.get(api_url) for api_url in api_urls]

# Ensure that all requests were successful
assert all(reliefweb_raw.status_code == 200 for reliefweb_raw in reliefweb_raws)

reliefweb_list = [
    item for reliefweb_raw in reliefweb_raws for item in reliefweb_raw.json()["data"]
]


# =============================================================================

# 2.0. Create the reliefweb dataframe
# -----------------------------------

# Transform the API's output into a dataframe

# Normalize the list into a DataFrame
rw_df = pd.json_normalize(reliefweb_list, sep="_")


# Create functions to normalize the DataFrame for those that are nested into lists, with comma separated values, or to extract the thumbnail which is nested deeper
def extract_and_join(row, field_name):
    if isinstance(row, list) and all(isinstance(elem, dict) for elem in row):
        return ", ".join([str(elem.get(field_name, "")) for elem in row])
    return row


def get_url_thumb(files):
    if isinstance(files, list) and files:
        first_file = files[0]  # access the first file dictionary
        if isinstance(first_file, dict) and "preview" in first_file:
            preview = first_file["preview"]  # access the 'preview' dictionary
            if isinstance(preview, dict) and "url-thumb" in preview:
                return preview["url-thumb"]  # return the 'url-thumb' value


# Extract for countries (where there are multiple), format (which is category), source (which is author), and thumbnail
rw_df["multiple_country_names"] = rw_df["fields_country"].apply(
    extract_and_join, field_name="name"
)
rw_df["category"] = rw_df["fields_format"].apply(extract_and_join, field_name="name")
rw_df["author"] = rw_df["fields_source"].apply(extract_and_join, field_name="shortname")
rw_df["thumb"] = rw_df["fields_file"].apply(get_url_thumb)

# Extract needed columns and rename them
rw_df = rw_df[
    [
        "fields_date_created",
        "fields_primary_country_name",
        "category",
        "author",
        "fields_title",
        "fields_origin",
        "fields_url_alias",
        "fields_body",
        "thumb",
    ]
]

rw_df.columns = [
    "date",
    "country",
    "category",
    "author",
    "title",
    "origin_link",
    "reliefweb_link",
    "summary",
    "thumb",
]


# =============================================================================

# 3.0. Clean the reliefweb dataframe
# ----------------------------------

# Convert to datetime (and remove timezone), sort by date, then convert it back to a string
rw_df["date"] = pd.to_datetime(rw_df["date"]).dt.tz_localize(None)
rw_df["date"] = rw_df["date"].dt.strftime("%Y-%m-%d")


# Rename certain categories
rw_df["category"] = rw_df["category"].fillna("")
rw_df["category"] = np.select(
    [
        # Where it contains certain words
        # Where it contains certain words
        rw_df["title"].str.contains("evaluation", case=False, na=False),
        rw_df["title"].str.contains("assess", case=False, na=False),
        rw_df["title"].str.contains("survey", case=False, na=False),
        rw_df["title"].str.contains("market", case=False, na=False),
        rw_df["title"].str.contains("price", case=False, na=False),
        rw_df["title"].str.contains("analysis", case=False, na=False),
        rw_df["title"].str.contains("research", case=False, na=False),
        rw_df["title"].str.contains("evidence", case=False, na=False),
        rw_df["title"].str.contains("study", case=False, na=False),
        rw_df["title"].str.contains("annual country report", case=False, na=False),
        rw_df["title"].str.contains("situation report", case=False, na=False),
        rw_df["title"].str.contains("lesson", case=False, na=False),
        rw_df["title"].str.contains("manual", case=False, na=False),
        rw_df["title"].str.contains("guideline", case=False, na=False),
        rw_df["title"].str.contains("dashboard", case=False, na=False),
        rw_df["title"].str.contains("map", case=False, na=False),
        rw_df["title"].str.contains("infographic", case=False, na=False),
        rw_df["title"].str.contains("country brief", case=False, na=False),
        rw_df["title"].str.contains("seasonal monitor", case=False, na=False),
        rw_df["title"].str.contains("mvam", case=False, na=False),
        rw_df["title"].str.contains("fact", case=False, na=False),
        rw_df["title"].str.contains("fill the nutrient", case=False, na=False),
        rw_df["title"].str.contains("understanding", case=False, na=False),
        rw_df["title"].str.contains("food security monitoring", case=False, na=False),
        rw_df["title"].str.contains("food security update", case=False, na=False),
        rw_df["title"].str.contains("food security bulletin", case=False, na=False),
        # Where it is a certain word
        (rw_df["category"] == "Map"),
        (rw_df["category"] == "Infographic"),
        (rw_df["category"] == "Evaluation and Lessons Learned"),
        (rw_df["category"] == "Assessment"),
        (rw_df["category"] == "Analysis"),
        (rw_df["category"] == "News and Press Release"),
        (rw_df["category"] == "Response Plans/Appeals")
    ],
    [
        # Where title contains certain words
        "Evaluation and Lessons Learned",
        "Assessments (Food Security and Nutrition)",
        "Assessments (Food Security and Nutrition)",
        "Market/Price Monitoring",
        "Market/Price Monitoring",
        "Analysis/Research",
        "Analysis/Research",
        "Analysis/Research",
        "Analysis/Research",
        "Annual Country Report",
        "Situation Report",
        "Evaluation and Lessons Learned",
        "Manuals/Guidelines",
        "Manuals/Guidelines",
        "Dashboards/Maps/Infographics",
        "Dashboards/Maps/Infographics",
        "Dashboards/Maps/Infographics",
        "Country Brief",
        "Assessments (Food Security and Nutrition)",
        "Assessments (Food Security and Nutrition)",
        "Dashboards/Maps/Infographics",
        "Assessments (Food Security and Nutrition)",
        "Analysis/Research",
        "Assessments (Food Security and Nutrition)",
        "Assessments (Food Security and Nutrition)",
        "Assessments (Food Security and Nutrition)",
        # Where category is a certain word
        "Dashboards/Maps/Infographics",
        "Dashboards/Maps/Infographics",
        "Evaluation and Lessons Learned",
        "Assessments (Food Security and Nutrition)",
        "Analysis/Research",
        "Stories/Articles",
        "Other",
    ],
    default=rw_df["category"],
)


# Rename certain countries to match the spatial dataset
rw_df["country"] = np.select(
    [
        (rw_df["country"] == "Lao People's Democratic Republic (the)"),
        (rw_df["country"] == "American Samoa"),
    ],
    [
        "Lao People's Democratic Republic",
        "Samoa",
    ],
    default=rw_df["country"],
)


# Sort values
rw_df = rw_df.sort_values(by=["date", "country"], ascending=False)

# Replace any black image values with a custom image to indicate a blank space
rw_df["thumb"] = rw_df["thumb"].fillna(
    "https://raw.githubusercontent.com/ctedja/regional_evidence/main/static/images/empty_link.png"
)

# Replace any missing values with an empty string and update date format
rw_df = rw_df.fillna("")
rw_df["date"] = pd.to_datetime(rw_df["date"])

# Update the country names in certain cases as needed
rw_df["country"] = rw_df.apply(
    lambda x: "Asia-Pacific" if "asia" in x["title"].lower() else x["country"],
    axis=1,
)

rw_df["country"] = rw_df["country"].apply(
    lambda x: "Pacific"
    if any(
        country.strip() in ["Fiji", "Samoa", "Tonga", "Tuvalu", "Papua New Guinea"]
        for country in x.split(",")
    )
    else x
)

# Remove any duplicates in the comma-separated column of countries
rw_df["country"] = rw_df["country"].apply(
    lambda x: ', '.join(sorted(set(country.strip() for country in x.split(','))))
)


# Where origin_link == "", replace with reliefweb_link
rw_df["link"] = rw_df.apply(
    lambda x: x["reliefweb_link"] if x["origin_link"] == "" else x["origin_link"],
    axis=1,
)



# 6.0. Preparing Data to be used as JSON
# --------------------------------------


records = rw_df.to_dict(orient="records")

# Create new dictionary with desired structure
data = {"data": records}


# Dump dictionary to json file - only if we are working on that separate exported file
with open("data.json", "w") as f:
    json.dump(data, f, default=str)

end_time = time.time()
(end_time - start_time)/60

