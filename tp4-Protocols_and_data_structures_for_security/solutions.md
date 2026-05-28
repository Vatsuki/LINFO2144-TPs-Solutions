
# Exercise 1 - Toy DNSSEC

### Background Knowledge 
*   **DNS Spoofing / Cache Poisoning:** In standard DNS, responses are unauthenticated. An attacker on the network can send fake responses to redirect users to malicious IP addresses and the user DNS resolver will cache the fake responses.
*   **Public Key Infrastructure (PKI) & Chain of Trust:** A system to authenticate data. Instead of hardcoding every public key in the world, you hardcode one "Root" public key. The Root signs the public key of `.be`. Then `.be` signs the public key of `uclouvain.be`. To verify the final server, you follow this chain of signatures back to the trusted Root.
*   **Replay Attacks on State Changes:** If data is signed and then later deleted or updated, an attacker might save the old signature and keep broadcasting the old data. To prevent this, cryptographic systems use **freshness mechanisms** like sequence numbers or explicit expiration timestamps.

### Solutions

**1. What security property does DNSSEC guarantee? Which attack(s) does this mechanism prevent?**
*   **Data Origin Authenticity:** It mathematically proves that the DNS response actually originated from the authoritative name server for that domain. An attacker cannot insert fake nodes/domains because they lack the parent's private signing key.
*   **Data Integrity:** It proves the data (e.g., the IP address) has not been altered in transit. 
*   **Attacks Prevented:** It prevents Man-In-The-Middle (MITM) attacks, DNS spoofing, and DNS cache poisoning.

**2. How should a DNS client verify the security of the DNS data for a domain?** 

To verify a domain like `uclouvain.be`, the client must validate the **Chain of Trust**:
1.  **Trust Anchor:** The client must already know and trust the public key ($pk$) of the Root (`.`). This is typically hardcoded into the OS or the DNS resolver software. The Root Server is an authoritative server, but doesn't know the IP address of `uclouvain.be`. It only knows exactly which servers are in charge of the Top-Level Domains
2.  **Query Root:** The client asks the Root server for the `uclouvain.be` name server information. The Root replies with  IP address for the `.be` name server, its public key ($pk_{be}$) and a signature over the data `(be. || pk_be)`. The client verifies this signature using the Root's $pk$.
3.  **Query the .be Name Server:** The client asks the `.be` name server for `uclouvain.be`. The `.be` server replies with the $pk_{uclouvain.be}$ and the IP address, alongside a signature made by $sk_{be}$.
4.  **Query uclouvain.be:** The Client asks the `uclouvain.be`for actual IP address for `uclouvain.be`." The server replies with the A record and a signature it made using its private key ($sk_{uclouvain.be}$) over the given IP address." The client takes $pk_{uclouvain.be}$ (which it validated in the before step) and checks the signature on the IP address. 

**3. Supporting changes in DNS data (domains added/removed/modified)**
Whenever a server sign (subdomain, subdomain IP, $pk_{subdomain}$), it will be valid forever. There is no concept of time, version or expiration $\rightarrow$ static system. 

This makes it vulnerable to replay attack : 

1. **Day 1:** `uclouvain.be` is hosted on Server A (`IP: 1.1.1.1`). The administrator signs `(uclouvain.be = 1.1.1.1)`. You request the website, your computer verifies the signature, and you securely connect. 
2. **Day 2:** The university upgrades their servers and moves the website to Server B (`IP: 2.2.2.2`). The administrator generates a *new* signature for `(uclouvain.be = 2.2.2.2)`. The university stops paying for Server A, and a malicious hacker buys Server A's old IP address (`1.1.1.1`).
3. **Day 3 (The Attack):** You try to go to `uclouvain.be`. The hacker intercepts your DNS request on the network and sends you the **Day 1 signature** `(uclouvain.be = 1.1.1.1)`.

Your computer looks at the Day 1 signature and verifies it with the Public Key. Because the math checks out (the admin really *did* sign that IP address in the past), your computer accepts it as genuine. You are secretly routed to the hacker's server, completely bypassing the security of DNSSEC.

**Solution:** Introduce **Time-to-Live (TTL) or Expiration Dates**. Every signed DNS record must include a timestamp indicating its validity period (e.g., "Valid until May 30th"). The signature must cover both the DNS data *and* the expiration date. When data is modified or deleted, the old signature will naturally expire, forcing the client to fetch the new, currently valid records.

**4. Alternative system using only hash functions**

a) **Datastructure:** We could use a **Merkle Tree** (Hash Tree). 

b) **How it works:** 
*   All DNS records (IP addresses) in a zone are placed at the leaves (bottom) of the tree.
*   Pairs of leaves are hashed together to form parent nodes, continuing all the way to a single **Root Hash**.
*   Instead of hardcoding the Root public key, the client hardcodes the Root Hash.
*   To resolve a query, the DNS server sends the requested data (leaf) *plus* the "authentication path" (the list of sibling hashes up the tree). The client hashes these together to see if they perfectly reconstruct the trusted Root Hash.

c) **Differences:**
*   **Operational Disadvantage (Huge):** In DNSSEC, updating a single record is easy: you just generate a new signature for that record. With a Merkle Tree, changing *one* IP address changes its hash, which changes its parent's hash, completely altering the global Root Hash. You would have to constantly distribute the new, updated Root Hash to every client in the world via a secure out-of-band channel, which is practically impossible.
*   **Security:** Hash functions are generally faster to compute and are resilient to Quantum Computers (unlike RSA/ECC signatures), but the lack of a private key makes dynamic state management a nightmare.

***

# Exercise 2 - TLS 1.3 and replay

### Background Knowledge
*   **TLS Handshakes:** In normal TLS 1.3 (1-RTT), the client and server exchange random nonces, do a Diffie-Hellman key exchange, and verify signatures *before* any application data (HTTP requests) is sent. This guarantees the session is fresh and prevents replay attacks.
*   **0-RTT (Early Data):** For speed, if a client recently talked to a server, the server gives them a "Session Ticket" (a Pre-Shared Key, PSK). The next time the client connects, they can encrypt their first HTTP request using this PSK and send it *immediately* in the very first packet (`ClientHello`). This saves 1 Round Trip Time (RTT).
*   **The Replay Vulnerability:** Because 0-RTT data is sent *before* the server has a chance to contribute a fresh random nonce to the session, an attacker who intercepts this first packet can copy it and send it to the server multiple times. The server will decrypt it successfully using the PSK.

### Solutions

**Under which exact conditions can TLS 1.3 be vulnerable?**

It is vulnerable when the **0-RTT (Early Data) feature is enabled**, which relies on session resumption using a Pre-Shared Key (Session Ticket) from a previous connection. The attacker simply captures the `ClientHello` packet containing the 0-RTT encrypted payload and replays it.

**Why did protocol designers accept this trade-off?**

**Performance.** 0-RTT eliminates latency. For mobile networks with high latency, or for APIs making frequent short-lived connections, saving one full round-trip of the network drastically speeds up web browsing and application responsiveness. The designers decided the speed boost was worth the risk, *provided* applications implement mitigations.

**Mitigation strategies:**

1.  **Application-Layer Idempotency:** The web server should be configured to only allow "safe" or idempotent HTTP methods (like `GET` requests, which just fetch data) inside 0-RTT early data. Unsafe requests (like `POST` requests transferring money or creating accounts) must be rejected in 0-RTT and forced to wait for the full 1-RTT handshake to complete.
2.  **Server-Side Strike Registers (Single-use tickets):** The server maintains a database (a strike register) of every Session Ticket it has issued. When a 0-RTT request arrives, the server checks the database. If the ticket is present, the server processes the data and *instantly deletes* the ticket. If an attacker replays the packet, the server will see the ticket is no longer in the database and reject it. *(Note: This is difficult to synchronize instantly across large distributed server farms, which is why Mitigation #1 is heavily relied upon).*

***

# Exercise 3 - Merkle tree

### Background Knowledge Required
*   **Cryptographic Hash Functions:** A one-way function ($H$) that maps arbitrary data to a fixed size. Crucially, it must be **Collision Resistant** (it is computationally impossible to find two different inputs that produce the same hash output).
*   **Merkle Trees:** A binary tree where every leaf node is the hash of a data block, and every non-leaf node is the hash of its child nodes' hashes. They are heavily used in Blockchains (Bitcoin) and Certificate Transparency logs because they allow for extremely efficient proofs that data belongs in a large dataset, without downloading the whole dataset.

### Solutions

Check the .xopp(or anotated pdf) for a visual solution.

**1. Describe the construction of the Merkle tree for $X = [9, 3, 7, 5, 2]$**
A Merkle tree is built bottom-up.
*   **Leaves (Level 0):** Hash each individual element in the list.
    $L_1 = H(9)$, $L_2 = H(3)$, $L_3 = H(7)$, $L_4 = H(5)$, $L_5 = H(2)$
*   **Internal Nodes (Level 1):** Concatenate adjacent hashes and hash them. Because 5 is odd, the last element might be paired with a dummy value (or itself, or brought up directly depending on the exact implementation). Let's assume standard pairing:
    $N_{1,2} = H(L_1 || L_2)$
    $N_{3,4} = H(L_3 || L_4)$
    $N_{5} = H(L_5 || empty)$
*   **Internal Nodes (Level 2):**
    $N_{1,2,3,4} = H(N_{1,2} || N_{3,4})$
    $N_{5} = H(N_5 || empty)$ (bringing it up)
*   **Root (Level 3):**
    $Root = H(N_{1,2,3,4} || N_{5})$

**2. Fixed-size identifier and security properties**
*   **Identifier:** The final **Root Hash** is the fixed-size identifier ($n$ bits) representing the entire list $X$.
*   **Security Properties:** It provides a **cryptographic binding / data integrity** to the entire list. If even a single bit in the list changes, its leaf hash changes, which cascades up the tree, resulting in a completely different Root Hash. 
*   **Required Property of H:** The hash function $H$ MUST be **collision-resistant**. If it wasn't, an attacker could find a fake list of integers that produces the exact same Root Hash, breaking the integrity of the tree.

**3. Short proof of inclusion (Merkle Proof)**
*   **How to make it:** To prove that an element is in the tree, you provide the element itself and its "Authentication Path" — the list of sibling hashes required to compute the path from the element's leaf up to the Root. For $3$, the proof is the array of hashes: $[L_1, N_{3,4}, N_5]$.
*   **How to verify:** The verifier hashes the element to get $L_2$. Then they compute $H(L_1 || L_2) = N_{1,2}$, then $H(N_{1,2} || N_{3,4}) = N_{1,2,3,4}$, and finally $H(N_{1,2,3,4} || N_5)$. If the computed hash matches the known Root Hash, the proof is valid.
*   **Size:** The size of the proof is $\lceil \log_2(N) \rceil$ hashes, where $N$ is the number of elements. This is highly efficient (e.g., a tree with 1 million items only requires 20 hashes as proof).

**4. Append operation and Prefix proof**

*   **Append Operation ($L' = L ++ [\alpha]$):**
    To append $\alpha$ (e.g., to $X$), you add it as a new leaf $L_6 = H(\alpha)$. You do *not* need to recompute the entire tree. You only compute the hashes along the branch where the new leaf is added. For $X$, $N_5$ was previously alone; now it pairs with $L_6$ to become $H(L_5 || L_6)$. You then recompute the nodes strictly on the path up to the new Root.
    *   **Complexity:** The time complexity is $O(\log N)$, as you only compute hashes equivalent to the height of the tree.
*   **Prefix Proof (Consistency Proof):**

    When a database (like a Certificate Transparency log or a Blockchain) grows, you want to prove to a client that the new database $L'$ is just the old database $L$ with some new data $\alpha$ appended to the end. You must prove that **no previous entries were altered or deleted.**

    To prove that $L$ is a prefix of $L'$, you must prove that the old Root Hash of $L$ can be reconstructed from a subset of the nodes existing in the new tree $L'$.

    *   **The Core Concept:**

        Instead of sending the entire list of elements, the prover sends a small set of pre-calculated hashes from the tree. 
        The magic of the Prefix Proof is that the verifier will use this **exact same set of hashes** to perform two different mathematical equations:
        1. Combine them to re-create the **Old Root Hash**.
        2. Combine them (plus the new element $\alpha$) to create the **New Root Hash**.

        If both equations match the trusted Roots, it mathematically proves $L$ is a prefix of $L'$.


    *   **Step-by-Step Example**

        Let's use an old list of 3 elements: $L = [D_1, D_2, D_3]$.
        We append a new element $\alpha$: $L' = [D_1, D_2, D_3, \alpha]$.

        **1. How the Old Tree ($L$) looked:**
        *   $H_{12} = H(D_1 || D_2)$
        *   $H_3 = H(D_3)$
        *   **$Root_{old}$** $= H(H_{12} || H_3)$

        **2. How the New Tree ($L'$) looks:**
        *   $H_{12}$ remains exactly the same.
        *   $H_{\alpha} = H(\alpha)$
        *   Because we appended $\alpha$, $H_3$ now has a partner! We compute their parent: $H_{3\alpha} = H(H_3 || H_{\alpha})$
        *   **$Root_{new}$** $= H(H_{12} || H_{3\alpha})$

        **3. The Proof Generation (What the Prover sends):**
        The prover wants to prove $L'$ is an extension of $L$. The prover sends a small proof consisting of:
        1.  The newly appended data: **$\alpha$**
        2.  The "Frontier" hashes of the old tree: **$[H_{12}, H_3]$**

        **4. The Verification (What the Client does):**
        The client knows the old $Root_{old}$ from yesterday, and just downloaded the new $Root_{new}$ today. They receive the proof $[\alpha, H_{12}, H_3]$ and do the following checks:

        *   **Check 1: Does this represent the old tree?**
            The client hashes the frontier together: $H(H_{12} || H_3)$.
            *Does this equal $Root_{old}$?* If yes, the client is 100% sure that $H_{12}$ and $H_3$ are the legitimate building blocks of the old list.

        *   **Check 2: Was the new tree built securely on top of it?**
            The client takes the exact same trusted blocks, but adds $\alpha$:
            1.  Hash the new element: $H_{\alpha} = H(\alpha)$
            2.  Pair it with the old unpaired node: $H_{3\alpha} = H(H_3 || H_{\alpha})$
            3.  Combine it with the rest of the tree: $H(H_{12} || H_{3\alpha})$
            
            *Does this equal $Root_{new}$?* If yes, the proof is complete. The new tree was mathematically built by strictly appending $\alpha$ to the old tree.
    
   
    *   **Size & Verification:** The number of hashes required is strictly bound by the height of the tree. Therefore, the size of the proof is logarithmic: **$O(\log N)$** (where $N$ is the number of elements in the tree). The verifier runs two logarithmic hashing chains simultaneously—one culminating in the old root, and one culminating in the new root.