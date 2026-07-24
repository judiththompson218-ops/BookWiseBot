import os
import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.books import search_books, get_book_recommendations

logger = logging.getLogger(__name__)

# Welcome message
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

📧 *Feedback:* Contact @yourusername
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when /start is issued."""
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when /help is issued."""
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an about message when /about is issued."""
    await update.message.reply_text(
        ABOUT_TEXT,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recommend books based on genre or query."""
    # Get the query from the command arguments
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
        books = get_book_recommendations(query, max_results=5)
        
        if not books:
            await update.message.reply_text(
                f"😕 No books found for *{query}*.\n"
                "Try a different genre or use /search to find specific titles.",
                parse_mode="Markdown"
            )
            return
        
        # Send each book as a formatted message
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

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages as search queries."""
    query = update.message.text.strip()
    
    if not query:
        return
    
    # Ignore if it's a command (already handled elsewhere)
    if query.startswith('/'):
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
        
        # Send each book as a formatted message
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

def format_book_message(book: dict) -> str:
    """Format a book dictionary into a readable message."""
    title = book.get("title", "Unknown Title")
    authors = ", ".join(book.get("authors", ["Unknown Author"]))
    description = book.get("description", "No description available.")
    
    # Truncate description if too long
    if len(description) > 500:
        description = description[:497] + "..."
    
    # Format rating
    rating = book.get("averageRating")
    rating_text = f"⭐ {rating}/5" if rating else "⭐ No rating available"
    
    # Format page count
    pages = book.get("pageCount")
    pages_text = f"📄 {pages} pages" if pages else "📄 Page count not available"
    
    # Format published date
    published = book.get("publishedDate", "")
    published_text = f"📅 {published}" if published else "📅 Publication date not available"
    
    # Format categories/genres
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
