import os
from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import utils
import asyncio
import emojis
load_dotenv()

bot = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(bot)

# BOT EVENTS

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        # Sync slash command tree
        synced = await tree.sync()
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

@tree.command(name="identify", description="Link your LeetCode account to your Discord account")
async def identify(interaction: discord.Interaction, user_slug: str):
    user_info = await utils.get_user_info(user_slug)
    # gonna need to turn this error check to a function
    if "error" in user_info:
        embed = discord.Embed(title="Error", description=user_info["message"])
        await interaction.response.send_message(embed=embed)
        return
    # TODO give random easy problem, check user solves, link with database
    # user should already have solved the problem
    await interaction.response.send_message(await utils.get_user_recent_solves(user_slug))

@tree.command(name="profile", description="Get information about a specific user")
async def profile(interaction: discord.Interaction, user_slug: str):
    user_info = await utils.get_user_info(user_slug)
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

# Force fetch question data
force_fetch = False
asyncio.run(utils.load_question_data(force_fetch=force_fetch))
asyncio.run(utils.load_contest_info_data(force_fetch=force_fetch))

bot.run(token=os.getenv('BOT_TOKEN'))