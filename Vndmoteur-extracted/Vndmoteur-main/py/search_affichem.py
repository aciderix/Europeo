
try:
    with open(r'f:\Europeo\FRONTAL\dll\couleurs1.vnd', 'rb') as f:
        data = f.read()

    # Simple text extraction
    text = "".join([chr(b) if 32 <= b <= 126 else "\n" for b in data])
    
    print(f"Searching in file size {len(data)}")

    if "AFFICHEM" in text:
        print("FOUND AFFICHEM!")
        # Find context
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if "AFFICHEM" in line:
                print(f"Line {i}: {line}")
    else:
        print("AFFICHEM NOT FOUND.")

except Exception as e:
    print(e)
