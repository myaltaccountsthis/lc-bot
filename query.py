import os
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

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

def do_query(query_name, values = {}):
    return client.execute(queries[query_name], variable_values=values)

limit = 50 # -1 if no limit
result = do_query("problemsetQuestionList", values={"categorySlug": "", "skip": 0, "limit": limit, "filters": {}})
with open(OUT_PATH + "questionList.txt", "w") as file:
    file.write(str(result))
