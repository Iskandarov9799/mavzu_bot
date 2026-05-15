import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN:       str  = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    DATABASE_URL:    str  = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    MINI_APP_URL:    str  = field(default_factory=lambda: os.getenv("MINI_APP_URL", ""))
    ADMIN_IDS:       list = field(default_factory=lambda: [
        int(x)
        for x in os.getenv("ADMIN_IDS", "")
                   .strip().strip("[]").replace(" ", "").split(",")
        if x.strip().lstrip("-").isdigit()
    ])
    PAYMENT_CARD:    str  = field(default_factory=lambda: os.getenv("PAYMENT_CARD",  "8600 0000 0000 0000"))
    PAYMENT_OWNER:   str  = field(default_factory=lambda: os.getenv("PAYMENT_OWNER", "Karta egasi"))
    SOLUTION_URL:    str  = field(default_factory=lambda: os.getenv("SOLUTION_URL", ""))
    RESULT_GROUP_ID: str  = field(default_factory=lambda: os.getenv("RESULT_GROUP_ID", ""))
    IMAGES_DIR:      str  = field(default_factory=lambda: os.getenv("IMAGES_DIR", "/var/www/bot_images"))
    IMAGES_URL:      str  = field(default_factory=lambda: os.getenv("IMAGES_URL", "http://localhost/images"))

    PRICE_DAILY:    int = 10_000
    PRICE_MONTHLY:  int = 50_000
    MAX_QUESTIONS:  int = 50
    BOLIMLAR_COUNT: int = 40

    SUBJECTS = {
        'onatili':  '📚 Ona tili',
        'adabiyot': '📖 Adabiyot',
    }

    def validate(self):
        errors = []
        if not self.BOT_TOKEN:    errors.append("❌ BOT_TOKEN yo'q!")
        if not self.DATABASE_URL: errors.append("❌ DATABASE_URL yo'q!")
        if not self.ADMIN_IDS:    errors.append("❌ ADMIN_IDS yo'q!")
        if not self.MINI_APP_URL: errors.append("⚠️  MINI_APP_URL yo'q!")
        for e in errors: print(e)
        if any("❌" in e for e in errors):
            raise SystemExit("Bot ishga tushmadi!")

config = Config()