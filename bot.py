from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import yt_dlp
import os
from flask import Flask, request

TELEGRAM_TOKEN = "8161571681:AAEpj7x4jiNA3ATMg3ajQMEmkcMp4rPYJHc"

# Flask app oluştur
app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merhaba! Müzik indirmek için bana bir YouTube linki gönder."
    )

async def download_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.message.chat_id
    
    # URL kontrolü
    if not ('youtube.com' in url or 'youtu.be' in url):
        await update.message.reply_text("Lütfen geçerli bir YouTube linki gönderin!")
        return
    
    await update.message.reply_text("İndirme başlıyor...")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'outtmpl': f'downloads/%(title)s.%(ext)s',
        'cookiesfrombrowser': ('chrome',),
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'force_generic_extractor': False,
        'ignoreerrors': True,
        'nocheckcertificate': True,
    }
    
    try:
        # İndirme klasörünü oluştur
        os.makedirs('downloads', exist_ok=True)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info['title']
            file_path = f"downloads/{title}.mp3"
            
            await update.message.reply_text("Dosya yükleniyor...")
            
            # Dosyayı Telegram'a gönder
            with open(file_path, 'rb') as audio_file:
                await context.bot.send_audio(
                    chat_id=chat_id,
                    audio=audio_file,
                    title=title,
                    performer="YouTube Music Bot"
                )
            
            # Geçici dosyayı sil
            os.remove(file_path)
            
    except Exception as e:
        await update.message.reply_text(f"Hata oluştu: {str(e)}")
        # Hata durumunda geçici dosyaları temizle
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Update None değilse ve message varsa
    if update and update.message:
        await update.message.reply_text("Bir hata oluştu. Lütfen geçerli bir YouTube linki gönderdiğinizden emin olun.")
    # Eğer effective_chat varsa
    elif update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Bir hata oluştu. Lütfen geçerli bir YouTube linki gönderdiğinizden emin olun."
        )
    print(f"Update {update} caused error {context.error}")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_music))
    application.add_error_handler(error_handler)
    
    # Normal polling başlat
    application.run_polling()

# Render için web endpoint'i
@app.route('/')
def home():
    return 'Bot çalışıyor!'

if __name__ == '__main__':
    # Eğer RENDER_EXTERNAL_URL varsa (Render ortamı)
    if os.environ.get('RENDER_EXTERNAL_URL'):
        port = int(os.environ.get('PORT', 8080))
        app.run(host='0.0.0.0', port=port)
    else:
        # Lokal geliştirme ortamı
        main() 