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
question_info_from_slug = {}
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

        # Store the question info into a dict for easy access
        for question in question_data:
            question["url"] = PROBLEM_LINK + question["titleSlug"]
            question_info_from_slug[question["titleSlug"]] = question
        print("Loaded question data!")

# Loads the contest info data by calling the query, stores into array and dict, TIME_EXPENSIVE
async def load_contest_info_data(forceFetch=False):
    global contest_info_data, contest_info_from_slug
    await load_question_data()
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
        # contest_info_data.reverse()

        # Store the contest info into a dict for easy access
        for contest in result:
            contest["url"] = CONTEST_LINK + contest["titleSlug"]
            for question in contest["questions"]:
                question_from_slug = question_info_from_slug[question["titleSlug"]]
                question["url"] = question_from_slug["url"]
                question["difficulty"] = question_from_slug["difficulty"]
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
    return question["url"]
    
# Returns the link of a random question with the given difficulty
async def random_question(allow_premium, difficulty):
    await load_question_data()
    # The data of a random question, keep looping if
    # it is a premium question and we don't want premium questions
    # it is a question of the wrong difficulty
    question = None
    while True:
        question = question_data[random.randrange(0, len(question_data))]
        if (allow_premium or not question["paidOnly"]) && lower(question["difficulty"]) == lower(difficulty):
            break
    return question["url"]

# Get generic info (questions and links) of a specific contest
# Returns None if the contest does not exist
async def get_contest_info(contest_type, contest_number):
    if contest_type is None and contest_number:
        return "You cannot specify a contest number without a contest type"

    await load_contest_info_data()

    # Creating a valid title slug
    if contest_number is None:
        if contest_type is None:
            # Get the latest contest
            title_slug = contest_info_data[0]["titleSlug"]
        else:
            # Get the latest contest of the specified type
            type_bool = contest_type == "biweekly"
            curr = 0
            # Max of 3 iterations
            while ("biweekly" in contest_info_data[curr]["titleSlug"]) != type_bool:
                curr += 1
            title_slug = contest_info_data[curr]["titleSlug"]
    else:
        # Get the specified contest
        title_slug = f"{contest_type}-contest-{contest_number}"
        if contest_type == "weekly" and contest_number < 58:
            title_slug = "leetcode-" + title_slug

    # Check if the contest exists
    if title_slug not in contest_info_from_slug:
        return None

    return contest_info_from_slug[title_slug]
