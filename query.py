import asyncio
import os
from gql import gql, Client
import gql.transport.exceptions as gql_exceptions
from gql.transport.aiohttp import AIOHTTPTransport
import queue

# SETUP GraphQL queries
# TODO fix TransportAlreadyConnected error (probably when running multiple queries at once)
queryUrl = "https://leetcode.com/graphql"

clientQueue = queue.Queue()
numClients = 16

# Use several gql clients to support async queries
for i in range(numClients):
    transport = AIOHTTPTransport(url=queryUrl)
    clientQueue.put(Client(transport=transport, execute_timeout=60))

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

# Runs a query with given name and parameters, returns None if error (ASYNC)
async def do_query(query_name, values = {}):
    success = False
    while not success:
        try:
            client = clientQueue.get(block=False)
            success = True
        except queue.Empty:
            await asyncio.sleep(1)
            continue
    try:
        result = await client.execute_async(queries[query_name], variable_values=values)
    except gql_exceptions.TransportQueryError as e:
        result = None
    clientQueue.put(client)
    return result

# TESTING, doesn't run when bot is made 🤥
# limit = -1 # -1 if no limit
# result = asyncio.run(do_query("problemsetQuestionList", values={"categorySlug": "", "skip": 0, "limit": limit, "filters": {}}))
# with open(OUT_PATH + "questionList.txt", "w") as file:
#     file.write(str(result).replace("'", "\""))
