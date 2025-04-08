import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import quote

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # needed for session tracking
CORS(app)

def get_random_wikipedia_page():
    """
    Fetches a random Wikipedia page title using the Wikipedia Random API.
    Ensures that the page is a valid article (not a talk page, category, help page, etc.).
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "random",
        "rnlimit": 1,
        "format": "json"
    }

    while True:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            page_title = data['query']['random'][0]['title']
            # Fetch metadata to check if it's an article (namespace 0)
            page_info_url = "https://en.wikipedia.org/w/api.php"
            page_info_params = {
                "action": "query",
                "titles": page_title,
                "prop": "info",
                "format": "json"
            }

            page_info_response = requests.get(
                page_info_url, params=page_info_params)
            if page_info_response.status_code == 200:
                page_info = page_info_response.json()
                page_id = list(page_info['query']['pages'].keys())[0]
                namespace = page_info['query']['pages'][page_id].get(
                    'ns', None)

                # Check if the page is in the main namespace (namespace 0)
                if namespace == 0:
                    return page_title
                else:
                    print(
                        f"Skipping non-article page: {page_title}. Retrying...")
            else:
                print(f"Error fetching metadata for {page_title}. Retrying...")
        else:
            print("Error fetching random Wikipedia page.")
            return None


def get_wikipedia_pageviews(article_title, days=30):
    # Calculate start and end dates
    end_date = datetime.today() - timedelta(days=1)  # yesterday (latest available data)
    start_date = end_date - timedelta(days=days - 1)

    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    # Encode the article title for use in the URL
    encoded_title = quote(article_title.replace(" ", "_"), safe='')

    endpoint = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{encoded_title}/daily/{start_str}/{end_str}"

    headers = {
        'User-Agent': 'obscurity-game (hackathon project)'
    }

    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        total_views = sum(item["views"] for item in data["items"])
        return total_views
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except KeyError:
        print("Unexpected data format or article not found.")
    return None


def get_hyperlinks_from_page(page_title):
    """
    Fetches and lists the hyperlinks on a Wikipedia page, excluding non-article links.
    """
    url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        added = set()

        # Find all <a> tags with href attributes
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Only consider links that start with '/wiki/', indicating it's a valid article
            if href.startswith('/wiki/') and ':' not in href:
                # Remove the '/wiki/' part to get the actual article title
                s = href[6:]
                if s not in added:
                    links.append(s)
                    added.add(s)

        return links
    else:
        print(f"Error: Unable to fetch {page_title}")
        return []

@app.route('/')
def index():
    # Start a new session
    session['visited'] = []
    session['clicks'] = 0

    start_article = get_random_wikipedia_page()
    session['visited'].append(start_article)

    links = get_hyperlinks_from_page(start_article)
    return render_template('game.html', title=start_article, links=links)

@app.route('/next', methods=['POST'])
def next_article():
    data = request.json
    next_title = data.get('title')

    if 'visited' not in session:
        session['visited'] = []

    if 'clicks' not in session:
        session['clicks'] = 0

    session['visited'].append(next_title)
    session['clicks'] += 1

    links = get_hyperlinks_from_page(next_title)

    return jsonify({
        'title': next_title,
        'links': links,
        'visited': session['visited'],
        'clicks': session['clicks']
    })

if __name__ == '__main__':
    app.run(debug=True)
