import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

# Load environment variables locally (from .env)
load_dotenv()

TOKEN = os.getenv("TOKEN")
MONGO = os.getenv("MONGO")
PREFIX = os.getenv("PREFIX", "!")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ---------- MongoDB Setup ----------
client = MongoClient(MONGO)
db = client["guardian"]
cases = db["cases"]

# ---------- Ready ----------
@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")

# ---------- User Info ----------
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title="User Info", color=0x2b2d31)
    embed.add_field(name="Username", value=str(member))
    embed.add_field(name="UserID", value=member.id)
    embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d"))
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

# ---------- Ban by ID ----------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, user_id: int, *, reason="No reason provided"):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.ban(user, reason=reason)
        cases.insert_one({
            "user": user_id,
            "action": "ban",
            "reason": reason,
            "moderator": ctx.author.id,
            "time": datetime.utcnow()
        })
        await ctx.send(f"Banned {user} | ID: {user_id}")
    except Exception as e:
        await ctx.send(f"Failed to ban ID {user_id}: {e}")

# ---------- Kick ----------
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    if member.top_role >= ctx.author.top_role:
        return await ctx.send("You cannot punish someone with equal/higher role.")
    await member.kick(reason=reason)
    await ctx.send(f"Kicked {member}")

# ---------- Warn ----------
@bot.command()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    cases.insert_one({
        "user": member.id,
        "action": "warn",
        "reason": reason,
        "moderator": ctx.author.id,
        "time": datetime.utcnow()
    })
    try:
        await member.send(f"You were warned in {ctx.guild.name}: {reason}")
    except:
        pass
    await ctx.send(f"{member} has been warned.")

# ---------- Message Delete Log ----------
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    channel = discord.utils.get(message.guild.text_channels, name="message-logs")
    if not channel:
        return
    embed = discord.Embed(title="Message Deleted", color=0xff0000)
    embed.add_field(name="User", value=f"{message.author} ({message.author.id})")
    embed.add_field(name="Channel", value=message.channel.mention)
    embed.add_field(name="Content", value=message.content[:1000] or "None")
    await channel.send(embed=embed)

# ---------- Message Edit Log ----------
@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    channel = discord.utils.get(before.guild.text_channels, name="message-logs")
    if not channel:
        return
    embed = discord.Embed(title="Message Edited", color=0x00ff00)
    embed.add_field(name="User", value=f"{before.author} ({before.author.id})")
    embed.add_field(name="Channel", value=before.channel.mention)
    embed.add_field(name="Before", value=before.content[:1000] or "None")
    embed.add_field(name="After", value=after.content[:1000] or "None")
    await channel.send(embed=embed)

# ---------- Run Bot ----------
bot.run(TOKEN)
