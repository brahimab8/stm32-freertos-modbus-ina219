import argparse
import serial

def main():
    p = argparse.ArgumentParser(description="Send one byte and print STM32 reply")
    p.add_argument("port", help="Serial port (e.g. COM3 or /dev/ttyUSB0)")
    p.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate")
    p.add_argument("-t", "--timeout", type=float, default=1, help="Read timeout (s)")
    args = p.parse_args()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=args.timeout)
    except Exception as e:
        print(f"Failed to open {args.port}: {e}")
        return

    try:
        while True:
            c = input("Char> ")
            if not c or c.lower() in ("quit","exit"):
                break
            ser.write(c[0].encode())
            resp = ser.readline()
            print("Reply:", resp.decode(errors="ignore").strip() or "<no data>")
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

if __name__ == "__main__":
    main()
