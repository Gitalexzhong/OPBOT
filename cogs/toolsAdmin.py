import discord
from discord.ext import commands
import time
import configparser
import re
import os


config = configparser.ConfigParser()
config.read('config.ini')


class Admin(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, ctx):

        if config['testing']['disableAdmin'] == "true":
            return

        verifyCommand = config['verification']['webhookCommand']
        if str(ctx.webhook_id) == config['verification']['webhookBotID'] and verifyCommand in ctx.content:
            verifcationName = ctx.content[len(verifyCommand)+1:]
            authChannel = self.client.get_channel(
                int(config['verification']['targetChannelID']))

            user = next((member for member in authChannel.members if str(
                member) == verifcationName), None)

            if user == None:
                user = next((member for member in authChannel.members if str(
                    member) == verifcationName[:-2]), None)

            if user == None:
                reboundChannel = self.client.get_channel(
                    int(config['verification']['errorStateChannel']))
                await reboundChannel.send(f"Manual verificiation required for ({verifcationName})\nUse < !verify @user > in the welcome channel")
                log_usage(f"Manual verify message - {verifcationName}")
            else:
                await verify_user(user, authChannel)
                await ctx.add_reaction('👍')

        elif "!verify " == ctx.content[:8]:

            authReq = discord.utils.get(
                ctx.channel.guild.roles, name=config['adminstration']['level2OverRideRole'])

            if authReq not in ctx.author.roles:
                await ctx.add_reaction('❌')
                return

            match = re.search(r'\d+', ctx.content[8:])
            user = [member for member in ctx.channel.members if
                    member.id == int(match.group())][0]

            log_usage(
                f"Manual Verify request by - {ctx.author.id} as username {ctx.author}")
            await verify_user(user, ctx.channel)
            await ctx.add_reaction('👍')

        elif "admin!debugInfo" == ctx.content and ctx.author.id == int(config['adminstration']['level1OverRide']):

            infoMessage = f'''Setup Info

            Username: {ctx.author.name}
            User ID: {ctx.author.id}
            Channel ID: {ctx.channel.id}
            Server (Guild) ID: {ctx.guild.id}
        
            Discord Usage Info: {discord.version_info}
            '''

            await ctx.channel.send(infoMessage)


async def verify_user(user, channel):
    removalRole = discord.utils.get(
        channel.guild.roles, name=config['verification']['unverifiedRole'])
    verifiedRole = discord.utils.get(
        channel.guild.roles, name=config['verification']['verifiedRole'])

    if removalRole in user.roles:
        await user.remove_roles(removalRole)

    if verifiedRole not in user.roles:
        await user.add_roles(verifiedRole)

    await channel.send(f"Welcome to the server <@{user.id}> !")
    log_usage(f"Verified - {user.id} as username {user}")


def log_usage(msg):
    if not os.path.exists("admin.log"):
        open("admin.log", "w").close()

    with open("admin.log", "a") as file:
        file.write(f"{str(time.time())} || {msg}\n")


async def setup(client):
    await client.add_cog(Admin(client))
    log_usage("Admin Module Reloaded")
    print("Loaded Admin module")
