import random
import query

PROBLEM_LINK = "https://leetcode.com/problems/"
CONTEST_LINK = "https://leetcode.com/contest/"

question_data = []
contest_info_data = []
contest_info_from_slug = {}

# Loads the question data by calling the query, stores into array by id, TIME_EXPENSIVE
def load_question_data():
    global question_data
    if len(question_data) == 0:
        result = query.do_query("problemsetQuestionList", values={"categorySlug": "", "skip": 0, "limit": -1, "filters": {}})
        
        question_data = result["problemsetQuestionList"]["questions"]

# Loads the contest info data by calling the query, stores into array and dict, TIME_EXPENSIVE
def load_contest_info_data():
    global contest_info_data
    if len(contest_info_data) == 0:
        result = query.do_query("contestGeneralInfo", values={"titleSlug": ""})["pastContests"]["data"]

        contest_info_data = result
        contest_info_data.reverse()
        for contest in result:
            contest_info_from_slug[contest["titleSlug"]] = contest

# Returns the link of a random question
def random_question(allow_premium):
    load_question_data()
    # The data of a random question, keep looping if
    # it is a premium question and we don't want premium questions
    question = None
    while True:
        question = question_data[random.randrange(0, len(question_data))]
        if allow_premium or not question["paidOnly"]:
            break
    return PROBLEM_LINK + question["titleSlug"]

# Get generic info (questions and links) of a specific contest
def get_contest_info(titleSlug=""):
    load_contest_info_data()
    if titleSlug == "":
        titleSlug = contest_info_data[-1]["titleSlug"]
    
    if titleSlug not in contest_info_from_slug:
        return "Contest not found"

    contest_info = contest_info_from_slug[titleSlug]
    return ''.join([contest_info["title"], ": ", CONTEST_LINK, titleSlug, "\n",
        "\n".join(PROBLEM_LINK + question["titleSlug"] for question in contest_info["questions"])])