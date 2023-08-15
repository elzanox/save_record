import os
import shutil
import cv2
import paho.mqtt.client as mqtt
import json
from datetime import datetime, timedelta
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

## MQTT CONFIG
ip_broker =  "test.mosquitto.org"
port_mqtt = 1883
topic = "TT03"

USERNAME = 'admin'
PASSWORD = 'Test1234'
IP = '192.168.2.25'
PORT = '554'

IP2 = '192.168.2.21'
PORT = '554'

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"

URL = 'rtsp://{}:{}@{}:{}/Streaming/Channels/102'.format(USERNAME, PASSWORD, IP, PORT)
URL2 = 'rtsp://{}:{}@{}:{}/Streaming/Channels/102'.format(USERNAME, PASSWORD, IP2, PORT)

print('Connect to: ' + URL)

cap = cv2.VideoCapture(URL)
# cap.set(3,640)
# cap.set(4,480)
# capp = cv2.VideoCapture(URL2)
# cap = cv2.VideoCapture(0)
rec_fps = 30
rec_format = ".mp4"
rec_fourcc = "mp4v"
rec_frame_width = int(cap.get(3))
rec_frame_height = int(cap.get(4))

# frame_width = int(capp.get(3))
# frame_height = int(capp.get(4))


# output_filename = 'cobaaaaa.mp4'

# video_writer = cv2.VideoWriter(output_filename, cv2.VideoWriter_fourcc(*'mp4v'), FPS_vid, (frame_width, frame_height))
# status = ""
# Fungsi callback ketika menerima pesan MQTT
def on_message(client, userdata, msg):
    global video_writer, recording
    # topic = msg.topic
    payload = msg.payload.decode("utf-8")
    # print(f"Received message: {payload} on topic: {topic}")
    
     # Parsing data JSON dari payload
    try:
        data = json.loads(payload)
        # global code,header,round_code,status,message,cd,result_code,time_open_bet,time_closing_bet,time_bl_rling,time_reward
        
        code                = data["CODE"]
        header              = data["HEADER"]
        round_code          = data["ROUND_CODE"]
        status              = data["STATUS"]
        # result_value        = data["RESULT_VALUE"]
        message             = data["MESSAGE"]
        cd                  = data["CD"]
        result_code         = data["RESULT_CODE"]
        time_open_bet       = data["TIME_OPEN_BET"]
        time_closing_bet    = data["TIME_CLOSING_BET"]
        time_bl_rling       = data["TIME_BL_RLING"]
        time_reward         = data["TIME_REWARD"]
        
        # statusz = []
        # statusz.append(status)
        # print(statusz)
        
        if status == "PRP_BL" and not recording:
            # Mulai perekaman video jika status menjadi "CLOSING_BET" dan belum merekam
            recording = True    
            start_recording(round_code)
            print("Memulai Perekaman")
        elif status == "AVL" and recording:
            # Berhenti dan menyimpan video jika status berubah menjadi "PREPARING_BALL" dan sedang merekam
            stop_recording()
            recording = False
            print("Berhenti Merekam")
        
        print(f"ROUND_CODE: {round_code},STATUS: {status},MESSAGE: {message}")
        
        
        # Lakukan operasi sesuai dengan isi data JSON yang diterima
        # # Misalnya, simpan data ke file atau lakukan operasi lain sesuai kebutuhan Anda
        # with open("received_data.txt", "a") as file:
        #     file.write(f"{round_code}: {message}\n")
    except KeyError as error_format_json:
        print("Error Format JSON:", str(error_format_json))
    except json.JSONDecodeError as error_parsing_json:
        print("Error parsing JSON:", str(error_parsing_json))
           
    # # Simpan data ke file atau lakukan operasi lain sesuai kebutuhan Anda
    # # Misalnya, simpan data ke file teks
    # with open("received_data.txt", "a") as file:
    #     file.write(payload + "\n")

# Fungsi untuk memulai perekaman video
def start_recording(current_round_code):
    global video_writer, recording
    recording = True
    
    # Mendapatkan tanggal, bulan, dan tahun saat ini
    now = datetime.now()
    tanggal = now.day
    bulan = now.month
    tahun = now.year
    jam = now.hour
    menit = now.minute
    
    rec_root_folder_path = "recorder"
    rec_subfolder_path = f"{tanggal:02d}-{bulan:02d}-{tahun}"
    rec_subsubfolder_path = f"{jam:02d}"
    rec_full_path = os.path.join(rec_root_folder_path,
                                 rec_subfolder_path,
                                 rec_subsubfolder_path)
       
    
    #set filename to save
    rec_name = os.path.join(rec_full_path,
                            current_round_code + rec_format)
    
    
    #set path for 2 days ago
    target_date = now - timedelta(days=2)
    rec_subfolder_to_delete_path = target_date.strftime("%d-%m-%Y") 
    rmrec_full_path = os.path.join(rec_root_folder_path,
                                   rec_subfolder_to_delete_path)
    
    
    # print(full_path)
    if not os.path.exists(rec_full_path):
        os.makedirs(rec_full_path)
        print(f"Folder '{rec_full_path}' berhasil dibuat.")
    # else:
        # print(f"Folder '{rec_full_path}' sudah dibuat.")
    
    
    # print(rmrec_full_path)
    if os.path.exists(rmrec_full_path):
        shutil.rmtree(rmrec_full_path, ignore_errors=True)
        print(f"Folder {rmrec_full_path} telah dihapus.")
    # else:
        # print(f"Tidak ditemukan folder {rmrec_full_path}.")
    
        
    # print(rec_name)
    video_writer = cv2.VideoWriter(rec_name,
                                   cv2.VideoWriter_fourcc(*rec_fourcc),
                                   rec_fps,
                                   (rec_frame_width,rec_frame_height))

# Fungsi untuk menghentikan dan menyimpan perekaman video
def stop_recording():
    global video_writer, recording
    recording = False
    video_writer.release()

# ... (kode selanjutnya)

recording = False  # Inisialisasi status perekaman video

# Konfigurasi klien MQTT
client = mqtt.Client()
client.on_message = on_message

client.connect(ip_broker)
client.subscribe(topic)  # Ganti "topic/data" dengan topik yang Anda gunakan



while True: 
    ret, frame = cap.read()
    # ret, frame2 = capp.read()
    # Periksa pesan MQTT secara non-blok
    client.loop(timeout=0.001)
    # print(status)
    # Jika sedang merekam, tulis frame video
    if recording:
        video_writer.write(frame)
    cv2.imshow('RTSP', frame)
    # cv2.imshow('RTSSP', frame2)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Melepaskan sumber daya
cap.release()
# capp.release()
video_writer.release()
cv2.destroyAllWindows()