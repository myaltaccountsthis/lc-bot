import re
import os
import random
import query

PROBLEM_PATH = "out/questionList.txt"
CONTEST_PATH = "out/contestList.txt"
PROBLEM_LINK = "https://leetcode.com/problems/"
CONTEST_LINK = "https://leetcode.com/contest/"

question_data = []
contest_info_data = []
contest_info_from_slug = {}

# Loads the question data by calling the query, stores into array by id, TIME_EXPENSIVE
async def load_question_data(forceFetch=False):
    global question_data
    if len(question_data) == 0:
        if forceFetch or not os.path.exists(PROBLEM_PATH):
            result = await query.do_query("problemsetQuestionList", values={"categorySlug": "", "skip": 0, "limit": -1, "filters": {}})
            with open(PROBLEM_PATH, "w") as file:
                file.write(str(result))
        else:
            with open(PROBLEM_PATH, "r") as file:
                result = eval(file.read())
        question_data = result["problemsetQuestionList"]["questions"]
        print("Loaded question data!")

# Loads the contest info data by calling the query, stores into array and dict, TIME_EXPENSIVE
async def load_contest_info_data(forceFetch=False):
    global contest_info_data, contest_info_from_slug
    if len(contest_info_data) == 0:
        if forceFetch or not os.path.exists(CONTEST_PATH):
            result = await query.do_query("contestGeneralInfo", values={"titleSlug": ""})
            result = result["pastContests"]["data"]
            with open(CONTEST_PATH, "w") as file:
                file.write(str(result))
        else:
            with open(CONTEST_PATH, "r") as file:
                result = eval(file.read())

        contest_info_data = result
        contest_info_data.reverse()
        for contest in result:
            contest_info_from_slug[contest["titleSlug"]] = contest
        print("Loaded contest data!")

# Returns the link of a random question
async def random_question(allow_premium):
    await load_question_data()
    # The data of a random question, keep looping if
    # it is a premium question and we don't want premium questions
    question = None
    while True:
        question = question_data[random.randrange(0, len(question_data))]
        if allow_premium or not question["paidOnly"]:
            break
    return PROBLEM_LINK + question["titleSlug"]

# Get generic info (questions and links) of a specific contest
async def get_contest_info(titleSlug=None):
    await load_contest_info_data()
    if titleSlug is None:
        titleSlug = contest_info_data[0]["titleSlug"]
    elif titleSlug not in contest_info_from_slug:
        return f"Could not find contest {titleSlug}"

    contest_info = contest_info_from_slug[titleSlug]
    return ''.join([contest_info["title"], ": ", CONTEST_LINK, titleSlug, "\n",
        "\n".join(PROBLEM_LINK + question["titleSlug"] for question in contest_info["questions"])])