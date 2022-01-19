# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""

import requests
import re
from flask import Flask, jsonify, request

# *The* app object
app = Flask(__name__)


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"


def gists_for_user(username):
    """Provides the list of gist metadata for a given user.

    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    gists_url = 'https://api.github.com/users/{username}/gists'.format(
        username=username)
    response = requests.get(gists_url)
    # BONUS: What failures could happen?
    # A connection error, timeout error
    # BONUS: Paging? How does this work for users with tons of gists?
    # To enable paging we can add another parameter "page" with integer values
    # the url can now become https://api.github.com/users/{username}/gists?page=1

    return response.json()


@app.route("/api/v1/search", methods=['POST'])
def search():
    """Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    post_data = request.get_json()
    # BONUS: Validate the arguments?
    invalid_arguments = []
    if post_data.get("username") is None or post_data.get("username") == "":
        invalid_arguments.append({'username': "Invalid data or data not provided"})

    if post_data.get("pattern") is None or post_data.get("pattern") == "":
        invalid_arguments.append({'pattern': "Invalid data or data not provided"})

    if invalid_arguments:
        return jsonify(invalid_arguments), 400

    username = post_data['username']
    pattern = post_data['pattern']

    result = {}
    gists = gists_for_user(username)
    matches = []
    for gist in gists:
        # REQUIRED: Fetch each gist and check for the pattern
        gist_id = gist.get("id")
        file_name = list(gist.get("files").keys())[0]
        gist_url = gist.get("files").get(file_name).get("raw_url")
        # response = requests.get(gists_url)
        response = requests.get(gist_url)
        raw_text = response.text
        search_pattern = re.compile(pattern)
        search_result = re.findall(search_pattern, raw_text)
        if search_result:
            match_url = f"https://gist.github.com/{username}/{gist_id}"
            matches.append(match_url)
        # BONUS: What about huge gists?
        # if there are more than one gist files in a single, we can always loop through that.
        # BONUS: Can we cache results in a datastore/db?
        # Yes we can do that with redis or sql/nosql database

    result['status'] = 'success'
    result['username'] = username
    result['pattern'] = pattern
    result['matches'] = matches

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9876)
