import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import quote

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'supersecretkey'
CORS(app)

def get_random_wikipedia_page():
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

            info_params = {
                "action": "query",
                "titles": page_title,
                "prop": "info",
                "format": "json"
            }
            info_response = requests.get(url, params=info_params)
            if info_response.status_code == 200:
                info = info_response.json()
                page_id = list(info['query']['pages'].keys())[0]
                namespace = info['query']['pages'][page_id].get('ns', None)
                if namespace == 0:
                    return page_title
        # fallback just in case
        return "Special:Random"

def get_wikipedia_pageviews(article_title, days=30):
    end_date = datetime.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=days - 1)
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    encoded_title = quote(article_title.replace(" ", "_"), safe='')
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{encoded_title}/daily/{start_str}/{end_str}"

    try:
        headers = {'User-Agent': 'obscurity-game (hackathon project)'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return sum(item["views"] for item in data["items"])
    except Exception as e:
        print(f"Pageview error for '{article_title}': {e}")
        return 0

def get_hyperlinks_from_page(page_title):
    url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
    response = requests.get(url)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = []
    added = set()
    for tag in soup.find_all('a', href=True):
        href = tag['href']
        if href.startswith('/wiki/') and ':' not in href:
            article = href[6:]
            if article not in added:
                links.append(article)
                added.add(article)
    return links

@app.route('/')
def index():
    session['visited'] = []
    session['clicks'] = 0

    start_article = get_random_wikipedia_page()
    session['visited'].append(start_article)

    return render_template('game.html', title=start_article)  # ✅ title passed to template

@app.route('/article_data')
def article_data():
    title = request.args.get("title", "Special:Random")
    if title == "Special:Random":
        title = get_random_wikipedia_page()

    links = get_hyperlinks_from_page(title)
    views = get_wikipedia_pageviews(title)

    return jsonify({
        "title": title,
        "links": links[:50],
        "pageviews": views
    })

@app.route('/next', methods=['POST'])
def next_article():
    data = request.json
    next_title = data.get('title')

    if not next_title:
        return jsonify({"error": "No title provided"}), 400

    session.setdefault('visited', []).append(next_title)
    session['clicks'] = session.get('clicks', 0) + 1

    links = get_hyperlinks_from_page(next_title)

    return jsonify({
        'title': next_title,
        'links': links,
        'visited': session['visited'],
        'clicks': session['clicks']
    })

if __name__ == '__main__':
    app.run(debug=True)
