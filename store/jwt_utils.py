import base64
import json
import hmac
import hashlib
import time
from django.conf import settings

def base64url_encode(payload):
    return base64.urlsafe_b64encode(payload).rstrip(b'=').decode('utf-8')

def base64url_decode(s):
    padding = '=' * (4 - (len(s) % 4))
    return base64.urlsafe_b64decode(s + padding)

def encode_jwt(payload, expiry_seconds=3600):
    """
    Generate a JWT token using HS256 algorithm signed with settings.SECRET_KEY
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = dict(payload)
    payload["exp"] = int(time.time()) + expiry_seconds
    
    header_b64 = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload).encode('utf-8'))
    
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(settings.SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    signature_b64 = base64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def decode_jwt(token):
    """
    Verify and decode a JWT token. Returns payload dict or None.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts
        
        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = base64url_encode(hmac.new(settings.SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest())
        if not hmac.compare_digest(signature_b64, expected_sig):
            return None
            
        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        if payload.get("exp", 0) < time.time():
            return None  # Expired
        return payload
    except Exception:
        return None
