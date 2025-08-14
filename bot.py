import os
import re
from urllib.parse import unquote
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Render env variable

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📂 Send me a .sh file, I will extract video & PDF links into a .txt file.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.endswith(".sh"):
        await update.message.reply_text("⚠ Please send a .sh file only.")
        return

    # Temporary file paths
    input_path = f"/tmp/{document.file_name}"
    output_path = input_path.replace(".sh", ".txt")

    # Download file
    file = await document.get_file()
    await file.download_to_drive(input_path)

    # Read and extract
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    titles, links = [], []

    # 🎥 Video titles
    raw_titles = re.findall(r'Starting download: "(.*?)"', content)
    clean_titles = [re.sub(r'\.(mp4|m3u8|pdf|mpd)$', '', t.strip(), flags=re.IGNORECASE) for t in raw_titles]
    titles.extend(clean_titles)

    # 🔗 Video links
    stream_links = re.findall(r'"(https?://(?:stream\.pwjarvis\.app|(?:www\.)?youtube\.com|youtu\.be)[^"]+)"', content)
    links.extend(stream_links)

    # ❌ YouTube error links
    error_links = re.findall(r'Video ID not found in URL: (https?://(?:www\.)?youtube\.com/embed/[^\s"]+)', content)
    for link in error_links:
        titles.append("YouTube Video")
        links.append(link)

    # 📄 PDF links
    pdf_links = re.findall(r"(https?://[^\s\"']+\.pdf)", content)
    for pdf in pdf_links:
        filename = unquote(pdf.split('/')[-1])
        clean_title = re.sub(r'\.pdf$', '', filename, flags=re.IGNORECASE)
        clean_title = clean_title.replace('_', ' ').replace('-', ' ').strip()
        titles.append(clean_title)
        links.append(pdf)

    # Save output
    with open(output_path, 'w', encoding='utf-8') as f:
        for title, link in zip(titles, links):
            f.write(f"{title} : {link}\n")

    # Send back
    await update.message.reply_document(open(output_path, 'rb'))

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()