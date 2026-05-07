import os
from dotenv import load_dotenv
load_dotenv()


class _Settings:
    # API keys
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # User trading profile — used in prompts for position sizing
    broker:           str   = os.getenv("BROKER",           "Apex Trader Funding")
    account_size:     float = float(os.getenv("ACCOUNT_SIZE",    "50000"))
    risk_per_trade:   float = float(os.getenv("RISK_PER_TRADE",  "0.01"))   # 1%
    max_daily_loss:   float = float(os.getenv("MAX_DAILY_LOSS",  "0.03"))   # 3%
    preferred_style:  str   = os.getenv("PREFERRED_STYLE",  "both")         # swing | day | both

    @property
    def risk_dollars(self) -> float:
        return round(self.account_size * self.risk_per_trade, 2)

    @property
    def max_loss_dollars(self) -> float:
        return round(self.account_size * self.max_daily_loss, 2)


settings = _Settings()
