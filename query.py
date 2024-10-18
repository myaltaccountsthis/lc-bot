import os
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

transport = AIOHTTPTransport(url="https://leetcode.com/graphql")
client = Client(transport=transport, execute_timeout=60)

def readFile(fileName):
    with open(fileName, "r") as file:
        content = file.read()
    return content

queries = {}
QUERIES_PATH = "queries/"
for file in os.listdir(QUERIES_PATH):
    queries[file[:file.find(".gql")]] = gql(readFile(QUERIES_PATH + file))

def doQuery(queryName, values = {}):
    client.execute(queries[queryName], variable_values=values)

result = doQuery("problemsetQuestionList", values={"categorySlug": "", "skip": 0, "limit": 50, "filters": {}})
# with open("out/questionlistshort.txt", "w") as file:
#     file.write(str(result))
