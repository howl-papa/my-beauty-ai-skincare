# test_api_key_decode.py
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()

def decode_api_key():
    encoded_key = os.getenv('KFDA_API_KEY')
    print(f"현재 인코딩된 키: {encoded_key}")
    
    # 1차 디코딩
    decoded_once = urllib.parse.unquote(encoded_key)
    print(f"1차 디코딩: {decoded_once}")
    
    # 2차 디코딩 (필요시)
    decoded_twice = urllib.parse.unquote(decoded_once)
    print(f"2차 디코딩: {decoded_twice}")
    
    return decoded_twice

if __name__ == "__main__":
    original_key = decode_api_key()
    print(f"\n사용할 API 키: {original_key}")