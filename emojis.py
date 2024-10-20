emoji_dict = {
    "Knight": ("lc_knight", 1297665621672198214),
    "Guardian": ("lc_guardian", 1297665632145506455),
}

def get_emoji(name):
    global emoji_dict
    if not name in emoji_dict:
        return ""
    info = emoji_dict[name]
    return f"<:{info[0]}:{info[1]}>"