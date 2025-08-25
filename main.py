import nextcord
from nextcord.ext import commands
import json
import os

intents = nextcord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

OWNERS_FILE = "YOUR WAY HERE\\discrod_bot\\owners.json"

def is_in_channel(channel_id):
    def predicate(ctx):
        return ctx.channel.id == channel_id
    return commands.check(predicate)

def load_data():
    if os.path.exists(OWNERS_FILE):
        try:
            with open(OWNERS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            return {}
    return {}

def save_data(data):
    with open(OWNERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@bot.event
async def on_ready():
    print(f"Бот запустился как {bot.user}")

# -------------------- КОМАНДА CREATE --------------------
@bot.command()
@is_in_channel(CHANNEL_ID)
async def create_channel(ctx, channel_name):
    guild = ctx.guild
    user_id = str(ctx.author.id)
    data = load_data()

    if user_id in data:
        await ctx.send("Вы уже создали канал! Сначала удалите его командой !delete.")
        return

    category = guild.get_channel(1408571780901376092)
    if category is None or not isinstance(category, nextcord.CategoryChannel):
        await ctx.send("Категория не найдена или ID неверный.")
        return

    existing = nextcord.utils.get(guild.channels, name=channel_name)
    if existing:
        await ctx.send(f"Канал {channel_name} уже существует.")
        return

    # Канал закрыт для всех кроме создателя
    overwrites = {
        guild.default_role: nextcord.PermissionOverwrite(connect=False, view_channel=False),
        ctx.author: nextcord.PermissionOverwrite(connect=True, view_channel=True)
    }

    new_channel = await guild.create_voice_channel(channel_name, category=category, overwrites=overwrites)
    await ctx.send(f"Голосовой канал {channel_name} создан! Доступ есть только у вас.")

    data[user_id] = {"channel_name": new_channel.name, "channel_id": new_channel.id, "allowed": []}
    save_data(data)

# -------------------- КОМАНДА DELETE --------------------
@bot.command()
@is_in_channel(CHANNEL_ID)
async def delete(ctx):
    guild = ctx.guild
    user_id = str(ctx.author.id)
    data = load_data()

    if user_id not in data:
        await ctx.send("У вас нет созданного канала для удаления.")
        return

    channel_id = data[user_id]["channel_id"]
    channel = guild.get_channel(channel_id)
    if channel:
        await channel.delete()
        await ctx.send(f"Ваш канал {data[user_id]['channel_name']} удалён!")

    del data[user_id]
    save_data(data)

# -------------------- КОМАНДА ALLOW --------------------
@bot.command()
@is_in_channel(CHANNEL_ID)
async def allow(ctx, member: nextcord.Member):
    guild = ctx.guild
    user_id = str(ctx.author.id)
    data = load_data()

    if user_id not in data:
        await ctx.send("У вас нет созданного канала для управления доступом.")
        return

    allowed = data[user_id].get("allowed", [])
    if member.id in allowed:
        await ctx.send(f"{member.display_name} уже допущен.")
        return

    channel = guild.get_channel(data[user_id]["channel_id"])
    if not channel:
        await ctx.send("Канал не найден.")
        return

    # Даем доступ пользователю
    await channel.set_permissions(member, connect=True, view_channel=True)
    allowed.append(member.id)
    data[user_id]["allowed"] = allowed
    save_data(data)
    await ctx.send(f"{member.display_name} теперь допущен к вашему каналу.")

# -------------------- КОМАНДА UNALLOW --------------------
@bot.command()
@is_in_channel(CHANNEL_ID)
async def unallow(ctx, member: nextcord.Member):
    guild = ctx.guild
    user_id = str(ctx.author.id)
    data = load_data()

    if user_id not in data:
        await ctx.send("У вас нет созданного канала для управления доступом.")
        return

    allowed = data[user_id].get("allowed", [])
    if member.id not in allowed:
        await ctx.send(f"{member.display_name} не был допущен.")
        return

    channel = guild.get_channel(data[user_id]["channel_id"])
    if channel:
        await channel.set_permissions(member, overwrite=None)

    allowed.remove(member.id)
    data[user_id]["allowed"] = allowed
    save_data(data)
    await ctx.send(f"{member.display_name} больше не имеет доступа к вашему каналу.")


bot.run('YOURE TOKEN HERE')
