import os
import io
import asyncio
import logging
from pypdf import PdfReader
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📄 **Welcome to DocuRead!** 📄\n\n"
        "I can scan and extract text from your PDF documents instantly with complete privacy.\n\n"
        "👉 **To begin, simply send or upload any `.pdf` file to this chat as a Document.**"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# Handle Document Uploads
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    
    # Verify file extension safety
    if not doc.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ Unsupported file format. Please upload a valid document ending in **.pdf**.")
        return

    status_msg = await update.message.reply_text("⏳ *Downloading document into secure memory buffer...*", parse_mode="Markdown")
    
    try:
        # Download file completely to memory pipeline
        bot = context.bot
        tg_file = await bot.get_file(doc.file_id)
        
        pdf_buffer = io.BytesIO()
        await tg_file.download_to_memory(pdf_buffer)
        pdf_buffer.seek(0)
        
        await status_msg.edit_text("⚙️ *Analyzing layout structure and extracting text modules...*", parse_mode="Markdown")
        
        # Parse PDF using pure Python pypdf package
        reader = PdfReader(pdf_buffer)
        extracted_text = ""
        
        # Iterate over pages and compile string values
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                extracted_text += f"--- [ Page {i+1} ] ---\n{text}\n\n"
        
        extracted_text = extracted_text.strip()
        
        if not extracted_text:
            await status_msg.edit_text("⚠️ *Extraction complete, but no readable text layer was found.*\n\nThis usually means the PDF is made of flattened images/scans rather than raw text vectors.")
            return

        # Handle output based on size limits (Telegram chat block maximum is 4096 characters)
        if len(extracted_text) <= 3500:
            await status_msg.delete()
            await update.message.reply_text(
                f"✅ **Text Extracted Successfully:**\n\n```\n{extracted_text}\n```", 
                parse_mode="Markdown"
            )
        else:
            await status_msg.edit_text("📦 *Text layout is quite large! Compiling into a clean data file attachment...*")
            
            # Convert string to output memory text file
            txt_buffer = io.BytesIO(extracted_text.encode('utf-8'))
            txt_buffer.seek(0)
            txt_buffer.name = f"extracted_{doc.file_name.replace('.pdf', '')}.txt"
            
            await update.message.reply_document(
                document=txt_buffer, 
                caption=f"✅ **Success!** Extracted text from `{doc.file_name}` is ready."
            )
            await status_msg.delete()

    except Exception as e:
        logger.error(f"Error compiling PDF: {e}")
        await status_msg.edit_text("❌ An internal structural error occurred while parsing this document matrix.")

def main():
    # Explicit loop initialization logic ensuring full Python 3.14.3 Render compatibility layers pass
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if not TOKEN:
        logger.error("No BOT_TOKEN found in environment config scopes!")
        return

    application = Application.builder().token(TOKEN).build()

    # Handlers Registration Mapping
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("🤖 DocuRead pipeline pipelines active and processing...")
    application.run_polling()

if __name__ == "__main__":
    main()
