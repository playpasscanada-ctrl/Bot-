import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import os
from flask import Flask
from threading import Thread

# ================= CONFIGURATION =================
# Apni API Keys yahan daalein (Ya Environment Variables use karein best hai)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ================= FLASK SERVER (For Render Web Service) =================
app = Flask('')

@app.route('/')
def home():
    return "I am alive! Bot is running. 🚀"

def run_http():
    # Render automatically assigns a PORT via environment variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ================= AI SETUP (GEMINI) =================
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # 'gemini-1.5-flash' use kar rahe hain jo FREE aur FAST hai
    model = genai.GenerativeModel('gemini-pro')
else:
    print("⚠️ WARNING: GEMINI_API_KEY nahi mili!")

# ================= BOT SETUP =================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} commands globally.")
    except Exception as e:
        print(f"❌ Sync Error: {e}")

# ================== ON MENTION (TAG) LOGIC ==================
@bot.event
async def on_message(message):
    # 1. Agar message khud bot ka hai, to ignore karo
    if message.author == bot.user:
        return

    # 2. Agar koi Bot ko TAG kare (Mention)
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        # User ka message saaf karein (Tag hatayein taaki AI confuse na ho)
        clean_text = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        # Agar khali tag kiya ho (Bina kuch likhe)
        if not clean_text:
            clean_text = "Haan bhai, kya haal hai? Kuch poocho toh sahi!"

        # Typing indicator (Taaki user ko lage bot likh raha hai)
        async with message.channel.typing():
            try:
                if not GEMINI_API_KEY:
                    await message.reply("❌ Admin ne API Key set nahi ki hai.")
                    return

                # AI Prompt (Yahan bot ka attitude set karo)
                prompt = f"You are a savage, funny, and roasted Discord bot. User said: '{clean_text}'. Reply in Hinglish (Hindi+English) short and funny."
                
                # Generate Answer
                response = await model.generate_content_async(prompt)
                reply_text = response.text

                # Message bhejo
                await message.reply(reply_text)

            except Exception as e:
                await message.reply(f"❌ Dimag kharab ho gaya mera (Error): {e}")

    # 3. Ye line ZAROORI hai, warna baaki commands (SLASH) kaam nahi karengi
    await bot.process_commands(message)

# ================= COMMAND: /ask (AI Chat) =================
@bot.tree.command(name="ask", description="Ask anything to the AI Bot")
async def ask(interaction: discord.Interaction, question: str):
    # 1. Defer (User ko wait karao)
    await interaction.response.defer()

    try:
        if not GEMINI_API_KEY:
            await interaction.followup.send("❌ Admin ne API Key set nahi ki hai.")
            return

                # 3. Flirty/Romantic Prompt (Safe but Funny)
        prompt = f"You are a very flirty, romantic, and playful girlfriend/boyfriend AI. You love the user and always try to impress them with cheesy pickup lines and romantic Hinglish compliments. Be dramatic and funny. Question: {question}"
        
        # 3. Generate Answer
        response = await model.generate_content_async(prompt)
        text = response.text

        # Discord limit check (2000 chars)
        if len(text) > 1900:
            text = text[:1900] + "... (Answer too long)"

        # 4. Send Embed
        embed = discord.Embed(description=text, color=0x3498db)
        embed.set_author(name="Gemini AI 🤖", icon_url="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d473d88634747ae4.svg")
        embed.set_footer(text=f"Asked by {interaction.user.name}")
        
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}")

# ================= MAIN ENTRY POINT =================
if __name__ == "__main__":
    if DISCORD_TOKEN:
        keep_alive() # Web server start karo
        bot.run(DISCORD_TOKEN)
    else:
        print("❌ Error: DISCORD_TOKEN nahi mila! Environment Variable check karo.")
