from datetime import datetime

def derive_month(date_str):
    if not date_str:
        return ""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%b-%y")