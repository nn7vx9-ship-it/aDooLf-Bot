import os
import io
import json
import random
import asyncio
import time
import discord
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

GAME_TIME = 15
active_games = set()

SCORES_FILE = "scores.json"

def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_scores(scores):
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=4)

def add_points(user_id, points=10):
    scores = load_scores()
    uid = str(user_id)
    scores[uid] = scores.get(uid, 0) + points
    save_scores(scores)

SAMPLE_QUESTIONS = {
    "general": {
        "easy": [
            {"q": "ما عاصمة الكويت؟", "a": "مدينة الكويت"},
            {"q": "كم عدد أيام الأسبوع؟", "a": "7 أيام"},
            {"q": "ما لون السماء في الأيام الصافية؟", "a": "أزرق"},
            {"q": "كم عدد شهور السنة الهجرية؟", "a": "12 شهراً"},
        ],
        "medium": [
            {"q": "ما أكبر كوكب في المجموعة الشمسية؟", "a": "المشتري"},
            {"q": "ما اللغة الرسمية في البرازيل؟", "a": "البرتغالية"},
        ],
        "hard": [
            {"q": "ما العنصر الكيميائي الذي رمزه Fe؟", "a": "الحديد"},
        ],
    },
    "religious": {
        "easy": [
            {"q": "كم عدد أركان الإسلام؟", "a": "خمسة"},
            {"q": "ما اسم كتاب المسلمين؟", "a": "القرآن الكريم"},
            {"q": "كم عدد الصلوات المفروضة في اليوم والليلة؟", "a": "خمس صلوات"},
            {"q": "ما هي السورة التي تسمى قلب القرآن؟", "a": "سورة يس"},
            {"q": "من هو خاتم الأنبياء والمرسلين؟", "a": "محمد صلى الله عليه وسلم"},
            {"q": "في أي شهر صيام المسلمين؟", "a": "شهر رمضان"},
        ],
        "medium": [
            {"q": "ما السورة التي لا تبدأ بالبسملة؟", "a": "سورة التوبة"},
            {"q": "كم عدد أركان الإيمان؟", "a": "ستة"},
            {"q": "من هو النبي الذي صبر على البلاء؟", "a": "أيوب عليه السلام"},
        ],
        "hard": [
            {"q": "ما السورة التي ذُكرت فيها البسملة مرتين؟", "a": "سورة النمل"},
            {"q": "من هو الصحابي الملقب بأمين هذه الأمة؟", "a": "أبو عبيدة بن الجراح"},
        ],
    },
}

PERSONAL_QUESTIONS = [
    {"q": "كم عمرك الحقيقي حالياً؟", "icon": "🎂"},
    {"q": "متى آخر مرة ضميت أحد من أهلك أو اخوياك؟", "icon": "🫂"},
    {"q": "من هو اعز خوي عندك بالقروب؟", "icon": "👑"},
    {"q": "من هو اول خوي تعرفت عليه بحياتك ولا زلتم مع بعض؟", "icon": "🤝"},
    {"q": "وش أكثر موقف محرج صار لك وأنت صغير؟", "icon": "😅"},
    {"q": "لو عطوك مليون دينار، وش أول شي تشتريه؟", "icon": "💰"},
    {"q": "وش العادة السيئة اللي ودك تغيرها بنفسك؟", "icon": "🚬"},
    {"q": "أكثر لعبة أدمنتها بحياتك ولا يمكن تمل منها؟", "icon": "🎮"},
    {"q": "لو خيروك تعيش بدون إنترنت أسبوع أو بدون أكل مفضل شهر؟", "icon": "📱"},
    {"q": "من هو الشخص اللي مستحيل ترد له طلب؟", "icon": "❤️"},
]

SPEED_SENTENCES = [
    "سبحان الله وبحمده",
    "صلى الله وسلم على محمد",
    "استغفر الله العظيم واتوب اليه",
    "برمج بوت ديسكورد فخم جدا",
    "عاش خوينا بطل الالعاب كله",
    "موت وكبد وسرعة وصاروخ ارض",
]

COUNT_WORDS = [
    {"word": "الكويت", "count": 6},
    {"word": "الرياض", "count": 6},
    {"word": "رمضان", "count": 5},
    {"word": "القرآن", "count": 6},
    {"word": "ديسكورد", "count": 7},
    {"word": "قهوة", "count": 4},
]

def load_questions():
    try:
        with open("questions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return SAMPLE_QUESTIONS

questions = load_questions()

def arabic(text):
    return get_display(arabic_reshaper.reshape(str(text)))

def get_auto_icon(question_text, category):
    q = str(question_text)
    if "الكويت" in q:
        return "🇰🇼"
    elif "السعودية" in q or "الرياض" in q:
        return "🇸🇦"
    elif "الإمارات" in q or "دبي" in q:
        return "🇦🇪"
    elif "مصر" in q or "القاهرة" in q:
        return "🇪🇬"
    elif "اليابان" in q or "طوكيو" in q:
        return "🇯🇵"
    elif "البرازيل" in q:
        return "🇧🇷"
    elif "كوكب" in q or "المجموعة الشمسية" in q:
        return "🪐"
    elif "ماء" in q or "البحر" in q or "السماء" in q:
        return "💧"
    elif "أيام" in q or "شهور" in q or "سنة" in q:
        return "📅"
    
    if category == "religious":
        if "القرآن" in q or "سورة" in q or "كتاب" in q:
            return "📖"
        elif "الصلاة" in q or "أركان" in q:
            return "🕌"
        elif "النبي" in q or "محمد" in q or "الأنبياء" in q:
            return "💚"
        elif "رمضان" in q or "صيام" in q:
            return "🌙"
        else:
            return "⭐"
            
    return "💡"

def make_image(title, text, footer, icon_text="❓"):
    width, height = 1200, 675
    
    if os.path.exists("background.png"):
        img = Image.open("background.png").convert("RGB")
        img = img.resize((width, height))
    else:
        img = Image.new("RGB", (width, height), "#101010")

    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 48)
        text_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 52)
        footer_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
        icon_font = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", 45)
    except OSError:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()
        icon_font = ImageFont.load_default()

    def centered(txt, y, font, fill):
        shaped = arabic(txt)
        box = draw.textbbox((0, 0), shaped, font=font)
        x = (width - (box[2] - box[0])) // 2
        draw.text((x, y), shaped, font=font, fill=fill)

    centered(title, 80, title_font, "#e32636")

    box_box = (150, 200, 1050, 470)
    draw.rounded_rectangle(box_box, radius=25, fill=(15, 5, 5, 200), outline="#e32636", width=4)

    words = str(text).split()
    lines = []
    line = ""

    for word in words:
        test = (line + " " + word).strip()
        shaped = arabic(test)
        if draw.textlength(shaped, font=text_font) > 800 and line:
            lines.append(line)
            line = word
        else:
            line = test

    if line:
        lines.append(line)

    total_height = len(lines) * 70
    y = 200 + (270 - total_height) // 2

    for l in lines:
        centered(l, y, text_font, "white")
        y += 70

    try:
        draw.text((180, 310), icon_text, font=icon_font, fill="white")
        draw.text((980, 310), icon_text, font=icon_font, fill="white")
    except Exception:
        pass

    centered(footer, 595, footer_font, "#dddddd")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def get_random_question_from_category(category):
    cat_data = questions.get(category, {})
    all_questions = []
    for diff in cat_data.values():
        all_questions.extend(diff)
    if not all_questions:
        return None
    return random.choice(all_questions)

async def start_game(ctx, category):
    if ctx.channel.id in active_games:
        return

    active_games.add(ctx.channel.id)

    try:
        question = get_random_question_from_category(category)
        if question is None:
            await ctx.send("ما عندي أسئلة حالياً.")
            return

        label = "عام" if category == "general" else "ديني"
        icon = get_auto_icon(question["q"], category)

        question_image = make_image(
            "السؤال",
            question["q"],
            f"التصنيف: {label} | الوقت: {GAME_TIME} ثانية (+10 نقاط للإجابة الصحيحة)",
            icon_text=icon
        )

        msg_file = discord.File(question_image, filename="question.png")
        await ctx.send(file=msg_file)
        question_image.close()

        def check(m):
            return m.channel == ctx.channel and not m.author.bot

        try:
            user_msg = await bot.wait_for('message', timeout=GAME_TIME, check=check)
            if user_msg.content.strip() == question["a"]:
                add_points(user_msg.author.id, 10)
                await ctx.send(f"كفو {user_msg.author.mention}! إجابتك صحيحة واكتسبت 10 نقاط! 🎉")
        except asyncio.TimeoutError:
            pass

        await asyncio.sleep(2)

        answer_image = make_image(
            "الإجابة الصحيحة",
            question["a"],
            "انتهى الوقت!",
            icon_text="✅"
        )

        ans_file = discord.File(answer_image, filename="answer.png")
        await ctx.send(file=ans_file)
        answer_image.close()

    finally:
        active_games.discard(ctx.channel.id)

@bot.command(name="حروف")
async def letters_count_game(ctx):
    if ctx.channel.id in active_games:
        return
    active_games.add(ctx.channel.id)
    try:
        item = random.choice(COUNT_WORDS)
        img = make_image(
            "تحدي عدد الحروف",
            f"كم عدد حروف كلمة:\n({item['word']}) ؟",
            "اكتب رقم عدد الحروف فقط في الشات خلال 15 ثانية!",
            icon_text="🔢"
        )
        img_file = discord.File(img, filename="letters.png")
        await ctx.send(file=img_file)
        img.close()

        def check(m):
            return m.channel == ctx.channel and not m.author.bot

        try:
            msg = await bot.wait_for('message', timeout=15, check=check)
            if msg.content.strip() == str(item["count"]):
                add_points(msg.author.id, 10)
                await ctx.send(f"كفو يا {msg.author.mention}! إجابتك صحيحة (عددها {item['count']}) وربحت 10 نقاط! 🏆")
            else:
                await ctx.send(f"خطأ! الإجابة الصحيحة هي: **{item['count']}**")
        except asyncio.TimeoutError:
            await ctx.send(f"انتهى الوقت! الإجابة الصحيحة هي: **{item['count']}**")
    finally:
        active_games.discard(ctx.channel.id)

@bot.command(name="سرعة")
async def speed_game(ctx):
    if ctx.channel.id in active_games:
        return
    active_games.add(ctx.channel.id)
    try:
        sentence = random.choice(SPEED_SENTENCES)
        img = make_image(
            "تحدي الكتابة السريعة",
            sentence,
            "أسرع شخص يكتب الجملة بدقة يفوز بـ 20 نقطة!",
            icon_text="⚡"
        )
        img_file = discord.File(img, filename="speed.png")
        await ctx.send(file=img_file)
        img.close()

        start_t = time.time()
        def check(m):
            return m.channel == ctx.channel and not m.author.bot and m.content.strip() == sentence

        try:
            msg = await bot.wait_for('message', timeout=20, check=check)
            elapsed = round(time.time() - start_t, 2)
            add_points(msg.author.id, 20)
            await ctx.send(f"🚀 أسرع كابتن {msg.author.mention}! كتبها في وقت ({elapsed} ثانية) وفاز بـ 20 نقطة لوحده فقط!")
        except asyncio.TimeoutError:
            await ctx.send("⏱️ انتهى الوقت! محد قدر يكتبها بالوقت المحدد.")
    finally:
        active_games.discard(ctx.channel.id)

@bot.command(name="نقاط")
async def points(ctx):
    scores = load_scores()
    pts = scores.get(str(ctx.author.id), 0)
    await ctx.send(f"👤 {ctx.author.mention} رصيدك الحالي هو: **{pts} نقطة** 🌟")

@bot.command(name="ترتيب")
async def leaderboard(ctx):
    scores = load_scores()
    if not scores:
        await ctx.send("ما فيه أي نقاط مسجلة لحد الحين! ابدأ العب واكسب نقاط.")
        return
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = ""
    for idx, (uid, pts) in enumerate(sorted_scores, 1):
        desc += f"**#{idx}** | <@{uid}> — **{pts} نقطة**\n"

    embed = discord.Embed(title="🏆 لوحة الشرف وترتيب اللاعبين", description=desc, color=0xe32636)
    await ctx.send(embed=embed)

@bot.command(name="اسألني")
async def personal_question(ctx):
    item = random.choice(PERSONAL_QUESTIONS)
    img = make_image(
        "سؤال شخصي وسوالف",
        item["q"],
        "أجب بصراحة في الشات!",
        icon_text=item["icon"]
    )
    img_file = discord.File(img, filename="personal.png")
    await ctx.send(file=img_file)
    img.close()

@bot.command(name="اوامر_العاب")
async def games(ctx):
    await ctx.send(
        "**📜 أوامر البوت وقائمة الألعاب:**\n"
        "`!عام` - سؤال عام عشوائي\n"
        "`!ديني` - سؤال ديني عشوائي\n"
        "`!حروف` - تحدي معرفة عدد حروف الكلمة (اكتب الرقم)\n"
        "`!سرعة` - تحدي الكتابة السريعة (أول شخص يكتبها يفوز)\n"
        "`!اسألني` - أسئلة سوالف وشخصية\n"
        "`!نقاط` - لعرض رصيدك ونقاطك\n"
        "`!ترتيب` - لوحة الشرف وترتيب اللاعبين"
    )

@bot.command(name="عام")
async def general(ctx):
    await start_game(ctx, "general")

@bot.command(name="ديني")
async def religious(ctx):
    await start_game(ctx, "religious")

@bot.event
async def on_ready():
    print(f"تم تشغيل البوت بنجاح: {bot.user}")

if not TOKEN:
    raise RuntimeError("لم يتم العثور على DISCORD_TOKEN داخل ملف .env")

bot.run(TOKEN)