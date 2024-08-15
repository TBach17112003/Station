import urllib3
# from urllib3.util.ssl_ import create_urllib3_context
import ssl


try:
    # Create a custom SSL context
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    # ssl_context.set_ciphers("AES256-SHA")
    ssl_context.load_verify_locations(cafile='./ca.crt')
    http = urllib3.PoolManager(
        ssl_context = ssl_context
    )
    
    response = http.request('GET', 'https://begvn.home:9090/data/accelerator/date?date=2024-08-12')
    print(response.data)
except Exception as e:
    print('Error: ',e)



