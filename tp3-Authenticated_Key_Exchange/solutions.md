As previously, this file contains general theory and explanation that will help to do the TP. Detailed solution for question 1 on the `.xopp`.

# Asymmetric Cryptography & Key Exchange Primitives

While AEAD and KDFs secure the channel *after* a key is established, Authenticated Key Exchange (AKE) protocols are used to safely agree on that shared key over an untrusted network.

## Properties of Authenticated Key Exchange (AKE)
When analyzing an AKE protocol, we evaluate it against specific security goals.

### 1. Authentication Levels
*   **One-Sided Security:** Only one party proves their identity (Server authenticates itself via a certificate, but the Client remains anonymous).
*   **Two-Sided (Mutual) Security:** Both the Client and Server prove their identities to each other .

### 2. Forward Secrecy (Perfect Forward Secrecy - PFS)
**Definition:** If an attacker records all encrypted network traffic for years, and then physically breaches the server today to steal its long-term private keys ($sk$), they still *cannot* decrypt the past traffic.


### 3. Session Freshness
Both parties must contribute randomness (a nonce or a fresh ephemeral key) to the final session key. If only Party A dictates the key and Party B contributes no randomness, Party B cannot guarantee the session is fresh, making the protocol vulnerable to replay attacks.



## Digital Signatures & Certificates
Used to prove identity and ensure authenticity. Denoted as a scheme $S = (S.Gen, S.Sign, S.Verify)$:
*   **$S.Gen()$**: Generates a long-term Key Pair: a private signing key ($sk$) and a public verification key ($pk$).
*   **$S.Sign(sk, m)$**: Produces a signature $\sigma$ over message $m$ using the private key.
*   **$S.Verify(pk, m, \sigma)$**: Outputs True if $\sigma$ is valid for message $m$ using public key $pk$.
*   **Certificates**: To prevent an attacker from just sending their own public key and claiming to be the server, public keys are bundled into Certificates signed by a trusted Certificate Authority (CA). A certificate securely binds an identity ($id$) to a public key ($pk$).

## Key Encapsulation Mechanism (KEM)
Here we are securely transmitting a symmetric key using asymetric public-key cryptography.
*   **$KEM.Gen()$**: Generates an asymmetric key pair $(sk, pk)$. 
*   **$KEM.Encap(pk)$**: Takes a public key and generates a *random* symmetric session key $k$ (unrelated to the pk) and its corresponding ciphertext encapsulation $c$. 
*   **$KEM.Decap(sk, c)$**: Takes the private key and the ciphertext $c$ to recover the same symmetric key $k$.

**Ephemeral vs. Static Keys:** 
*   **Ephemeral Keys (Freshness):** The asymetric key pair generated with $KEM.Gen()$, are generated on-the-fly for a single session (new keypair per connection) **and immediately deleted afterward**.
*   **Static/Stable Keys:** Long-term keys reused across multiple sessions. 

## Putting it all together - How to achieve forward secrecy:
The symetric session key ($k$) must be ephemeral, as well as the asymetric key pairs ($pk, sk$) used to share it ! Instead of using Party B's long-term key to encrypt the session, the long-term key is only used to *prove identity*. For the actual encryption key $k_{temp}$, we generate a "throwaway" keypair $pk_{temp}, sk_{temp}$.

Let's walk through it step-by-step:

1. **The Ephemeral Generation:** Party A wants to talk to Party B. Instead of looking up B's long-term public key, Party A says "Hello." 
   * Party B generates a **brand new, temporary KEM key pair** on the spot ($pk_{temp}$, $sk_{temp}$).

2. **The Authentication (Signatures):** Party B needs to prove they are the real Party B. So, Party B takes their **long-term private signature key** and signs the temporary public key: $Signature = Sign(sk_{longterm}, pk_{temp})$.
   * Party B sends both $pk_{temp}$ and the $Signature$ to Party A.

3. **The Encapsulation (KEM):** Party A verifies the signature using B's long-term certificate. Since it's valid, A knows $pk_{temp}$ really came from B.
   * Party A now runs $KEM.Encap(pk_{temp})$ to generate the symmetric session key $k$ and the ciphertext $c$. 
   * Party A sends $c$ to Party B.

4. **The Decapsulation:** Party B uses their **temporary private key** ($sk_{temp}$) to decapsulate $c$ and recover $k$.

5. **THE MOST IMPORTANT STEP (Destruction):** As soon as $k$ is established, both Party A and Party B **permanently delete** $sk_{temp}$ and $pk_{temp}$. If the long-term key leaks, the attacker can impersonate the server in the future, but past ephemeral keys are already destroyed.

## Common Attacks on Key Exchange Protocols
To prove an AKE protocol is insecure, you must construct an attack scenario. Look for these vulnerabilities:

### 1. Replay Attacks in AKE
If a protocol does not use nonces or randomness from the receiver, an attacker can capture the initiator's initial messages (the KEM encapsulation $c$ and the signature) and resend them later.
*   **Consequence:** The receiver will process the old message and derive the *exact same session key* $k$ as a previous session. This violates freshness and can allow the attacker to replay old encrypted app-layer traffic as well.

### 2. Identity Misbinding
**Definition:** Party A thinks they are securely talking to Party B. Party B actually thinks they are securely talking to Party C (the attacker). **The attacker doesn't know the session key**, but they trick the parties into sharing a key while having mismatched beliefs about who is on the other end. 
*   **How to spot it:** This happens if the protocol signatures do not explicitly cover the **identities** ($id_P, id_Q$) of the participants, or if the identities are not bound into the final KDF (e.g., $k' = KDF(k, id_P, id_Q)$). 
*   **The Attack:** A client signs a KEM ciphertext. The attacker intercepts it, strips the client's signature, applies their *own* signature, and forwards it to the server. The server derives the key $k$ and thinks it belongs to the attacker, while the client derives $k$ and thinks they are talking to the server.


A detailed Explanation for one of the Variation is explained below. Read it if you are lost.

### 3. Key Exposure Attack
What happens to the protocol if the ephemeral symetric session key or a specific long-term key is compromised?

### 4. Deterministic State (Dummy Protocol)
If a protocol has no secret initial state (no long-term private keys) and samples *no randomness* during execution, its outputs are entirely deterministic. An eavesdropper can simply simulate the exact same computations locally to deduce the session key. 


---

# Exercise 1 - Variation 4 

### 1. The Protocol in Variation 4
In Variation 4, the identity of the initiator ($id_P$) is removed from the responder's ($Q$) signature. The protocol looks like this:

1. **$P \to Q$ :** $pk, \ S.Sign_{sk_P}(pk, id_Q)$ 
2. **$Q \to P$ :** $c, \ S.Sign_{sk_Q}(pk, c)$
*(Note how $Q$'s signature covers the public key and ciphertext, but omits $P$'s identity).*

### 2. The Attack Execution
Let’s introduce an active attacker, **Eve ($E$)**, who has her own legitimate account/identity in the system ($id_E$) and her own long-term signature keys ($sk_E, pk_E$).

1. **$P$ initiates a connection to $Q$:**
   $P$ generates an ephemeral KEM key pair $(sk, pk)$ and sends the initial message over the network:
   $P \to [Eve]: pk, \ S.Sign_{sk_P}(pk, id_Q)$

2. **Eve intercepts and modifies the message:**
   Eve strips away $P$'s signature. She keeps $P$'s ephemeral public key ($pk$) and generates a *new* signature using her own private key, claiming she is the one initiating the connection to $Q$:
   $[Eve] \to Q: pk, \ S.Sign_{sk_E}(pk, id_Q)$

3. **$Q$ receives the message:**
   $Q$ verifies Eve's signature. Because it is mathematically valid, $Q$ thinks: *"Ah, Eve wants to establish a secure channel with me using this public key $pk$."*
   $Q$ encapsulates a session key $k \gets KEM.Encap_{pk}()$ to produce ciphertext $c$.
   $Q$ signs the response *(as dictated by Variation 4)* and sends it back:
   $Q \to [Eve]: c, \ S.Sign_{sk_Q}(pk, c)$

4. **Eve intercepts and forwards the message:**
   Because Variation 4 does **not** include the identity of the person $Q$ thinks he is talking to ($id_E$) inside the signature, Eve can just forward this exact message directly to $P$:
   $[Eve] \to P: c, \ S.Sign_{sk_Q}(pk, c)$

5. **$P$ receives the message:**
   $P$ checks $Q$'s signature. It successfully verifies over $pk$ and $c$. $P$ uses their ephemeral secret key ($sk$) to decapsulate $c$ and recover the session key $k$. $P$ thinks: *"Great, I have established a secure channel with $Q$."*

### 3. The Result (The Misbinding)
Let's look at the final state of the protocol:
* **$P$** holds key $k$, and thinks they share it with **$Q$**.
* **$Q$** holds key $k$, and thinks they share it with **Eve**.
* **Eve** does *not* know $k$ (because she doesn't have $P$'s ephemeral private key).

### 4. Why is this a problem?
You might think: *"If Eve doesn't know the key, who cares? The channel between $P$ and $Q$ is still encrypted!"* 

But cryptography is about more than just secrecy; it's about **Authentication context**.

**Scenario: A Banking Application**
Imagine $P$ is Alice, $Q$ is her Bank, and this protocol is used to establish the encrypted tunnel for their banking app.
1. Alice ($P$) thinks she has a secure connection to the Bank ($Q$).
2. The Bank ($Q$) has a secure connection, but thinks the person on the other end is Eve.
3. Alice sends an encrypted request using key $k$: *"Deposit my $1,000 paycheck."*
4. The Bank receives the encrypted request and decrypts it with key $k$.
5. The Bank processes the request under the identity associated with key $k$. The Bank's internal system says: *"I just received a valid encrypted deposit request over the secure channel I share with Eve. I will credit $1,000 to Eve's account."*

Eve just stole Alice's money without ever having to break the encryption or decrypt the traffic! She simply manipulated the **identities** bound to the session key.

### How the original AKE1 prevented this
If $Q$ had signed $id_P$ as well (as in the original AKE1: $s_Q = S.Sign_{sk_Q}(pk, c, id_P)$), the attack would fail at Step 4. 

When $Q$ replied to Eve in Step 3, $Q$'s signature would have been $S.Sign_{sk_Q}(pk, c, \mathbf{id_E})$. If Eve forwarded that to $P$, $P$ would see $id_E$ in the signature, realize the message wasn't meant for them, and immediately abort the connection.

---

# Exercise 2

### Question 1: Properties of the outputs
*If both parties execute the protocol correctly and the communication between them is not tampered with, what are the important properties satisfied by the outputs of these key establishment protocols?*

**Solution:**
Assuming no active attacker tampering with the packets, the outputs of KE1 and KE2 satisfy three main properties:
1. **Correctness (Key Agreement):** Both the Client ($C$) and the Server ($S$) will output the exact same shared session key ($k_C = k_S$).
2. **Confidentiality (Secrecy):** The resulting session key is known *only* to $C$ and $S$. An eavesdropper observing the public network cannot compute the session key because they do not have the server's private key ($sk_S$) required to decapsulate the ciphertext ($c_C$).
3. **One-Sided Authentication:** The client is guaranteed that they are establishing a key with the legitimate server $S$ (because only $S$ holds the private key $sk_S$ matching the verified certificate). However, the server does *not* know who the client is (the client remains anonymous).

---

### Question 2: Weaknesses in KE1 fixed in KE2 & Practical Exploitation
*What is the weakness in KE1 that is fixed in KE2? How could it be exploited in practice (e.g., you may consider that this is the key establishment for a TLS-like protocol)?*

**Solution:**
* **The Weakness (Lack of Server Contribution/Freshness):** In KE1, the final session key is dictated entirely by the client ($k_C$). The server contributes no randomness. Because the server's public key ($pk_S$) is static, if an attacker records the client's ciphertext ($c_C$), they can replay it at any time in the future.
* **The Fix in KE2:** KE2 introduces a random nonce generated by the server ($r_S \leftarrow \{0,1\}^{256}$). The final session key is derived using a Key Derivation Function ($KDF(r_S, k_C)$). This ensures that the server contributes to the **freshness** of the session key. 
* **Exploitation in Practice (Replay Attack):** 
  If KE1 is used for a TLS-like protocol, an attacker can record the initial key exchange ($c_C$) *and* the subsequent encrypted application data (e.g., an encrypted HTTP `POST /transfer?amount=100` request). 
  Later, the attacker opens a new connection to $S$ and replays $c_C$. The server will decapsulate $c_C$ and derive the *exact same session key* $k_S$ as before. The attacker then replays the encrypted HTTP request. The server will successfully decrypt it and process the bank transfer a second time.
  In **KE2**, this attack fails: if the attacker replays $c_C$, the server will generate a *new, completely different* $r_S$ for the session. The resulting key $KDF(r_S, k_C)$ will not match the old key, and the replayed encrypted HTTP request will fail the AEAD decryption check (outputting `⊥`).

---

### Question 3: TLS comparison and Improving KE2
*Which security property/properties does the TLS key establishment enjoy, compared to KE2? Propose a way to improve KE2 in that respect, without using a digital signature Sign operation in the protocol.*

**Solution:**
* **Missing Security Property:** Neither KE1 nor KE2 provides Forward Secrecy because the confidentiality of the session key relies entirely on the server's long-term key ($pk_S/sk_S$). TLS key establishment enjoys **Perfect Forward Secrecy (PFS)**, which KE2 entirely lacks. In KE2, if the server's long-term private key ($sk_S$) is compromised in the future, an attacker can look at their logs, decapsulate past $c_C$ values to get $k_C$, and easily compute $KDF(r_S, k_C)$ because $r_S$ was sent in plaintext. 

* **How to improve KE2 (Achieving Forward Secrecy without `Sign`):**
To achieve Forward Secrecy, we must use an *ephemeral* key exchange, but we are not allowed to use Digital Signatures to authenticate it. We can solve this by encapsulating against **two** different public keys: the server's static certificate key (for authentication) and a newly generated ephemeral key (for forward secrecy). This is heavily inspired by the **KEMTLS** framework.

**Improved Protocol (KE3):**
1. $C$ opens a connection to $S$.
2. $S$ generates a fresh, **ephemeral** KEM keypair: $(sk_E, pk_E) \leftarrow KEM.Gen()$.
3. $S$ sends to $C$: its static certificate (containing static $pk_S$) **and** the ephemeral public key $pk_E$.
4. $C$ verifies the certificate for $(S, pk_S)$.
5. $C$ performs *two* encapsulations:
   * $(k_{stat}, c_{stat}) \leftarrow KEM.Encap(pk_S)$ *(Authenticates the server)*
   * $(k_{eph}, c_{eph}) \leftarrow KEM.Encap(pk_E)$ *(Provides Forward Secrecy)*
6. $C$ sends both ciphertexts $(c_{stat}, c_{eph})$ to $S$.
7. $S$ decapsulates both:
   * $k_{stat} \leftarrow KEM.Decap(sk_S, c_{stat})$
   * $k_{eph} \leftarrow KEM.Decap(sk_E, c_{eph})$
8. Both parties compute the final session key using the KDF: 
   **$Key = KDF(k_{stat}, k_{eph})$**. 
9. $S$ instantly deletes $sk_E$.

**Why this works:**
* **No `Sign` operation is used:** Authentication is achieved implicitly because only the true Server possesses $sk_S$ to decapsulate $c_{stat}$. 
* **Forward Secrecy is achieved:** The final session key is bound to $k_{eph}$. Because $sk_E$ is ephemeral and deleted immediately after the handshake, an attacker who compromises the static $sk_S$ years later cannot decapsulate $c_{eph}$, meaning they cannot compute the KDF to recover the final session key.

---
# Exercise 3

To establish a secret over a public channel, you *must* have some source of unobservable entropy (either a pre-shared secret or local randomness). 


### Core Concept: Determinism vs. Secrecy
The problem states two critical weaknesses about Party $P$:
1.  $P$ **does not sample randomness** during the execution of the protocol.
2.  $P$ **does not have secret values** as part of its initial state (its initial state is public knowledge).

So $P$ is essentially a **deterministic state machine** with public initial parameters. Everything $P$ does—how it updates its internal state and what it outputs—depends entirely on the messages it receives from the network. 

Because the adversary $A$ is an eavesdropper, they can see the entire transcript $T$ (every message sent and received by $P$). Therefore, $A$ sees the exact same inputs that $P$ sees.

### Building the Adversary $A$
To prove that $\text{AnonKEadv}[A,\mathcal{P}] = 1$, we must write an algorithm for the adversary $A$ that takes the transcript $T$ and successfully outputs $\hat{k} = k$ exactly 100% of the time.


1.  **Initialize a Simulation:** $A$ creates a local software clone of Party $P$ on their own machine. Because $P$'s initial state contains no secrets, $A$ can perfectly initialize this simulated $P$ to the exact same starting state as the real $P$.
2.  **Read the Transcript:** $A$ looks at the recorded network transcript $T$, which contains the sequence of all messages exchanged between $P$ and $Q$.
3.  **Feed the Simulation:** For every message in $T$ that was sent by $Q$ to $P$, adversary $A$ inputs that message into their locally simulated $P$.
    *   *Note:* Because the simulated $P$ is completely deterministic, whenever it processes $Q$'s message, it will generate an outgoing message that perfectly matches what the real $P$ sent in transcript $T$.
4.  **Extract the Key:** After the final message in $T$ is processed, the real $P$ completes the protocol and outputs the session key $k$. Because the simulated $P$ underwent the exact same deterministic state transitions as the real $P$, the simulated $P$ will compute and output a key $\hat{k}$.
5.  **Output:** $A$ outputs $\hat{k}$.

### Conclusion & Advantage
Because there is zero randomness and zero hidden state in $P$, the local simulation is a mathematically perfect mirror of the real execution. 
Therefore, the simulated key is guaranteed to be the actual key ($\hat{k} = k$). 

$$ \Pr[\hat{k} = k \mid \hat{k} \leftarrow A(T)] = 1 $$

Thus, the adversary's advantage is **1 (or 100%)**. 

### Broader Takeaway (Why does this matter?)
You might ask: *"What if Party $Q$ has a super-secure long-term private key and uses excellent randomness?"*

**It doesn't matter.** If a protocol requires two parties to arrive at the *same* shared key $k$, the security of that key is bounded by the weakest link. If $Q$ is forced to establish a key with a completely deterministic, public $P$, $Q$ must inherently transmit enough information over the public channel for $P$ to calculate $k$. The adversary simply uses that same public information to calculate $k$ alongside $P$. 

To be secure against eavesdroppers, **both** parties must contribute to the key using either a hidden initial state (like a long-term private key) or local randomness (like generating an ephemeral KEM keypair).

---
# Exercise 4 

Cryptography assumes the attacker only sees the ciphertext. However, Side-Channel attacks exploit the *metadata* of the encryption process—in this case, the **size of the ciphertext**.

### 1. The Vulnerability: Compression + Encryption + User Control
**BREACH** (Browser Reconnaissance and Exfiltration via Adaptive Compression of Hypertext) targets HTTPS responses. It requires three conditions to be met on the server:
1.  **HTTP Compression is enabled** (e.g., gzip/Deflate).
2.  **User-input is reflected** in the HTTP response body (e.g., a URL parameter like `?username=alice` is printed on the page).
3.  **A highly sensitive secret** is present in that same response body (e.g., a CSRF token).

### 2. How Compression Leaks Data
Algorithms like `gzip` (DEFLATE) compress data by finding repeated sequences of bytes and replacing them with short "pointers" to the previous occurrence.
*   If a string appears once, it takes up normal space.
*   If a string appears twice, the second instance is compressed into a tiny reference, **making the overall HTTP response smaller.**
*   Encryption (like AES/TLS) encrypts this compressed payload. Encryption hides the *content*, but it **does not hide the length**. The attacker can observe the `Content-Length` of the encrypted packets passing over the network.

### 3. Exploitation Strategy (The Oracle Attack)
Imagine the server's HTML contains a secret: `CSRF_TOKEN: 7b9a`.
The attacker tricks the victim's browser into making repeated requests to the server, injecting a guess into the reflected parameter:
*   **Request 1 (Guess "0"):** `?username=CSRF_TOKEN: 0`. The server response contains `CSRF_TOKEN: 0` and `CSRF_TOKEN: 7b9a`. No significant overlap. Length = 500 bytes.
*   **Request 2 (Guess "7"):** `?username=CSRF_TOKEN: 7`. The server response contains `CSRF_TOKEN: 7` and `CSRF_TOKEN: 7b9a`. There is an overlap! The compression engine shrinks it. Length = 498 bytes.

By observing the network length drop, the attacker knows "7" is the correct first character. They then guess "7a", "7b", etc., extracting the secret byte-by-byte in a brute-force manner, purely by looking at the encrypted packet size.

### 4. Mitigations
To prevent BREACH, developers can implement:
1.  **Disable Compression:** Simple, but hurts website performance.
2.  **Length Hiding / Padding:** Add a random amount of garbage data (padding) to every HTTP response to mask the true compressed size. (A TLS feature, though complex to implement perfectly).
3.  **Token Masking (XOR):** Instead of sending a static CSRF token, generate a random nonce for every request. Send `(nonce, token XOR nonce)`. Because the nonce changes every time, the byte sequence of the secret changes on every page load, breaking the compression algorithm's ability to find predictable repeated patterns.

