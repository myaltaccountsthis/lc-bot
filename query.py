import asyncio
import os
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

# SETUP GraphQL queries
# TODO fix TransportAlreadyConnected error (probably when running multiple queries at once)
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

# Runs a query with given name and parameters (ASYNC)
async def do_query(query_name, values = {}):
    return await client.execute_async(queries[query_name], variable_values=values)

# TESTING, doesn't run when bot is made 🤥
# limit = -1 # -1 if no limit
# result = asyncio.run(do_query("problemsetQuestionList", values={"categorySlug": "", "skip": 0, "limit": limit, "filters": {}}))
# with open(OUT_PATH + "questionList.txt", "w") as file:
#     file.write(str(result).replace("'", "\""))
