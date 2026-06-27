import json

with open("features.json") as f:
    features = json.load(f)

total = len(features)
vals = list(features.values())

telegram  = sum(1 for v in vals if v.get("uses_telegram"))
email     = sum(1 for v in vals if v.get("uses_email"))
multipage = sum(1 for v in vals if v.get("is_multipage"))
password  = sum(1 for v in vals if v.get("has_password_field"))
card      = sum(1 for v in vals if v.get("steals_card"))
captcha   = sum(1 for v in vals if v.get("has_captcha"))

print(f"Total kits:      {total}")
print(f"Telegram exfil:  {telegram} ({telegram/total*100:.1f}%)")
print(f"Email exfil:     {email} ({email/total*100:.1f}%)")
print(f"Multi-page:      {multipage} ({multipage/total*100:.1f}%)")
print(f"Has password:    {password} ({password/total*100:.1f}%)")
print(f"Steals card:     {card} ({card/total*100:.1f}%)")
print(f"Has captcha:     {captcha} ({captcha/total*100:.1f}%)")