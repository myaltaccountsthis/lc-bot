import os
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

# SETUP GraphQL queries
transport = AIOHTTPTransport(url="https://leetcode.com/graphql")
client = Client(transport=transport, execute_timeout=60)

def read_file(file_name):
    with open(file_name, "r") as f:
        content = f.read()
    return content

queries = {}
QUERIES_PATH = "queries/"
OUT_PATH = "out/"
os.makedirs(OUT_PATH, exist_ok=True)

for file in os.listdir(QUERIES_PATH):
    queries[file[:file.find(".gql")]] = gql(read_file(QUERIES_PATH + file))


# ACTUAL QUERIES, use Postman to get query formatting

# Returns a dictionary of all the LeetCode questions
def query_questions(query_name, values = {}):
    return client.execute(queries[query_name], variable_values=values)


# TESTING, doesn't run when bot is made
limit = -1 # -1 if no limit
result = query_questions("problemsetQuestionList", values={"categorySlug": "", "skip": 0, "limit": limit, "filters": {}})
with open(OUT_PATH + "questionList.txt", "w") as file:
    file.write(str(result).replace("'", "\""))
