"""
Ethio-Agri Advisor - Telegram Bot
Farmers get advice via Telegram (works on any phone!)
"""

import os
import logging
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import requests
import pandas as pd
import numpy as np

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token from @BotFather (Get yours at t.me/BotFather)
TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your token

# Ethiopian crop data
CROP_DATA = {
    'teff': {
        'name_am': 'ጤፍ',
        'icon': '🌾',
        'planting': 'መጋቢት (የበልግ ዝናብ መጀመሪያ)',
        'planting_en': 'February (start of Belg rains)',
        'fertilizer': '50kg DAP በሄክታር + 50kg Urea ከ30 ቀን በኋላ',
        'fertilizer_en': '50kg DAP/ha + 50kg Urea after 30 days',
        'harvest': '90-100 ቀናት (ቅጠሎች ሲገረፉ)',
        'harvest_en': '90-100 days (when leaves turn yellow)',
        'pests': 'የሰራተኛ ትል (አረንጓዴ ትሎች)',
        'pests_en': 'Armyworm (green caterpillars)',
        'warning': 'ሙቀቱ ከ30°C በላይ ከሆነ ማታ ላይ ውኃ ይረጩ',
        'warning_en': 'If temp >30°C, spray water in evening'
    },
    'maize': {
        'name_am': 'በቆሎ',
        'icon': '🌽',
        'planting': 'ሚያዝያ-ግንቦት (ከከባድ ዝናብ በኋላ)',
        'planting_en': 'April-May (after heavy rains)',
        'fertilizer': '100kg N + 40kg P በሄክታር',
        'fertilizer_en': '100kg N + 40kg P per hectare',
        'harvest': '120-140 ቀናት (ሽሮች ሲደርቁ)',
        'harvest_en': '120-140 days (when husks dry)',
        'pests': 'የበቆሎ አጣሚ እና የግንድ ቆራጭ',
        'pests_en': 'Maize stalk borer and stem borer',
        'warning': 'ለ3 ሳምንታት ዝናብ ካልኖረ ውኃ ማስተካከል ያስፈልጋል',
        'warning_en': 'If no rain for 3 weeks, irrigation needed'
    },
    'coffee': {
        'name_am': 'ቡና',
        'icon': '☕',
        'planting': 'በዝናብ ወቅት መጀመሪያ ከጥላ ዛፎች ጋር',
        'planting_en': 'With shade trees at start of rainy season',
        'fertilizer': 'ኦርጋኒክ ፍግ + 20-20-20 NPK',
        'fertilizer_en': 'Organic manure + 20-20-20 NPK',
        'harvest': 'ጥቅምት-ታህሳስ (ቀይ ፍሬዎች ሲበቅሉ)',
        'harvest_en': 'October-December (red berries)',
        'pests': 'የቡና ቅጠል ዝገት እና የቤሪ ነጭት',
        'pests_en': 'Coffee Leaf Rust and Berry Borer',
        'warning': 'በከፍተኛ ድርቅ ጊዜ የጥላ ዛፎችን አያስወግዱ',
        'warning_en': 'Maintain shade trees during drought'
    },
    'wheat': {
        'name_am': 'ስንዴ',
        'icon': '🌾',
        'planting': 'ሰኔ-ሐምሌ (ለመጀመሪያው ዝናብ)',
        'planting_en': 'June-July (for main rains)',
        'fertilizer': '60kg N + 30kg P በሄክታር',
        'fertilizer_en': '60kg N + 30kg P per hectare',
        'harvest': '110-120 ቀናት (ጭንቅላቶች ሲወርዱ)',
        'harvest_en': '110-120 days (when heads turn golden)',
        'pests': 'የስንዴ ቅጠል ዝገት እና አፋት',
        'pests_en': 'Wheat leaf rust and aphids',
        'warning': 'በከፍተኛ እርጥበት ጊዜ የፈንገስ በሽታ ይጠንቀቁ',
        'warning_en': 'Watch for fungal diseases in high humidity'
    }
}

# Disease data
DISEASE_DATA = {
    'leaf_spot': {
        'name_am': 'ቅጠል ነጠብጣብ',
        'name_en': 'Leaf Spot',
        'symptoms': 'ቡናማ ነጠብጣቦች በቅጠሎች ላይ',
        'symptoms_en': 'Brown spots on leaves',
        'treatment': 'የመዳብ ፀረ-ፈንገስ ይረጩ, የታመሙ ቅጠሎችን ያስወግዱ',
        'treatment_en': 'Spray copper fungicide, remove infected leaves'
    },
    'armyworm': {
        'name_am': 'ሰራተኛ ትል',
        'name_en': 'Armyworm',
        'symptoms': 'ቅጠሎች በትሎች ተበላሽተው',
        'symptoms_en': 'Leaves eaten by caterpillars',
        'treatment': 'ተፈጥሯዊ ጠላቶችን ይጠቀሙ, በእጅ ያንሱ',
        'treatment_en': 'Use natural enemies, handpick caterpillars'
    },
    'rust': {
        'name_am': 'ዝገት',
        'name_en': 'Rust',
        'symptoms': 'ብርቱካን-ቡናማ ቀለም በቅጠሎች ላይ',
        'symptoms_en': 'Orange-brown color on leaves',
        'treatment': 'የሰልፈር ፀረ-ፈንገስ ይረጩ, የሚቋቋም ዘር ይጠቀሙ',
        'treatment_en': 'Spray sulfur fungicide, use resistant varieties'
    }
}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued"""
    
    welcome_text = """
🌾 *እንኳን ደህና መጡ ወደ ኢትዮ-አግሪ አማካሪ!*
*Welcome to Ethio-Agri Advisor!*

🇪🇹 ለኢትዮጵያ ገበሬዎች ቀላል የግብርና ምክር
*Simple farming advice for Ethiopian farmers*

📱 ምን ማድረግ ይችላሉ / *What you can do:*
• 🌾 የሰብል ምክር ያግኙ (Get crop advice)
• 🐛 የበሽታ መለየት (Disease detection)
• 📊 የምርት አስሊያ (Yield calculator)
• 👥 የገበሬዎች መድረክ (Community forum)

📝 ለመጀመር ከታች ያሉትን ቁልፎች ይጫኑ
*Press the buttons below to start*

🌱 አብረን እናድጋለን! / *Together we grow!*
"""
    
    keyboard = [
        [InlineKeyboardButton("🌾 የሰብል ምክር / Crop Advice", callback_data='crop_advice')],
        [InlineKeyboardButton("🐛 በሽታ መለየት / Disease Detection", callback_data='disease')],
        [InlineKeyboardButton("📊 ምርት አስላ / Yield Calc", callback_data='yield_calc')],
        [InlineKeyboardButton("👥 የገበሬዎች መድረክ / Community", callback_data='community')],
        [InlineKeyboardButton("❓ እርዳታ / Help", callback_data='help')],
        [InlineKeyboardButton("📢 ዜና / News", callback_data='news')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Crop advice handler
async def crop_advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show crop selection menu"""
    
    query = update.callback_query
    await query.answer()
    
    text = """
🌾 *የሰብል ምክር - Crop Advice*

የሚፈልጉትን ሰብል ይምረጡ:
*Choose your crop:*
"""
    
    keyboard = [
        [InlineKeyboardButton("🌾 ጤፍ (Teff)", callback_data='crop_teff')],
        [InlineKeyboardButton("🌽 በቆሎ (Maize)", callback_data='crop_maize')],
        [InlineKeyboardButton("☕ ቡና (Coffee)", callback_data='crop_coffee')],
        [InlineKeyboardButton("🌾 ስንዴ (Wheat)", callback_data='crop_wheat')],
        [InlineKeyboardButton("🔙 ወደ መጀመሪያ / Back", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Show specific crop advice
async def show_crop_advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display detailed advice for selected crop"""
    
    query = update.callback_query
    await query.answer()
    
    crop_key = query.data.split('_')[1]  # crop_teff -> teff
    crop = CROP_DATA.get(crop_key)
    
    if crop:
        text = f"""
{ crop['icon'] } *{crop['name_am']} ({crop_key.title()})*

📅 *መትከል / Planting:*
{crop['planting']}
_{crop['planting_en']}_

💪 *ማዳበሪያ / Fertilizer:*
{crop['fertilizer']}
_{crop['fertilizer_en']}_

🌾 *መሰብሰብ / Harvest:*
{crop['harvest']}
_{crop['harvest_en']}_

🐛 *ተባዮች / Pests:*
{crop['pests']}
_{crop['pests_en']}_

⚠️ *ማስጠንቀቂያ / Warning:*
{crop['warning']}
_{crop['warning_en']}_

💡 *ተጨማሪ ጥያቄ ካለ / Questions?*
📱 የአካባቢዎን ግብርና ባለሙያ ይጠይቁ
*Contact your local agricultural expert*
"""
        
        keyboard = [
            [InlineKeyboardButton("🔙 ወደ ሰብሎች / Back to Crops", callback_data='crop_advice')],
            [InlineKeyboardButton("🏠 መጀመሪያ / Home", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

# Disease detection
async def disease_detection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show disease detection options"""
    
    query = update.callback_query
    await query.answer()
    
    text = """
🐛 *በሽታ መለየት - Disease Detection*

ምልክቶቹን ይምረጡ / *Choose symptoms:*
"""
    
    keyboard = [
        [InlineKeyboardButton("🟤 ቡናማ ነጠብጣቦች / Brown Spots", callback_data='disease_leaf_spot')],
        [InlineKeyboardButton("🐛 ቅጠል የሚበሉ ትሎች / Caterpillars", callback_data='disease_armyworm')],
        [InlineKeyboardButton("🟠 ብርቱካን-ቡናማ ቀለም / Orange-Brown", callback_data='disease_rust')],
        [InlineKeyboardButton("📸 ፎቶ ላኩ / Send Photo", callback_data='disease_photo')],
        [InlineKeyboardButton("🔙 ወደ መጀመሪያ / Back", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Show disease advice
async def show_disease_advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display disease treatment advice"""
    
    query = update.callback_query
    await query.answer()
    
    disease_key = query.data.split('_')[1]  # disease_leaf_spot -> leaf_spot
    disease = DISEASE_DATA.get(disease_key)
    
    if disease:
        text = f"""
🩺 *{disease['name_am']} ({disease['name_en']})*

🔍 *ምልክቶች / Symptoms:*
{disease['symptoms']}
_{disease['symptoms_en']}_

💊 *ህክምና / Treatment:*
{disease['treatment']}
_{disease['treatment_en']}_

⚠️ *ማስጠንቀቂያ / Warning:*
በሽታው ከተስፋፋ የአካባቢ ባለሙያ ይደውሉ!
*If disease spreads, call local expert!*

📞 ነጻ የስልክ መስመር / *Free Helpline:* 0800-123-456
"""
        
        keyboard = [
            [InlineKeyboardButton("🔙 ወደ በሽታዎች / Back", callback_data='disease')],
            [InlineKeyboardButton("🏠 መጀመሪያ / Home", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

# Yield calculator
async def yield_calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show yield calculator"""
    
    query = update.callback_query
    await query.answer()
    
    text = """
📊 *የምርት አስሊያ - Yield Calculator*

የሰብል ዓይነት እና ስፋት ይጻፉ:
*Write crop type and area:*

ለምሳሌ / *Example:*
`ጤፍ 2` (ጤፍ በ2 ሄክታር)
*Teff on 2 hectares*

`በቆሎ 1.5` (በቆሎ በ1.5 ሄክታር)
*Maize on 1.5 hectares*

ወይም ከታች ያሉትን ይጫኑ:
*Or press below:*
"""
    
    keyboard = [
        [InlineKeyboardButton("🌾 ጤፍ 1 ሄክታር / Teff 1ha", callback_data='calc_teff_1')],
        [InlineKeyboardButton("🌽 በቆሎ 1 ሄክታር / Maize 1ha", callback_data='calc_maize_1')],
        [InlineKeyboardButton("☕ ቡና 1 ሄክታር / Coffee 1ha", callback_data='calc_coffee_1')],
        [InlineKeyboardButton("🔙 ወደ መጀመሪያ / Back", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Calculate yield
async def calculate_yield(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Calculate and display yield"""
    
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')  # calc_teff_1
    crop_key = data[1]
    area = float(data[2])
    
    # Average yields (kg/ha)
    yields = {
        'teff': 1800,
        'maize': 3000,
        'coffee': 800,
        'wheat': 2500
    }
    
    # Prices (ETB/kg)
    prices = {
        'teff': 60,
        'maize': 40,
        'coffee': 120,
        'wheat': 45
    }
    
    crop_name = CROP_DATA.get(crop_key, {}).get('name_am', crop_key.title())
    expected_yield = yields.get(crop_key, 2000) * area
    expected_income = expected_yield * prices.get(crop_key, 50)
    
    text = f"""
📊 *የምርት ውጤት - Yield Result*

🌾 *ሰብል / Crop:* {crop_name}
📏 *ስፋት / Area:* {area} ሄክታር / hectares

📈 *የሚጠበቀው ምርት / Expected Yield:*
{expected_yield:,.0f} ኪሎ ግራም / kg

💰 *የሚጠበቀው ገቢ / Expected Income:*
ብር {expected_income:,.0f} ETB

💡 *ምክር / Advice:*
• ጥሩ ዘር ይጠቀሙ / Use quality seeds
• በትክክል ያስተዳድሩ / Manage properly
• ተባዮችን ይከታተሉ / Monitor for pests

📱 የአካባቢ ባለሙያን ያማክሩ
*Consult local agricultural expert*
"""
    
    keyboard = [
        [InlineKeyboardButton("🔄 እንደገና አስላ / Recalculate", callback_data='yield_calc')],
        [InlineKeyboardButton("🏠 መጀመሪያ / Home", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Community forum
async def community(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show community forum"""
    
    query = update.callback_query
    await query.answer()
    
    text = """
👥 *የገበሬዎች መድረክ - Farmer Community*

💡 *የሌሎች ምክሮች / Other Farmers' Tips:*

1️⃣ አቶ በቀለ (Oromia)
"ጤፍ ከመትከል በፊት ዘሩን በውኃ ውስጥ ማጥለቅ ምርት ይጨምራል!"
*"Soak teff seeds before planting for better yield!"*

2️⃣ ወ/ሮ አስናቀ (Amhara)
"በቆሎ ሲተክሉ በመስመር መካከል ባቄላ ብትተኩ አፈር ያሻሻላል"
*"Plant beans between maize rows to improve soil"*

3️⃣ አቶ ገረም (Tigray)
"የቡና ተክል ላይ የባናና ቅርፊት ብትቀብሩ ተባይ ይቀንሳል"
*"Use banana peels around coffee to reduce pests"*

✍️ *የእርስዎን ምክር ያጋሩ / Share Your Tip:*
በመልእክት ይላኩ / *Send as message:* `💡 [የእርስዎ ምክር / Your tip]`
"""
    
    keyboard = [
        [InlineKeyboardButton("📤 ምክር አጋሩ / Share Tip", callback_data='share_tip')],
        [InlineKeyboardButton("📢 የቅርብ ጊዜ ምክሮች / Recent Tips", callback_data='recent_tips')],
        [InlineKeyboardButton("🔙 ወደ መጀመሪያ / Back", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    
    query = update.callback_query
    await query.answer()
    
    text = """
❓ *እርዳታ - Help*

📱 *እንዴት መጠቀም ይቻላል? / How to use:*

1️⃣ 🌾 *የሰብል ምክር / Crop Advice*
   • ሰብል ይምረጡ / Select crop
   • ዝርዝር ምክር ያግኙ / Get detailed advice

2️⃣ 🐛 *በሽታ መለየት / Disease Detection*
   • ምልክቶችን ይምረጡ / Select symptoms
   • ህክምና ያግኙ / Get treatment advice

3️⃣ 📊 *ምርት አስላ / Yield Calculator*
   • ሰብል እና ስፋት ይጻፉ / Write crop & area
   • የሚጠበቀውን ምርት ይመልከቱ / See expected yield

4️⃣ 👥 *ኮሚዩኒቲ / Community*
   • ከሌሎች ገበሬዎች ይማሩ / Learn from others
   • የእርስዎን ምክር ያጋሩ / Share your tips

📞 *ነጻ የስልክ መስመር / Free Helpline:*
0800-123-456

🌐 *ድረ-ገጽ / Website:*
[Coming soon]

📧 *ኢሜል / Email:*
ethio.agri.advisor@gmail.com

🏠 *መጀመሪያ ለመመለስ / To go home:*
የ'Home' ቁልፍ ይጫኑ / Press 'Home' button
"""
    
    keyboard = [
        [InlineKeyboardButton("🏠 መጀመሪያ / Home", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# News command
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show agricultural news"""
    
    query = update.callback_query
    await query.answer()
    
    text = """
📢 *የግብርና ዜና - Agricultural News*

🌾 *የቅርብ ጊዜ መረጃዎች / Latest Updates:*

1️⃣ 🌧️ *የዝናብ ትንበያ / Weather Forecast*
   • የበልግ ዝናብ በመጋቢት ወር ይጀምራል
   • Belg rains expected to start in February

2️⃣ 💰 *የገበያ ዋጋዎች / Market Prices*
   • ጤፍ: 60 ብር/ኪሎ / Teff: 60 ETB/kg
   • በቆሎ: 40 ብር/ኪሎ / Maize: 40 ETB/kg
   • ቡና: 120 ብር/ኪሎ / Coffee: 120 ETB/kg

3️⃣ 🏆 *የሚበቃ ዘር አይነቶች / Improved Seeds*
   • ለከፍታ አካባቢ: 'Diga' ጤፍ
   • ለዝቅተኛ አካባቢ: 'Melkassa' በቆሎ

4️⃣ 🎓 *የስልጠና ፕሮግራሞች / Training Programs*
   • በአካባቢዎ ባለሙያዎች ነጻ ስልጠና
   • Free training by local experts

📱 *ተጨማሪ መረጃ ለማግኘት:*
የአካባቢ ግብርና ጽህፈት ቤትን ይጎብኙ
*Visit your local agricultural office*
"""
    
    keyboard = [
        [InlineKeyboardButton("🔄 አዲስ ዜና / Refresh", callback_data='news')],
        [InlineKeyboardButton("🏠 መጀመሪያ / Home", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Handle text messages (for custom queries)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user text messages"""
    
    text = update.message.text.lower()
    user = update.message.from_user
    
    # Check for yield calculation
    if 'ሄክታር' in text or 'hectare' in text.lower():
        # Simple parsing (e.g., "teff 2" or "ጤፍ 2")
        parts = text.split()
        if len(parts) >= 2:
            try:
                crop_key = parts[0]
                area = float(parts[1])
                
                # Map Amharic to English
                crop_map = {
                    'ጤፍ': 'teff',
                    'በቆሎ': 'maize',
                    'ቡና': 'coffee',
                    'ስንዴ': 'wheat'
                }
                crop_key = crop_map.get(crop_key, crop_key)
                
                if crop_key in CROP_DATA:
                    yields = {'teff': 1800, 'maize': 3000, 'coffee': 800, 'wheat': 2500}
                    prices = {'teff': 60, 'maize': 40, 'coffee': 120, 'wheat': 45}
                    
                    expected_yield = yields.get(crop_key, 2000) * area
                    expected_income = expected_yield * prices.get(crop_key, 50)
                    crop_name = CROP_DATA.get(crop_key, {}).get('name_am', crop_key.title())
                    
                    response = f"""
📊 *የምርት ውጤት / Yield Result*

🌾 ሰብል / Crop: {crop_name}
📏 ስፋት / Area: {area} ሄክታር

📈 የሚጠበቀው ምርት: {expected_yield:,.0f} ኪሎ
💰 የሚጠበቀው ገቢ: ብር {expected_income:,.0f}

🌱 መልካም ምርት! / Good farming!
"""
                    await update.message.reply_text(response, parse_mode='Markdown')
                    return
            except:
                pass
    
    # Check for disease symptoms
    if any(word in text for word in ['ቡናማ', 'ነጠብጣብ', 'brown', 'spot', 'ትል', 'caterpillar', 'ዝገት', 'rust']):
        await update.message.reply_text(
            "🔍 *በሽታ መረጃ / Disease Info*\n\n"
            "በሽታዎን ለመለየት የ'Disease Detection' ቁልፍ ይጫኑ\n"
            "*Press 'Disease Detection' to identify*",
            parse_mode='Markdown'
        )
        return
    
    # Check for crop help
    crop_map = {
        'teff': 'teff',
        'ጤፍ': 'teff',
        'maize': 'maize',
        'በቆሎ': 'maize',
        'coffee': 'coffee',
        'ቡና': 'coffee',
        'wheat': 'wheat',
        'ስንዴ': 'wheat'
    }
    
    for key, value in crop_map.items():
        if key in text:
            crop = CROP_DATA.get(value)
            if crop:
                response = f"""
{crop['icon']} *{crop['name_am']}*

📅 መትከል: {crop['planting']}
💪 ማዳበሪያ: {crop['fertilizer']}
🌾 መሰብሰብ: {crop['harvest']}
🐛 ተባዮች: {crop['pests']}
⚠️ ማስጠንቀቂያ: {crop['warning']}

📱 ተጨማሪ መረጃ: የ'Crop Advice' ቁልፍ ይጫኑ
"""
                await update.message.reply_text(response, parse_mode='Markdown')
                return
    
    # Default response
    await update.message.reply_text(
        "🌾 *ኢትዮ-አግሪ አማካሪ*\n\n"
        "እንኳን ደህና መጡ! / *Welcome!*\n\n"
        "📝 ለመጀመር / *To start:*\n"
        "• /start - ዋና ምናሌ / Main menu\n"
        "• /help - እርዳታ / Help\n\n"
        "💡 ሰብል ይጻፉ / *Type crop name*\n"
        "(ጤፍ, በቆሎ, ቡና, ስንዴ)",
        parse_mode='Markdown'
    )

# Back to main menu
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu"""
    
    query = update.callback_query
    await query.answer()
    await start(update, context)

# Main function
def main():
    """Start the bot"""
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(crop_advice, pattern='^crop_advice$'))
    application.add_handler(CallbackQueryHandler(show_crop_advice, pattern='^crop_'))
    application.add_handler(CallbackQueryHandler(disease_detection, pattern='^disease$'))
    application.add_handler(CallbackQueryHandler(show_disease_advice, pattern='^disease_'))
    application.add_handler(CallbackQueryHandler(yield_calculator, pattern='^yield_calc$'))
    application.add_handler(CallbackQueryHandler(calculate_yield, pattern='^calc_'))
    application.add_handler(CallbackQueryHandler(community, pattern='^community$'))
    application.add_handler(CallbackQueryHandler(help_command, pattern='^help$'))
    application.add_handler(CallbackQueryHandler(news, pattern='^news$'))
    application.add_handler(CallbackQueryHandler(back, pattern='^back$'))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    print("🤖 Ethio-Agri Advisor Bot is running!")
    print("📱 Send /start to get started")
    print("Press Ctrl+C to stop")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
