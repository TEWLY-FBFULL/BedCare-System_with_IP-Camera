import urllib.parse

def generate_rtsp_url(brand_pattern, ip, username=None, password=None, channel=1, port=554):
    if not brand_pattern:
        return None
    
    # EZVIZ default username is admin
    safe_user = urllib.parse.quote(username) if username else "admin"
    safe_pass = urllib.parse.quote(password) if password else ""
    
    url = brand_pattern
    url = url.replace("{ip}", str(ip))
    url = url.replace("{port}", str(port))
    url = url.replace("{username}", safe_user)
    url = url.replace("{password}", safe_pass) 
    url = url.replace("{channel}", str(channel))
    return url