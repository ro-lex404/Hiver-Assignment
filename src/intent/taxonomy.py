from typing import Dict, List, Any

INTENT_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "ORDER_STATUS_DELIVERY": {
        "description": "Late delivery, tracking status inquiries, carrier delays, missing package.",
        "keywords": ["tracking", "track", "delivery", "delivered", "package", "where is", "delayed", "late", "carrier", "tba", "shipping", "shipped", "transit", "porch", "driver", "courier"],
        "policy": "Direct to amazon.com/your-orders, explain 24h grace period, or request DM if >48h lost."
    },
    "REFUND_AND_RETURNS": {
        "description": "Return labels, return window, refund delays, gift card refunds, Kohl's/Whole Foods drop-off.",
        "keywords": ["refund", "return", "returned", "returning", "kohl", "whole foods", "ups drop", "money back", "reimburse", "restocking", "label", "qr code"],
        "policy": "Direct to amazon.com/returns, mention 3-5 business day timeline, escalate if amount disputed."
    },
    "DAMAGED_DEFECTIVE_ITEM": {
        "description": "Item broken, crushed, defective hardware, expired goods, wrong size/item sent.",
        "keywords": ["damaged", "broken", "cracked", "defective", "shattered", "leaking", "expired", "scratched", "wrong item", "wrong size", "stopped working", "faulty", "ruined"],
        "policy": "Offer instant replacement via amazon.com/returns without return requirement for broken glass/hazardous."
    },
    "ACCOUNT_ACCESS_SECURITY": {
        "description": "Account lockouts, 2FA OTP issues, unrecognized logins, phishing scams, data deletion.",
        "keywords": ["hacked", "unauthorized", "locked out", "2fa", "otp", "password", "phishing", "scam", "spoof", "suspend", "banned", "gdpr", "compromised"],
        "policy": "Never ask for credentials in public. Escalate immediately to Account Security Team."
    },
    "BILLING_AND_PRIME": {
        "description": "Prime subscription renewal, duplicate charges, payment errors, tax invoices, unexpected fees.",
        "keywords": ["prime", "charged", "billing", "bill", "subscription", "renewal", "duplicate charge", "invoice", "payment failed", "tax exempt", "membership", "fee"],
        "policy": "Direct to amazon.com/gp/primecentral for cancellations or DM for billing audit."
    },
    "PRODUCT_TROUBLESHOOTING": {
        "description": "Technical support for Kindle, Fire TV, Echo/Alexa, smart plugs, Prime Video streaming.",
        "keywords": ["kindle", "fire tv", "alexa", "echo", "remote", "wifi", "bluetooth", "boot loop", "frozen", "stream", "4k", "sd", "troubleshoot", "reset"],
        "policy": "Provide 40-second power cycle / restart instructions and link to amazon.com/devicesupport."
    },
    "FEEDBACK_AND_GENERAL": {
        "description": "Driver compliments, general app feedback, policy inquiries, appreciation.",
        "keywords": ["compliment", "feedback", "shoutout", "praise", "app update", "smile", "kudos", "thank you", "thanks", "terrible", "worst", "suggestion"],
        "policy": "Thank user, forward feedback to station/development team."
    }
}

ALL_INTENTS = list(INTENT_TAXONOMY.keys())
DEFAULT_INTENT = "FEEDBACK_AND_GENERAL"
