import serial
import time


arduino = serial.Serial("COM7", 9600, timeout=1)
time.sleep(2)

def send_command(cmd):
    arduino.write(f"{cmd}\n".encode())
    while True:
        line = arduino.readline().decode().strip()
        if line:
            print("Arduino:", line)
        if line == "moved OK":
            break

def move(a=0,b=0):
    points = [(a,b)]
    for a, b in points:
        arduino.write(f"{a},{b}\n".encode())

        while True:
            line = arduino.readline().decode().strip()
            if line:
                print("Arduino:", line)

            if line == "OK":
                break

def run():
    from cordi import take
    k=take()
    for i in k:
        if i=="UP":
            send_command("UP")
            time.sleep(5)
            continue
        if i=="DOWN":
            send_command("DOWN")
            time.sleep(5)
            continue
        move(i[1],i[0])
        print(i)

run()
# send_command("DOWN")
# send_command("UP")
# send_command("DOWN")
# send_command("UP")
# send_command("DOWN")

move(0,-5)


arduino.close() 