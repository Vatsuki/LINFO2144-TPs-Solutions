
# Exercise 1

Below is just general theory to allow to understand the exercise. Detailled solution on the `.xopp`.

## 1. The Threat
We assume the attacker can:
1. **Eavesdrop:** Read all messages passing through the network.
2. **Intercept:** Stop messages from reaching their destination (drop them).
3. **Modify:** Change the contents of a message.
4. **Inject/Replay:** Insert new messages or resend older messages they previously recorded.

The only thing the attacker *cannot* do is break the underlying cryptography (e.g., they cannot guess the secret key). 


## 2. The Cryptographic Toolbox
To defend against the attacker, the algorithms use specific cryptographic primitives.

### 1. AEAD (Authenticated Encryption with Associated Data)
Denoted as `(Enc, Dec)`, AEAD is the standard for symmetric encryption. It takes three inputs: a Key ($k$), a Nonce ($n$), and a Message ($m$).
*   **Confidentiality:** It encrypts the message so the attacker cannot read it.
*   **Integrity & Authenticity:** It attaches an authentication tag to the ciphertext. When the receiver calls `Dec`, the algorithm checks this tag. If the ciphertext was altered, or if it was encrypted with a different key/nonce, `Dec` will output `⊥` (Error / Bottom).
*   **IMPORTANT: Nonces must NEVER be reused with the same key.** A "nonce" is a Number Used Once. If an attacker sees two different messages encrypted with the *same key* and the *same nonce*, the security of the AEAD is completely shattered.

### 2. KDF (Key Derivation Function)
Denoted as `F(k, ...)`. A KDF takes a high-entropy secret (the master key $k$) and uses it to derive one or more sub-keys. 
*   **Domain Separation:** We use KDFs to ensure that different parts of a system use different keys. For example, rather than using one key for everything, we can derive a specific "Sending Key" and "Receiving Key." If an attacker breaks or manipulates one stream of communication, the other remains secure.


## 3. Properties of a Secure Channel
When evaluating the algorithms, we must check them against the following properties:

### 1. Correctness
**Definition:** If Party A sends a sequence of messages, and there is no attacker on the network, Party B must be able to receive and successfully decrypt them. 
*   **Full-Duplex Communication:** Modern channels are asynchronous. Party A and Party B can send messages at the exact same time. 
*   **Red Flag:** Look at the variables initialized in `Init`. If an algorithm uses a *single, shared counter* for both sending and receiving the algorithm is not correct. If both parties speak at the same time or messages arrives out of order, their counters will fall out of sync, and legitimate messages will output `⊥`. 

### 2. Confidentiality, Integrity, and Authenticity
Because all the algorithms use an AEAD, these three properties are largely guaranteed out-of-the-box, **provided the nonce is never reused.** 

### 3. Replay Protection
**Definition:** An attacker records a valid message sent by Party A yesterday, and sends it to Party B today. Party B must reject it.
*   **How to achieve it:** The receiver must maintain a state (like a counter `n_r`). When a message arrives, the receiver decrypts it using their expected counter, and then increments their counter. If the attacker replays an old message, the receiver will try to decrypt it with the *new, incremented counter*, the AEAD tag won't match, and it will output `⊥`.
*   **Red Flag in Code:** If the `Recv` function accepts a nonce supplied by the ciphertext (sent in the clear, not a internal tracked counter) and uses it to decrypt without verifying if it is fresh, the algorithm is vulnerable to replay attacks.


### 4. Reflection Protection
**Definition:** An attacker intercepts a message sent by Party A, and sends it *back* to Party A. Party A must reject it.
*   **How to achieve it:** You must have **Directional Symmetry Breaking** (Domain Separation). There are two ways to do this:
    1.  **Key Separation:** Party 0 sends with Key X and receives with Key Y. Party 1 sends with Key Y and receives with Key X (This is done using the KDF based on the role $R$).
    2.  **Nonce Separation:** Both parties use the same Key, but they use different nonces. For example, Party 0 only uses *even* nonces, and Party 1 only uses *odd* nonces.
*   **Red Flag in Code:** If Party A and Party B use the exact same Key *and* the exact same nonce spaces, an attacker can reflect Party A's first message back to Party A, and Party A's receiver will accept it. `Recv` should use a different key (because of the KDF), or expects a completely different nonce (e.g., odd vs even), to be secure against reflection.


### 5. In-Order Delivery & Drop Detection
**Definition:** If Party A sends Message 1 then Message 2, Party B must process them in that exact order. If an attacker drops Message 1, Party B must reject Message 2.
*   **How to achieve it:** Strict, sequentially incrementing counters (e.g., $n = n + 1$ on both send and receive). If Message 1 is dropped, Party B's counter doesn't advance. When Message 2 arrives (encrypted with nonce 2), Party B will try to decrypt it with nonce 1, resulting in `⊥`.

---

# Exercise 2 Confidentiality beyond standard definition

## TLS traffic sniffing.

-	Regular tiny packet : probably ping / keep alive packets  to keep the socket open and ensure real-time push notifications can be received.
-	On big packet : You can suppose a message has been send / received. 

You don’t know the content but you know when it has been send, the IP source and IP dest (maybe a server and not an end-user). Like Whatsapp, you can analyze the behavior of the user (message frequency, contacts,...) even though you don’t know the content of the message.
If you are running an advertisement business, you know if you have just served an add to the user.  If you observe a 200-byte packet sent by the user's device immediately after displaying the ad or interacting with it, you can perform a Timing and Length Correlation Attack :

-	You know the exact size (200 bytes) and the exact time it was sent.
-	You can suppose that this 200-byte packet is likely a telemetry/analytics event ("ad_viewed" or "ad_clicked") being sent back to the messaging app's servers.

By fingerprinting the exact byte size of different actions (a text message might average 50 bytes, while an "ad clicked" API call might consistently be exactly 200 bytes once encrypted), the attacker can perfectly map out user behavior without ever breaking the TLS encryption. 

The attack exploits the following protocol’s characteristics:

-	Length Preservation (Deterministic Ciphertext Length): TLS provides confidentiality of the payload, but it does not hide the length of the data. If the length of the ciphertext is almost exactly the length of the plaintext (plus a small fixed overhead), observing the packet size leaks the exact size of the application-layer data.
-	Event-Driven Timing: The protocol transmits data exactly when an event occurs. This immediate transmission creates a timing side-channel.
-	Lack of Metadata Protection: IP addresses (source/destination) and port numbers remain unencrypted in the network and transport layers. TLS only encrypts the application layer.

To mitigate Traffic Analysis (Side-Channel) attacks :
-	Fixed packet size using padding and splitting the payloads data, 
-	Generate dummy traffic at random intervals,
-	Schedule packets transmission to avoid sending packet immediately when an event occurs.

## Interactive SSH

A naive SSH client sends one network packet the exact millisecond a user presses a key. Because SSH and TLS only encrypt the content of the packet but preserve the timing and length, an eavesdropper can see the exact delay between keystrokes.

Because of the physical layout of keyboards, the time it takes to type certain pairs of letters varies. By feeding these microsecond timings into a statistical model, an attacker can predict the sequence of characters typed, completely bypassing the encryption.

The most critical sensitive data sent interactively over SSH is a Password. Users frequently type passwords into remote shells like for the initial login ! If an attacker can deduce the keystrokes via timing analysis, they can recover the user's plaintext passwords. Since packets are send immediately upon key press, this can give out the password lenght.

We can guess when the user is behind the computer typing in its shell or not. We may be able to identify patterns and map them to different commands. Therefore we can get information on what is the user doing. 
We can also distinguish between users based on the typing speed.


**Mitigation :**

OpenSSH 9.5 introduced the ObscureKeystrokeTiming configuration to mitigate this specific vulnerability. It employs two main techniques:
-	Traffic Shaping (Fixed Intervals): Instead of sending a packet immediately upon a key press, the SSH client sends interactive traffic at fixed intervals (default is every 20ms). The real keystroke is delayed and shoved into the next available 20ms "slot".
-	Chaffing (Dummy Packets): The client sends fake keystroke packets ("chaff") for a random interval after the user stops typing.
-	Batching, send packets periodically that contains more than 1 keystroke.

The trade-offs are:
- Security vs. Usability (Latency): A higher interval provides stronger security because it forces all keystrokes into heavily delayed buckets, fully destroying timing patterns. However, a remote shell requires low latency. If the interval is too high, the user will experience highly degraded usability.
- Security vs. Network Performance (Bandwidth/Overhead): To hide the typing, OpenSSH sends constant fixed-interval packets and generates fake chaff packets. This means a single typed character might result in more than one packets being sent instead of just one. This increases network overhead, bandwidth usage, ...


# Exervise 3 - Timing Side-Channel Attack

`server.py` :

```python
PINCODE = "33102144"

def verify_pincode(pincode):
    if len(pincode) != len(PINCODE):
        return False
    time.sleep(0.01)
    for check, ref in zip(pincode, PINCODE):
        if check != ref:
            return False
        else:
            time.sleep(0.01)
    return True
# [...]
```

**Guess the length of the PIN:** 

If we try incorrect length, the server response will be really fast. Right now on localhost, we can check the response time in the browser by clicking F12 then going into the network tab. So as soon as we get a slower answer we can suppose it's the password length. In practice an attacker would write a Python script using the requests library to send PINs of length 1, 2, 3... and measure the response time. Because network latency fluctuates, the script would send each length 10 or 20 times and take the average to filter out noise.

**Guessing the PIN:**

-	To brute force, supposing it's only decimal numbers (0 to 9), their is 10^(size of the password) = 10^8 possibilities.
-	If you guess digits one-by-one, 80 possibilities in the worst case : 10 attempts to find the first digit, 10 for the second, ...
-	When we find the first digit, the server will check the second number we provided, making the respond slightly slower. Therefore we try a 8 digits number and change the first digit until we get a slower. We know no what is the first digit.
-	Yes, we can extend this to all digits by keeping the first digit found and then try all possibilities for the second digits until we can a slower answer. We keep going until we have found all of them.


# Exercise 4 - 4 SSH with compression security

**zlib behavior: 2n distinct characters vs. 2 identical strings of n characters**

zlib compress data by finding repeated sequence of bytes and replacing the second occurence with a short "pointer" (lenght an distance) to the first occurence. A string of $2n$ dinstinct chracters will hardly compress at all becasue there are no repetitions. however, the concatenation of two identical strings of lenght $n$ will compress very well. The first strin g is stored nromally, the second entirely replaced by a tiny pointer saying "copy n bytes from n bytes ago". Therefore the output is much smaller.

**Extending to evil + secret**
If we send an evil string that shares exactly some characters wtih the secret, the compression algo will spot the repetition. If we send evil = "Paris" and the secret contains it, the total lenght of the encrypted payload will reduce ! By systematically guessing into evil and measureing the output we can guess the sercret. The guess that results in the samllest packet size will be the correct one.


# Exercise 5 - Performance comparison

