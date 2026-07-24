import os
import logging
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

# Google Books API
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY", "")

# ============= HELPER FUNCTIONS =============

def search_books(query, max_results=5):
    """Search for books using Google Books API."""
    try:
        params = {
            "q": query,
            "maxResults": max_results,
            "printType": "books",
            "orderBy": "relevance"
        }
        
        if GOOGLE_BOOKS_API_KEY:
            params["key"] = GOOGLE_BOOKS_API_KEY
        
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            return []
        
        books = []
        for item in items:
            volume_info = item.get("volumeInfo", {})
            
            if not volume_info.get("title"):
                continue
                
            book = {
                "title": volume_info.get("title", ""),
                "authors": volume_info.get("authors", ["Unknown Author"]),
                "description": volume_info.get("description", "No description available."),
                "averageRating": volume_info.get("averageRating"),
                "ratingsCount": volume_info.get("ratingsCount", 0),
                "pageCount": volume_info.get("pageCount"),
                "categories": volume_info.get("categories", []),
                "publishedDate": volume_info.get("publishedDate", ""),
                "publisher": volume_info.get("publisher", ""),
                "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail", ""),
                "infoLink": volume_info.get("infoLink", ""),
                "previewLink": volume_info.get("previewLink", ""),
            }
            books.append(book)
            
        return books
        
    except Exception as e:
        logger.error(f"Error searching books: {e}")
        return []

def format_book_message(book):
    """Format a book dictionary into a readable message."""
    title = book.get("title", "Unknown Title")
    authors = ", ".join(book.get("authors", ["Unknown Author"]))
    description = book.get("description", "No description available.")
    
    # Truncate description if too long
    if len(description) > 500:
        description = description[:497] + "..."
    
    rating = book.get("averageRating")
    rating_text = f"⭐ {rating}/5" if rating else "⭐ No rating available"
    
    pages = book.get("pageCount")
    pages_text = f"📄 {pages} pages" if pages else "📄 Page count not available"
    
    published = book.get("publishedDate", "")
    published_text = f"📅 {published}" if published else "📅 Publication date not available"
    
    categories = book.get("categories", [])
    categories_text = f"📚 {', '.join(categories)}" if categories else "📚 No genre information"
    
    message = f"""📖 *{title}*

✍️ *Author:* {authors}
{rating_text}
{pages_text}
{published_text}
{categories_text}

📝 *Description:*
{description}
"""
    
    return message

# ============= COMMAND HANDLERS =============

WELCOME_TEXT = """
📚 *Welcome to BookWise Bot!*

I can help you find your next great read. Here's what I can do:

🔍 *Search* - Just type any book title, author, or genre
📖 *Recommend* - Get personalized recommendations
ℹ️ *About* - Learn more about this bot

Try typing a book name or use /recommend to get started!
"""

HELP_TEXT = """
📖 *How to use BookWise Bot*

• *Search*: Type any book title, author, or genre
  Example: "Harry Potter" or "Stephen King"

• *Recommendations*: Use /recommend + genre
  Example: /recommend sci-fi

• *Commands*:
  /start - Start the bot
  /help - Show this help message
  /recommend [genre] - Get book recommendations
  /search [query] - Search for books
  /about - About this bot

Happy reading! 📚
"""

ABOUT_TEXT = """
📚 *About BookWise Bot*

This bot helps you discover new books to read using the Google Books API.

📌 *Features:*
• Search by title, author, or genre
• Get book descriptions and ratings
• View cover images
• Get recommendations by genre

👨‍💻 *Created with:*
• Python & python-telegram-bot
• Google Books API
• Deployed on Railway
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message when /help is issued."""
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send an about message when /about is issued."""
    await update.message.reply_text(
        ABOUT_TEXT,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recommend books based on genre or query."""
    query = " ".join(context.args) if context.args else None
    
    if not query:
        await update.message.reply_text(
            "📖 *Please specify a genre or topic!*\n\n"
            "Example: `/recommend sci-fi`\n"
            "Example: `/recommend mystery thriller`\n\n"
            "Or just type a genre like 'fantasy' and I'll find recommendations!",
            parse_mode="Markdown"
        )
        return
    
    await update.message.reply_text(f"🔍 Searching for *{query}* recommendations...", parse_mode="Markdown")
    
    try:
        # Search with subject filter for better genre results
        search_query = f"subject:{query}"
        books = search_books(search_query, max_results=5)
        
        # If no results, try a general search
        if not books:
            books = search_books(query, max_results=5)
        
        if not books:
            await update.message.reply_text(
                f"😕 No books found for *{query}*.\n"
                "Try a different genre or use /search to find specific titles.",
                parse_mode="Markdown"
            )
            return
        
        for book in books:
            message = format_book_message(book)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 View on Google Books", url=book.get("infoLink", "#"))]
            ])
            
            await update.message.reply_text(
                message,
                parse_mode="Markdown",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
    except Exception as e:
        logger.error(f"Error in recommend: {e}")
        await update.message.reply_text(
            "❌ *Oops!* Something went wrong.\n"
            "Please try again later.",
            parse_mode="Markdown"
        )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages as search queries."""
    # Check if it's a command
    if update.message.text and update.message.text.startswith('/'):
        return
    
    query = update.message.text.strip() if update.message.text else ""
    
    if not query:
        return
    
    await update.message.reply_text(f"🔍 Searching for *{query}*...", parse_mode="Markdown")
    
    try:
        books = search_books(query, max_results=5)
        
        if not books:
            await update.message.reply_text(
                f"😕 No books found for *{query}*.\n"
                "Try a different search term or use /recommend to get suggestions.",
                parse_mode="Markdown"
            )
            return
        
        for book in books:
            message = format_book_message(book)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 View on Google Books", url=book.get("infoLink", "#"))]
            ])
            
            await update.message.reply_text(
                message,
                parse_mode="Markdown",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
    except Exception as e:
        logger.error(f"Error in search: {e}")
        await update.message.reply_text(
            "❌ *Oops!* Something went wrong.\n"
            "Please try again later.",
            parse_mode="Markdown"
        )

# ============= MAIN FUNCTION =============

def main():
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("recommend", recommend))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("search", search))

    # Handle all other text messages (treat as search query)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))

    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
