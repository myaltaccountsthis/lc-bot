import asyncio
import os
from datetime import datetime
from fileinput import filename
from importlib.metadata import files
from itertools import compress

import discord
from discord import app_commands
from dotenv import load_dotenv

import emojis
import utils
import database

load_dotenv()

bot = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(bot)

USERNAME_MAX_LENGTH = 30

db = database.Database()

# BOT EVENTS

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        # Sync slash command tree
        synced = await tree.sync()
        # Check server every 5 minutes
        asyncio.create_task(check_server())
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# GENERAL COMMANDS

@tree.command(name="ping", description="Display latency information")
async def ping(interaction: discord.Interaction):
    text = f'Pong! {round (bot.latency * 1000)} ms initial.'
    # Initial ping message
    await interaction.response.send_message(text)
    msg = await interaction.original_response()

    # Edit the message with the latency of original response
    time = round((msg.created_at - interaction.created_at).total_seconds() * 1000)
    await msg.edit(content=text + f' {time} ms round-trip.')


# PROBLEM COMMANDS

# Displays a random leetcode problem, can specifiy if you want premium problems
@tree.command(name="random", description="Get a random question from LeetCode")
@app_commands.choices(difficulty=[
    app_commands.Choice(name="Easy", value="Easy"),
    app_commands.Choice(name="Medium", value="Medium"),
    app_commands.Choice(name="Hard", value="Hard"),
    app_commands.Choice(name="Random", value="Random")
])
async def randomQuestion(interaction: discord.Interaction, difficulty: app_commands.Choice[str] = "Random", allow_premium: bool = False):
    await interaction.response.send_message(await utils.random_question(difficulty, allow_premium))


# CONTEST COMMANDS

# Group for all contest related commands
contest = app_commands.Group(name="contest", description="Commands related to contests")
# Command to get problems from a specific contest
@contest.command(name="info", description="Get information about a specific contest")
@app_commands.choices(contest_type=[
    app_commands.Choice(name="Weekly", value="weekly"),
    app_commands.Choice(name="Biweekly", value="biweekly")
])
async def info(interaction: discord.Interaction, contest_type: app_commands.Choice[str] = None, contest_number: int = None):
    contest_info = await utils.get_contest_info(contest_type.value if contest_type else None, contest_number)
    if contest_info is None:
        await interaction.response.send_message(f"Could not find {contest_type.name} Contest {contest_number}.")
    elif type(contest_info) == str:
        await interaction.response.send_message(contest_info)
    else:
        embed = discord.Embed(title=contest_info["title"], url=contest_info["url"])
        # add each hyperlink to the embed as a line in description
        embed.color = discord.Color.orange()
        embed.description = "\n".join([f"**{i + 1}.** [{question['title']}]({question['url']}) *({question['difficulty']})*"
                                       for i, question in enumerate(contest_info["questions"])])

        embed.set_footer(text=f"Contest held on {datetime.fromtimestamp(contest_info["startTime"]).strftime('%b %d, %Y')}")
        await interaction.response.send_message(embed=embed)
tree.add_command(contest)


# USER COMMANDS

active_identification = {}
verified_users = {}
for user in db.get_all_users():
    verified_users[user[0]] = user[1]

@tree.command(name="identify", description="Link your LeetCode account to your Discord account")
async def identify(interaction: discord.Interaction, username: str):
    if (len(username) > USERNAME_MAX_LENGTH):
        await interaction.response.send_message(f"Username too long, must be less than {USERNAME_MAX_LENGTH} characters.")
        return
    
    user_id = interaction.user.id

    # allow users to reverify only if the new username is different
    if user_id in verified_users and verified_users[user_id].lower() == username.lower():
        await interaction.response.send_message(f"You have already verified that you are `{username}` on LeetCode.")
        return

    user_info = await utils.get_user_info(username)

    # TODO: turn this error check to a function
    if "error" in user_info:
        embed = discord.Embed(title="Error", description=user_info["message"])
        await interaction.response.send_message(embed=embed)
        return

    # get the official username from the user info
    username = user_info["username"]

    recent_ac_list = await utils.get_user_recent_solves(username)
    embed = discord.Embed(title="Verification Instructions", color=discord.Color.orange())

    unique_code = utils.generate_unique_code()

    if len(recent_ac_list) == 0:
        # use add-two-integers
        embed.description = f"Please verify that you are `{username}` on LeetCode by adding\n```Verifying with Leetcode Bot - {unique_code}```\nas a note on your most recent **accepted** submission. If you don't have one, you can use [2235. Add Two Integers]({utils.PROBLEM_LINK}add-two-integers/)."
    else:
        last_ac = recent_ac_list[0]
        embed.description = f"Please verify that you are `{username}` on LeetCode by adding\n\n```Verifying with Leetcode Bot - {unique_code}```\nas a note on either your most recent **accepted** submission **[({last_ac['title']})]({utils.PROBLEM_LINK + last_ac['titleSlug']}/submissions/{last_ac['id']})** or on a new one."

    embed.set_footer(text="Click the button below when you're finished verifying")

    # Upload the image to discord
    # TODO: store image as an external url instead
    image = utils.IDENTIFY_IMAGE()
    embed.set_image(url=f"attachment://{image.filename}")

    if user_id in active_identification:
        active = active_identification[user_id]
        button = active[2]
        message = active[3]
        # disable the previous button
        button.button_callback.disabled = True
        await message.edit(view=button)

    button = FinishIdentification(user_id)
    await interaction.response.send_message(embed=embed, file=image, view=button)

    # store the active identification session
    active_identification[user_id] = [username, unique_code, button, await interaction.original_response()]

class FinishIdentification(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="I'm finished", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction: discord.Interaction, button: discord.Button):
        user_id = interaction.user.id

        # check if the button is clicked by the same user
        if user_id != self.user_id:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return
        if user_id not in active_identification:
            await interaction.response.send_message("You haven't started the verification process yet.", ephemeral=True)
            return

        # error handling
        username, unique_code, target_button, message = active_identification[user_id]
        if self != target_button:
            return
        user_info = await utils.get_user_info(username)
        if "error" in user_info:
            embed = discord.Embed(title="Error", description=user_info["message"])
            await interaction.response.send_message(embed=embed)
            return

        # check if the user has added the note
        recent_ac_list = await utils.get_user_recent_solves(username)
        found = False
        valid_note = f"Verifying with Leetcode Bot - {unique_code}"
        for submission in recent_ac_list:
            if len(submission["notes"]) <= len(valid_note) + 4 and valid_note == str(submission["notes"]).strip():
                found = True
                break

        # if the note is found, add the user to the verified list
        if found:
            verified_users[user_id] = username
            db.add_user(user_id, username)
            button.disabled = True
            await message.edit(view=self)
            del active_identification[user_id]
            await interaction.response.send_message(f"Successfully verified that you are {username} on LeetCode.")
        else:
            await interaction.response.send_message("Could not find the verification note on your **recent accepted submissions**. Please try again.", ephemeral=True)


@tree.command(name="profile", description="Get information about a specific user")
async def profile(interaction: discord.Interaction, username: str = None):
    # if no username is specified, use the discord user's leetcode username
    if username is None:
        if interaction.user.id in verified_users:
            username = verified_users[interaction.user.id]
        else:
            await interaction.response.send_message("Please specify a user to get information about.")
            return
    
    if (len(username) > USERNAME_MAX_LENGTH):
        await interaction.response.send_message(f"Username too long, must be less than {USERNAME_MAX_LENGTH} characters.")
        return
    
    user_info = await utils.get_user_info(username)
    if "error" in user_info:
        embed = discord.Embed(title="Error", description=user_info["message"])
        await interaction.response.send_message(embed=embed)
        return
        
    num_solved = {}
    for category in user_info["problems_solved"]["acSubmissionNum"]:
        num_solved[category["difficulty"]] = category["count"]
    lines = [
        "**Contests**",
        f"Rating: {round(user_info['rating'], 1)} {emojis.get_emoji(user_info["badge"])}",
        f"Top {user_info["top_percentage"]}%",
        "",
        f"**Problems Solved:**",
        f"Easy: {num_solved["Easy"]}",
        f"Medium: {num_solved["Medium"]}",
        f"Hard: {num_solved["Hard"]}",
        f"Total: {num_solved["All"]}"
    ]

    embed = discord.Embed()
    embed.set_author(name=user_info["username"], icon_url=user_info["user_avatar"], url=f"https://leetcode.com/u/{user_info["username"]}")
    embed.description = "\n".join(lines)
    await interaction.response.send_message(embed=embed)

# USELESS COMMANDS

@tree.command(name="daily_time", description="sus", nsfw=True)
async def gif(interaction: discord.Interaction):
    await interaction.response.send_message("https://cdn.discordapp.com/attachments/1124365604523081748/1296155709393735853/leetcodedaily.gif?ex=6713e592&is=67129412&hm=fec412a88da2b6ff773ae3a8419c06efb9218119d9f63b8129797fae31087bba&")

@tree.command(name="gf", description="am 1500 rated", nsfw=True)
async def gif(interaction: discord.Interaction):
    await interaction.response.send_message("https://cdn.discordapp.com/attachments/1190447467720868024/1287496458878062716/leetcodegf.gif?ex=6716ac04&is=67155a84&hm=b45d538b2c2e0d9ef44018772ad23ea35284d1fd1825d90a143b1b924fe0fe82&")

# load data from server
asyncio.run(utils.load_question_data(check_server=True))
asyncio.run(utils.load_contest_info_data(check_server=True))

# Check server every 5 minutes
async def check_server():
    while True:
        await asyncio.sleep(300)
        await utils.load_question_data(check_server=True)
        await utils.load_contest_info_data(check_server=True)

bot.run(token=os.getenv('BOT_TOKEN'))