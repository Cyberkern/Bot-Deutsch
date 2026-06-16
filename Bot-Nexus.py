"""
╔══════════════════════════════════════════════════════════╗
║        🤖 ALL-IN-ONE DISCORD BOT – Slash Commands       ║
║                                                          ║
║  BOT TOKEN → Als Umgebungsvariable BOT_TOKEN setzen     ║
║  (niemals direkt hier eintragen und auf GitHub pushen!) ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import threading
import random
from datetime import datetime
from flask import Flask

# ─────────────────────────────────────────────
#  🔑 BOT TOKEN
#  → Auf Render.com als Umgebungsvariable setzen:
#    Key:   BOT_TOKEN
#    Value: Dein echter Token
# ─────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "DEIN_BOT_TOKEN_HIER")

# ─────────────────────────────────────────────
#  ⚙️  Konfiguration
# ─────────────────────────────────────────────
PORT = int(os.getenv("PORT", 10000))

# ─────────────────────────────────────────────
#  🌐 Flask-Webserver  (Render braucht einen
#     offenen Port, sonst gilt der Service
#     als abgestürzt)
# ─────────────────────────────────────────────
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Discord Bot läuft!", 200

@flask_app.route("/health")
def health():
    name = bot.user.name if bot.user else "wird gestartet…"
    return {"status": "ok", "bot": name}, 200

def webserver_starten():
    flask_app.run(host="0.0.0.0", port=PORT)

# ─────────────────────────────────────────────
#  🤖 Bot-Einrichtung
# ─────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

class MeinBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Slash-Commands global synchronisieren
        # (dauert bis zu 1 Stunde bei Discord – für Tests: guild-spezifisch)
        await self.tree.sync()
        print("✅ Slash-Commands synchronisiert!")

bot = MeinBot()

# ══════════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"✅ Eingeloggt als {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="/help | All-in-One Bot"
        )
    )

@bot.event
async def on_member_join(member: discord.Member):
    kanal = member.guild.system_channel
    if kanal:
        embed = discord.Embed(
            title="👋 Willkommen!",
            description=(
                f"Herzlich willkommen auf **{member.guild.name}**, {member.mention}!\n"
                f"Du bist Mitglied **#{member.guild.member_count}**."
            ),
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await kanal.send(embed=embed)

@bot.event
async def on_member_remove(member: discord.Member):
    kanal = member.guild.system_channel
    if kanal:
        embed = discord.Embed(
            title="👋 Auf Wiedersehen!",
            description=f"**{member}** hat den Server verlassen.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        await kanal.send(embed=embed)

# ──────────────────────────────────────────────
#  XP-System (In-Memory)
# ──────────────────────────────────────────────
xp_daten: dict[int, dict] = {}

def xp_fuer_level(level: int) -> int:
    return 100 * (level ** 2)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    uid = message.author.id
    if uid not in xp_daten:
        xp_daten[uid] = {"xp": 0, "level": 1}

    xp_daten[uid]["xp"] += random.randint(5, 15)
    naechstes_level = xp_daten[uid]["level"] + 1

    if xp_daten[uid]["xp"] >= xp_fuer_level(naechstes_level):
        xp_daten[uid]["level"] = naechstes_level
        await message.channel.send(
            f"🎉 {message.author.mention} ist jetzt **Level {naechstes_level}**! Glückwunsch!"
        )

    await bot.process_commands(message)

# ══════════════════════════════════════════════
#  📋 ALLGEMEINE SLASH-COMMANDS
# ══════════════════════════════════════════════

@bot.tree.command(name="help", description="Zeigt alle verfügbaren Befehle an")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Hilfe – Alle Slash-Commands",
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="📋 Allgemein",
        value="`/ping` `/info` `/avatar` `/serverinfo` `/userinfo`",
        inline=False)
    embed.add_field(name="🎲 Spaß",
        value="`/würfel` `/münze` `/8ball` `/zitat`",
        inline=False)
    embed.add_field(name="⚙️ Moderation",
        value="`/kick` `/ban` `/mute` `/unmute` `/clear`",
        inline=False)
    embed.add_field(name="🎵 Voice",
        value="`/join` `/leave`",
        inline=False)
    embed.add_field(name="⭐ XP-System",
        value="`/xp` `/rangliste`",
        inline=False)
    embed.set_footer(text="Alle Befehle beginnen mit /")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ping", description="Zeigt die Latenz des Bots")
async def slash_ping(interaction: discord.Interaction):
    latenz = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latenz: **{latenz} ms**")


@bot.tree.command(name="info", description="Informationen über den Bot")
async def slash_info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Bot-Info",
        description="Ein kostenloser All-in-One Discord Bot auf Deutsch!",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Server",  value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Nutzer",  value=str(len(set(bot.get_all_members()))), inline=True)
    embed.set_footer(text="Entwickelt mit discord.py")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="avatar", description="Zeigt den Avatar eines Nutzers")
@app_commands.describe(mitglied="Der Nutzer, dessen Avatar angezeigt werden soll")
async def slash_avatar(interaction: discord.Interaction, mitglied: discord.Member = None):
    mitglied = mitglied or interaction.user
    embed = discord.Embed(title=f"🖼️ Avatar von {mitglied}", color=discord.Color.blurple())
    embed.set_image(url=mitglied.display_avatar.url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="serverinfo", description="Informationen über diesen Server")
async def slash_serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=f"🏠 {g.name}", color=discord.Color.blurple(),
                          timestamp=datetime.utcnow())
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="👑 Besitzer",   value=g.owner.mention,   inline=True)
    embed.add_field(name="👥 Mitglieder", value=g.member_count,    inline=True)
    embed.add_field(name="📁 Kanäle",     value=len(g.channels),   inline=True)
    embed.add_field(name="🎭 Rollen",     value=len(g.roles),      inline=True)
    embed.add_field(name="📅 Erstellt",   value=g.created_at.strftime("%d.%m.%Y"), inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="userinfo", description="Informationen über einen Nutzer")
@app_commands.describe(mitglied="Der Nutzer, über den du Infos möchtest")
async def slash_userinfo(interaction: discord.Interaction, mitglied: discord.Member = None):
    m = mitglied or interaction.user
    embed = discord.Embed(title=f"👤 {m}", color=m.color, timestamp=datetime.utcnow())
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.add_field(name="ID",          value=str(m.id), inline=True)
    embed.add_field(name="Beitritt",    value=m.joined_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="Registriert", value=m.created_at.strftime("%d.%m.%Y"), inline=True)
    rollen = " ".join(r.mention for r in m.roles[1:]) or "Keine"
    embed.add_field(name="Rollen", value=rollen, inline=False)
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════
#  🎲 SPASS-BEFEHLE
# ══════════════════════════════════════════════

@bot.tree.command(name="würfel", description="Wirft einen Würfel")
@app_commands.describe(seiten="Anzahl der Seiten (Standard: 6)")
async def slash_wuerfel(interaction: discord.Interaction, seiten: int = 6):
    seiten = max(2, seiten)
    ergebnis = random.randint(1, seiten)
    await interaction.response.send_message(
        f"🎲 Du hast eine **{ergebnis}** gewürfelt! *(1–{seiten})*"
    )


@bot.tree.command(name="münze", description="Wirft eine Münze")
async def slash_muenze(interaction: discord.Interaction):
    seite = random.choice(["Kopf 🪙", "Zahl 🔵"])
    await interaction.response.send_message(f"Die Münze zeigt: **{seite}**!")


@bot.tree.command(name="8ball", description="Stellt der Glaskugel eine Ja/Nein-Frage")
@app_commands.describe(frage="Deine Frage an die Glaskugel")
async def slash_achtball(interaction: discord.Interaction, frage: str):
    antworten = [
        "🟢 Definitiv ja!", "🟢 Ja, sicher!", "🟢 Sehr wahrscheinlich.",
        "🟡 Vielleicht…", "🟡 Schwer zu sagen.", "🟡 Frag später nochmal.",
        "🔴 Eher nicht.", "🔴 Nein.", "🔴 Auf keinen Fall!"
    ]
    embed = discord.Embed(title="🎱 Magische 8-Ball", color=discord.Color.dark_purple())
    embed.add_field(name="❓ Frage",   value=frage,                   inline=False)
    embed.add_field(name="💬 Antwort", value=random.choice(antworten), inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="zitat", description="Sendet ein zufälliges Motivationszitat")
async def slash_zitat(interaction: discord.Interaction):
    zitate = [
        "„Der Weg ist das Ziel." – Konfuzius",
        "„Glaube an dich selbst und alles ist möglich."",
        "„Erfolg ist die Summe kleiner Anstrengungen."",
        "„Träume groß, arbeite hart, bleib bescheiden."",
        "„Wer aufhört, besser zu werden, hat aufgehört, gut zu sein."",
    ]
    embed = discord.Embed(
        description=f"💬 {random.choice(zitate)}",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════
#  ⚙️  MODERATION
# ══════════════════════════════════════════════

@bot.tree.command(name="kick", description="Kickt ein Mitglied vom Server")
@app_commands.describe(mitglied="Das Mitglied, das gekickt werden soll",
                       grund="Der Grund für den Kick")
@app_commands.checks.has_permissions(kick_members=True)
async def slash_kick(interaction: discord.Interaction,
                     mitglied: discord.Member,
                     grund: str = "Kein Grund angegeben"):
    await mitglied.kick(reason=grund)
    await interaction.response.send_message(f"👢 **{mitglied}** wurde gekickt. Grund: {grund}")


@bot.tree.command(name="ban", description="Bannt ein Mitglied vom Server")
@app_commands.describe(mitglied="Das Mitglied, das gebannt werden soll",
                       grund="Der Grund für den Bann")
@app_commands.checks.has_permissions(ban_members=True)
async def slash_ban(interaction: discord.Interaction,
                    mitglied: discord.Member,
                    grund: str = "Kein Grund angegeben"):
    await mitglied.ban(reason=grund)
    await interaction.response.send_message(f"🔨 **{mitglied}** wurde gebannt. Grund: {grund}")


@bot.tree.command(name="mute", description="Mutet ein Mitglied")
@app_commands.describe(mitglied="Das Mitglied, das gemutet werden soll")
@app_commands.checks.has_permissions(manage_roles=True)
async def slash_mute(interaction: discord.Interaction, mitglied: discord.Member):
    await interaction.response.defer()
    muted_rolle = discord.utils.get(interaction.guild.roles, name="Muted")
    if not muted_rolle:
        muted_rolle = await interaction.guild.create_role(name="Muted")
        for kanal in interaction.guild.channels:
            await kanal.set_permissions(muted_rolle, send_messages=False, speak=False)
    await mitglied.add_roles(muted_rolle)
    await interaction.followup.send(f"🔇 **{mitglied}** wurde gemutet.")


@bot.tree.command(name="unmute", description="Entmutet ein Mitglied")
@app_commands.describe(mitglied="Das Mitglied, das entmutet werden soll")
@app_commands.checks.has_permissions(manage_roles=True)
async def slash_unmute(interaction: discord.Interaction, mitglied: discord.Member):
    muted_rolle = discord.utils.get(interaction.guild.roles, name="Muted")
    if muted_rolle and muted_rolle in mitglied.roles:
        await mitglied.remove_roles(muted_rolle)
        await interaction.response.send_message(f"🔊 **{mitglied}** wurde entmutet.")
    else:
        await interaction.response.send_message(f"❌ **{mitglied}** ist nicht gemutet.")


@bot.tree.command(name="clear", description="Löscht eine Anzahl von Nachrichten (max. 100)")
@app_commands.describe(anzahl="Wie viele Nachrichten sollen gelöscht werden?")
@app_commands.checks.has_permissions(manage_messages=True)
async def slash_clear(interaction: discord.Interaction, anzahl: int = 5):
    anzahl = min(max(1, anzahl), 100)
    await interaction.response.defer(ephemeral=True)
    geloescht = await interaction.channel.purge(limit=anzahl)
    await interaction.followup.send(
        f"🗑️ **{len(geloescht)}** Nachrichten gelöscht.", ephemeral=True
    )

# Fehlerbehandlung für fehlende Rechte bei Slash-Commands
@slash_kick.error
@slash_ban.error
@slash_mute.error
@slash_unmute.error
@slash_clear.error
async def moderation_fehler(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ Du hast keine Berechtigung für diesen Befehl.", ephemeral=True
        )
    else:
        await interaction.response.send_message(f"❌ Fehler: `{error}`", ephemeral=True)

# ══════════════════════════════════════════════
#  🎵 VOICE
# ══════════════════════════════════════════════

@bot.tree.command(name="join", description="Bot tritt deinem Voice-Channel bei")
async def slash_join(interaction: discord.Interaction):
    if interaction.user.voice is None:
        await interaction.response.send_message("❌ Du bist in keinem Voice-Channel!", ephemeral=True)
        return
    kanal = interaction.user.voice.channel
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(kanal)
    else:
        await kanal.connect()
    await interaction.response.send_message(f"🎵 Verbunden mit **{kanal.name}**.")


@bot.tree.command(name="leave", description="Bot verlässt den Voice-Channel")
async def slash_leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Voice-Channel verlassen.")
    else:
        await interaction.response.send_message("❌ Ich bin in keinem Voice-Channel.", ephemeral=True)

# ══════════════════════════════════════════════
#  ⭐ XP-SYSTEM
# ══════════════════════════════════════════════

@bot.tree.command(name="xp", description="Zeigt dein aktuelles XP und Level")
@app_commands.describe(mitglied="Nutzer, dessen XP du sehen möchtest (leer = du selbst)")
async def slash_xp(interaction: discord.Interaction, mitglied: discord.Member = None):
    m    = mitglied or interaction.user
    data = xp_daten.get(m.id, {"xp": 0, "level": 1})
    naechstes = xp_fuer_level(data["level"] + 1)
    embed = discord.Embed(title=f"⭐ XP von {m.display_name}", color=discord.Color.gold())
    embed.add_field(name="Level", value=str(data["level"]),            inline=True)
    embed.add_field(name="XP",    value=f"{data['xp']} / {naechstes}", inline=True)
    embed.set_thumbnail(url=m.display_avatar.url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="rangliste", description="Zeigt die Top-10 XP-Rangliste")
async def slash_rangliste(interaction: discord.Interaction):
    sortiert = sorted(xp_daten.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]
    embed = discord.Embed(title="🏆 XP-Rangliste", color=discord.Color.gold())
    if not sortiert:
        embed.description = "Noch keine XP-Daten vorhanden."
    for platz, (uid, data) in enumerate(sortiert, 1):
        nutzer = interaction.guild.get_member(uid)
        name   = nutzer.display_name if nutzer else f"Nutzer {uid}"
        embed.add_field(
            name=f"{platz}. {name}",
            value=f"Level {data['level']} · {data['xp']} XP",
            inline=False
        )
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════
#  🚀 START
# ══════════════════════════════════════════════

if __name__ == "__main__":
    threading.Thread(target=webserver_starten, daemon=True).start()
    print(f"🌐 Webserver läuft auf Port {PORT}")
    bot.run(BOT_TOKEN)