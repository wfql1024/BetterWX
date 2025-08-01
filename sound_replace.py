from _utils import *

title("Sound Replace")
print("\n - Replace WeChat notification sounds.")

# [Weixin.dll]
dll = dllpath(input(f"\n{BOLD}Weixin.dll{NO_BOLD} (leave blank = auto detect): "))
data = bytearray(load(dll))
# Data structure: 4 bytes length + data
# Search for WAV header to find the sound files.
# Sound 0 000110D0 = Lock
# Sound 1 0001678C = Notify
# Sound_2_00022E2C = Call Action
# Sound_3_000857AE = Call Ring
# Sound_4_000126E0 = Unlock
NAMES = {
    (0, 0x000110D0): "Lock",
    (1, 0x0001678C): "Notify",
    (2, 0x00022E2C): "Call Action",
    (3, 0x000857AE): "Call Ring",
    (4, 0x000126E0): "Unlock",
}
WAV_PATTERN = "RIFF????WAVEfmt"
print(f"\n> Find WAV header")
matches = search(data, WAV_PATTERN)

print(f"\n> Replace sound files")
for i, idx in enumerate(matches):
    length_offset = idx - 4
    length_data = data[length_offset : length_offset + 4]
    wav_length = int.from_bytes(length_data, "big")
    if wav_length > len(data):
        print(f"{YELLOW}[WARN] Invalid WAV length: {wav_length:X}{RESET}")

    wav_name = f" [{NAMES[(i, wav_length)]}]" if (i, wav_length) in NAMES else ""
    wav = wavpath(
        input(
            f"\n{BOLD}Sound {i} {wav_length:08X}{wav_name}{NO_BOLD} (leave blank = skip): "
        )
    )
    if not wav:
        print(f"{GREEN}no change{RESET}")
        continue

    wav_data = load(wav)
    if wav_data[:4] != b"RIFF" or wav_data[8:15] != b"WAVEfmt":
        print(
            f"{RED}[ERR] Invalid WAV header: {wav_data[:16]}, please use a valid WAV audio file!{RESET}"
        )
        pause()
        exit()
    rate = int.from_bytes(wav_data[0x18:0x1C], "little")
    if rate != 44100:
        print(
            f"{YELLOW}[ERR] Sound file sample rate must be 44100Hz, got {rate}Hz{RESET}"
        )
    if wav_data[0x24:0x28] != b"data":
        data_pos = wav_data.find(b"data", 0x24)
        if data_pos == -1 or data_pos + 8 > len(wav_data):
            print(f"{RED}[ERR] WAV data chunk not found.{RESET}")
            pause()
            exit()
        skipped = wav_data[0x24:data_pos]
        preview = skipped[:40].decode("ascii", "replace") + (
            "..." if len(skipped) > 40 else ""
        )
        print(
            f"{YELLOW}[WARN] Skipped {len(skipped):X} bytes of metadata: {preview}{RESET}"
        )
        riff_size = len(wav_data) - 8 - len(skipped)  # Fix RIFF ChunkSize
        wav_data = (
            wav_data[:0x04]
            + riff_size.to_bytes(4, "little")
            + wav_data[0x08:0x24]
            + wav_data[data_pos:]
        )
    if len(wav_data) > wav_length:
        print(
            f"{YELLOW}[WARN] Sound file too long ({len(wav_data):X} > {wav_length:X}), THE EXTRA PART WILL BE TRUNCATED!{RESET}"
        )
        wav_data = wav_data[:wav_length]
    if len(wav_data) < wav_length:
        count = wav_length - len(wav_data)
        print(f"{BLUE}[i] Sound file too short, filling {count:X} zero bytes{RESET}")
        wav_data += b"\x00" * count
    data[idx : idx + wav_length] = wav_data
    print(
        f"{GREEN}[√] Replaced Weixin.dll[{idx:08X}:{idx + wav_length:08X}] with <- {wav.name}{RESET}"
    )

# Backup and save
backup(dll)
save(dll, data)
pause()
