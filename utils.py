import random
import query

PROBLEM_LINK = "https://leetcode.com/problems/"

question_data = []

# Loads the data by calling the query, TIME_EXPENSIVE
def load_question_data():
    global question_data
    if len(question_data) == 0:
        result = query.query_questions("problemsetQuestionList", values={"categorySlug": "", "skip": 0, "limit": -1, "filters": {}})
        
        # print(result)
        question_data = result["problemsetQuestionList"]["questions"]

# Returns the link of a random question
def random_question(allow_premium=False):
    load_question_data()
    # The data of a random question, keep looping if
    # it is a premium question and we don't want premium questions
    question = None
    while True:
        question = question_data[random.randrange(0, len(question_data))]
        if allow_premium or not question["paidOnly"]:
            break
    return PROBLEM_LINK + question["titleSlug"] 