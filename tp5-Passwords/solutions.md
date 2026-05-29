# Exercise 1 - Timing attacks

### 1.1 - Timing attack vulnerability

**The Timing Leak :**

In this algorithm, the stored hashed password is compared with the hash of the provided password. Each characters are compared one by one. As soon as one character is incorrect, the verification immediately stops, however if a character is correct, the verification compares the next character of both hash. The time it takes to execute the loop iteration, exiting at i=1 takes slightly longer than exiting at i=0. This is only a leak of information about the password.  

Now because cryptographic hashes possess the avalanche effect (changing one letter of the plaintext completely randomizes the entire output hash), we cannot guess the plaintext password character by character !

**The Online Attack (Recovering the Hash h) :**

-	The attacker wants to find the first byte of the stored hash, h[0]. A byte has 2⁸ = 256 possible values (0x00 to 0xFF).
-	**Offline preparation:** The attacker generates random passwords on their own computer and hashes them until they find a set of 256 passwords that produce hashes starting with every possible byte from 0x00 to 0xFF.
-	**Online queries:** The attacker sends these 256 passwords to the server. 255 of them will fail at i=0 (fast reject). Exactly one will match the first byte h[0], causing the loop to advance to i=1 before failing (slower reject). The attacker measures the response times, identifies the slower response, and now knows h[0].
-	**Moving to the next byte:** To find h[1], the attacker again generates random passwords offline, searching for 256 passwords whose hashes start with the newly discovered h[0], followed by all 256 possible values for the second byte. They send these 256 queries to the server. The one that takes the longest reveals h[1].
-	**Math:** For each byte of the hash, the attacker makes maximum 256 queries to the server. If the hash has length |h|, the total number of queries sent to the server is at most 256 * |h|. 

**The Offline Dictionary Attack :**

The attackers take a massive list of common passwords (a dictionary like rockyou.txt), hash every single word on their own computers. They store the correspondence between the plaintext password and the hash of it. In our case, the attackers can sort the dictionary based on the hashes so that he can try each hashes byte by byte and having the corresponding plaintext password at the end.



### 1.2 - Preventing the attack
To prevent timing attacks, we must implement a Constant-Time String Comparison algorithm. Execution time and code branches (if/else) must never depend on secret data. The verifier must  must respond within the same duration regardless of how many characters match. 

**Warning : adding a random delay will not work as security mechanism!** If we add random delays, the attacker simply sends the same password 100 times, records the response times, and calculates the average. Because of the Law of Large Numbers, the random noise cancels itself out, and the tiny timing difference of the loop execution will still be visible in the averages. So it will just makes the attack a bit more fastidious without really preventing it.

Server side, we can also restrict the number of logging attempt. For example, allowing 5 wrong attempts before blocking the request for 5 minutes, then allowing 5 more attempts before blocking for 10 minutes, ... The point is to make the delay longer and longer so that trying 256 . |h| is not feasable in a reasonable amount of time.


# Exercise 2 - HOTP variant
- The user device has a secret symetric key $k$.
- The server send a challenge (random nouce) $x$, a 6-digit code.
- The device computes c = encryption of $x$ using $k$. (As seen in TP2, AE.Enc takes as parameter a nonce and the message to encrypte. Here we don't care about the message to send so we use 0)
- The device computes $c' = c mod 10^6$

1.	**How does the server verify authentication :** Because of the modulo operation, the server can not use the decryption function AE.Dec on the 6-digit response. The server knows x and k, so it re-encrypte the data and can compute the value of c’. If the client is legitimate, he can compute c’ too and send to to the server to confirm its identity.

2.	**"Principals" in this protocol:** The parties involved are the server, the user and the user’s device (hardware). We separates the user and the device because the user does not know the secret key k. The human's only role is to read and type numbers.

3. **Is this vulnerable to replay attack ?:**	Each time someone wants to authenticate, the server gives a random 6-digit code x. In Authenticated Encryption (AE), the nonce (number used once) must never repeat for the same key. In this protocol, the challenge x acts as the nonce. 

    If an attacker gives back a stolen c’ has the challenge’s answer, it will most likely not work because of the randomness of the given code. However, since the code x is only 6-digit, at some point the server might send the a code corresponding to the c’ reply the attacker has stolen, therefore successfully passing the challenge and authenticate as the user.

4.	**Is this vulnerable to pishing ?:** Phishing is tricking the user and make him send information to the attacker instead of the server. For example, the attacker can write an e-mail asking the user to log again via a provided URL. The URL redirects to an fake website acting has a Man-in-the-middle. 

    The MITM will ask the server to authenticate, the MITM will ask the client to solve the challenge, and finally the MITM will reply to the server with the resolved challenge, allowing him to authenticate instead of the user.

    Every protocol that doesn’t force the user to verify the identity of the one he is communicating with, and if there is no pre-established secured communication channel, are vulnerable to phishing. But implementing those measures will drastically reduce the usability.

5.	**How to improve security + remaining weakness?** To improve the security, we must increase the size of the challenge x (the nonce) enough to make collision’s probabilities very low. The server side we can also limits  the authentication attempts and proves it’s identity using signatures.

    Remaining Weaknesses:

    1.  **The Usability vs. Security Paradox:** If you improve security by making the challenge $x$ a cryptographically secure 256-bit number, **the human can no longer type it into the device**. If it's small enough to type, it's vulnerable to collisions; if it's large enough to be secure, it's unusable.
    2.  **Still Vulnerable to Phishing:** Changing the size of $x$ or limiting attempts does absolutely nothing to stop a real-time MITM phishing attack. The attacker will just relay the long challenge and the 6-digit response.


# Exercise 3 - Cracking passwords

## Password Security and Entropy
When users authenticate with passwords, the security relies entirely on the unpredictability of the chosen secret.

### Brute-Force
To crack a password without any prior knowledge, an attacker must guess every possible combination (Brute-Force). The difficulty of this is measured in **Entropy**:
*   **Search Space ($S$):** The total number of possible passwords. If a password is exactly $L$ characters long and uses a character set of size $C$ (e.g., 26 for lowercase letters), the search space is $S = C^L$.
*   **Average Guesses:** On average, an attacker will find the correct password after searching half the space: $\approx S / 2$.

### Entropy

In security, we measure the strength of a password in **bits of entropy**. 

1. **Shannon Entropy ($H$):** Measures the uncertainty of the password creator. For a uniform distribution over $N$ possibilities, the Shannon entropy is:
   $$H = \log_2(N) \text{ bits}$$
   This tells us how many random binary choices (yes/no questions) it would take to represent the password.

2. **Guessing Entropy ($G$):** This represents the **expected (average) number of guesses** an attacker must make to find the correct password using an optimal strategy (guessing from most likely to least likely). 
   * For a **uniform distribution** (where all passwords are equally likely), the optimal strategy is just guessing without replacement in any random order.
   * In this uniform case, the average number of guesses is $G = \frac{N+1}{2}$.

3. **Guessing Entropy in Bits:** This is simply the base-2 logarithm of the average number of guesses:
   $$\text{Guessing Entropy (in bits)} \approx \log_2\left(\frac{N}{2}\right) = \log_2(N) - 1 \text{ bits}$$

### Dictionary Attacks
In reality, users do not choose passwords uniformly at random. They use recognizable words, names, and patterns. 
*   **Online Dictionary Attack:** The attacker attempts to log into the live service using a list of common passwords (like the `rockyou.txt` breach dataset). 
*   **Offline Dictionary Attack:** The attacker steals the server's database of cryptographic hashes and rapidly tests candidate passwords on their own hardware.


## 3.1 - Compute Complexity
**Total Possibilities (Search Space) :**

Because the user chooses a password of exactly 20 characters uniformly at random from the 26 lowercase letters, the total number of possible passwords $N = 26^20≈1.99 × (10 )^{28}$
The 256-bit hash output has $2^{256} ≈ 1.15 × 10^{77}$ possibilities. Because the hash space is massively larger than the password space, we can assume there are zero collisions. Every password will map to a unique hash. Therefore, the attacker is strictly guessing passwords, not fighting hash collisions.

**Average Number of Guesses:**

Since the password was chosen uniformly and randomly, the attacker has no "smart" starting point. Their best strategy is a Brute-Force attack, trying every combination one by one.  In the luckiest case, they find it on the 1st guess. In the worst case, they find it on the N-th guess.

Because the distribution is uniform, the expected value (average number of guesses) is exactly halfway through the search space: Average Guesses = $(N + 1)/2≈ N/2= (26^{20})/2 ≈ 9.96 × 10^{27}$ guesses.
Details of the computation :

To find the average number of guesses, we use the **Expected Value** ($\mathbb{E}$). Let $G$ be a random variable representing the number of guesses it takes to find the correct password.

1. Let $N = 26^{20}$ be the total number of possible passwords.
2. Since the target password is chosen uniformly at random, the probability that the correct password is found on exactly the $i$-th guess is equal for all guesses:
   $$P(G = i) = \frac{1}{N} \quad \text{for } i \in \{1, 2, \dots, N\}$$

3. The expected value $\mathbb{E}[G]$ is the sum of each possible number of guesses multiplied by its probability:
   $$\mathbb{E}[G] = \sum_{i=1}^{N} i \cdot P(G = i) = \sum_{i=1}^{N} i \cdot \frac{1}{N}$$

4. Factor out the constant $\frac{1}{N}$:
   $$\mathbb{E}[G] = \frac{1}{N} \sum_{i=1}^{N} i$$

5. Recall the standard algebraic formula for the sum of the first $N$ integers ($\sum_{i=1}^{N} i = \frac{N(N+1)}{2}$):
   $$\mathbb{E}[G] = \frac{1}{N} \cdot \frac{N(N+1)}{2}$$

6. Simplify the expression by canceling out $N$:
   $$\mathbb{E}[G] = \frac{N+1}{2}$$

7. Given $N = 26^{20} \approx 1.9928 \times 10^{28}$:
   $$\mathbb{E}[G] = \frac{26^{20} + 1}{2} \approx 9.964 \times 10^{27} \text{ guesses}$$

**Guessing entropy :**

#### Shannon Entropy of the Password
The total entropy of the uniform password space:
$$H = \log_2(N) = \log_2(26^{20})$$

Using logarithm properties ($\log(a^b) = b \log(a)$):
$$H = 20 \cdot \log_2(26)$$
$$H \approx 20 \cdot 4.7004 \approx 94.01 \text{ bits}$$

#### Guessing Entropy in Bits
The base-2 logarithm of the expected number of guesses:
$$\text{Guessing Entropy (bits)} = \log_2(\mathbb{E}[G]) = \log_2\left(\frac{N+1}{2}\right) \approx \log_2\left(\frac{26^{20}}{2}\right)$$

Using logarithm properties ($\log(a/b) = \log(a) - \log(b)$):
$$\text{Guessing Entropy (bits)} \approx 20 \cdot \log_2(26) - \log_2(2) \approx 94.01 - 1 = 93.01 \text{ bits}$$

## 3.2 - Find the Password
What we are doing here is an offline dictionary attack. The idea is to iterate over a wordlist, hash each word, and compare the outputs. Because we got access to hash, we do not need to interact with the authentication server anymore. We can compute toy_hash() locally on our own machine.

Notice that toy_hash() does not use a Salt (a random value appended to the password before hashing). Because there is no salt, we can just hash the dictionary words directly. If a salt had been used, we would have had to prepend/append the specific user's salt to every word in rockyou.txt during the loop.


# Exercise 4 - Authentication with passwords

## 4.1
- An offline dictionary attack means the attacker has obtained a copy of the database and tests candidates locally.
- The cracking cluser gives computing power to help do the computional intensive tasks. 
- An online dictionary attack means the attacker submits candidate passwords to the login server. We suppose there is NO server-side protections.

| | Offline Dictionary | Offline dict. + cracking cluster| Online Dictionary |
|- |- |- |- |
| Scheme A | YES, simple lookup | YES, simple lookup  | Yes/No depending on the password. If dumb password, just try enough times |
| Scheme B | YES. If we know the hashing function, we can use the rockyou file then hash each entry and compare with H(pw). Or use rainbow tables. | YES. Computing the hash is even faster, then its a lookup | Yes/No depending on the password. Hashing will maybe slow down a bit the server answer. |
| Scheme C | YES. However, because the salt is unique per user, the attacker must recompute the dictionary hashes for each individual user, neutralizing precomputed rainbow tables. | YES | Yes/No depending on the password. As legitimate users do, we just submit the password (not the concatenation of salt+pwd). |
| Scheme D | Yes/No depending on the password. While slow (100ms), a standard 14M word dictionary still only takes ~16 days on a single CPU, which is feasible. | Yes/No depending on the password.  A memory-hard hash functions greatly reduce GPU/ASICS cluster efficacity.| Yes/No. Here the server computational ressources might slow down even more the number of attempt/sec. So it depends on password. You can DoS the server though.|
| Scheme E | NO, you don't have the pepper so you gotta have to brute force which is not feasible in resonalble time. | NO. If the pepper and the password are strong enough there is too many possibilities : $2^{128} \times pwd\_size$| Yes/No depending on the password. |

For online attacks, we suppose there is no protection server side. This means the attacker will submits as much login attemps as possible. Therefor, protection only resides in the user password (and is limited by the network and server capabilities to handle the requests). Server side protection against online attacks will be discussed below.

## 4.2

Supposing the attacker got a local copy of the database. In Scheme B, if two user choose the same password, the stored hash will be the same. Therefore the attacker will directly know that. It is more unlikely two have a hash collision than two users having the same password, but in both case having one password will allow to log into both account.

In the Scheme C, the introduction of the salt will create an completely new hash even though the passwords are the same. Meaning the attacker can not know that two user uses the same password. 


## 4.3

A rainbow table is a precomputed table for caching the outputs of a cryptographic hash function. This table creates a link in both ways, allowing the attacker to obtain the password that generated the hash. In scheme B, we have all the hashes of the passwords. By using the table the attacker can find all the passwords of all users.

In Scheme C, a salt was added to each password before hashing them. This salt completely destroy the links in the rainbow table. H(pw) in the rainbow table will be different than H(s||pw). A rainbow table is designed to be computed once and used against millions of hashes. Because the salt in Scheme C is unique to each user, the attacker would have to compute a completely new rainbow table for every single user's unique salt. 

So this only makes precomputed rainbow table useless. However since the database store the salt in plaintext, this does not prevent a brute force attack to crack a user password. But brute forcing the password for every user may takes a lot of time.

## 4.4

If a hash function is only computationally slow, it means it just does a lot of math. An attacker will use GPUs or build ASICs. A modern GPU has thousands of Arithmetic Logic Units (ALUs). Because purely computational hashes require almost zero memory, an attacker's GPU can load 10,000 passwords simultaneously and compute them all in parallel. They effectively bypass the "100ms delay" by doing massive batches, calculating billions of hashes per second.

But if the hash requires large memory per evaluation, each parallel instance needs its own memory. Memory is expensive, take physical space, and most importantly is bandwidth limited. By making Hslow memory-hard, the algorithm demands high (V)RAM capacity per thread. This starves the attacker's parallel hardware of memory, forcing their GPU to process only a few passwords at a time, making the offline cracking cost very high.


## 4.5

### Why Password Storage Schemes Don't Stop Online Attacks :
An online dictionary attack occurs when the attacker sends login attempts directly to the authentication server. Even if the hash function takes 100 ms, the attacker is not limited by local computation. The attacker simply sends requests to the server and lets the server perform the expensive hash. If the server processes 100 requests per second, an attacker could attempt 100 guesses per second across accounts. The attacker does not pay the computational cost. 

The success of the online dictionary attack reside only on the weakness of the users passwords. If they are in a standard dictionary (14M), the online attack can succeed in resonable time.

The speed of an online attack is limited by network latency, server's connection limits,... not by the hash function. If the server uses a very slow hash, it actually helps the attacker. The attacker can even launch a DoS attack by sending a thousand login requests per second to overload the server. 
Therefore slow hashing protects mainly against offline attacks but not much against online attacks.

### Countermeasures Against Online Attacks :
To defend against online brute-force attempts, we must limit authentication attempts rather than rely on password hashing :
-	Rate limiting and Progressive delays : limiting the number of login attempts in a given time period per account (5 login attempts per 5 minute per account, 5 login attempts per 10 minutes, ...).
-	Account lockout : After several failed attempts, the account is temporarily locked. Then must wait or proceeds to additional verification steps (email verification or 2FA). However, this introduces a DoS attacks where attackers intentionally lock users’ accounts.
-	Avoid CAPTCHAs because these days they are not working anymore to prevent bot traffic.
-	Multi-factor authentication (MFA) : Enforce the use of an additional factor besides the password like authenticator apps or hardware security keys (Avoid SMS code though since this is not a really secure method). MFA makes your system less usable and less conveniant but completely block the attack.
-	IP reputation and anomaly detection :  Restrict the number of username attempts from a single IP, block IP from unusual geographic locations.


### Defending Against Slow, Distributed Botnet Attacks :

If adversary uses millions of different IP addresses (a botnet) and submits guesses very slowly, it completely bypasses standard IP-based rate limiting and IP reputation blocks (since residential botnet IPs often belong to legitimate ISPs).

**Scenario A: The adversary targets a specific user:**

Millions of bots take turns guessing the password for one user (like admin@company.com). We can protect against using the mechanism described above. Because the target is a single entity, implementing an Account-Based Rate Limiting / Lockout will efficiently defends against this attack. However this introduce a DoS risk to voluntary lock out the legitimate user. The best practice will be to enforce MFA.

**Scenario B: The adversary targets any user (Password Spraying)**

Now the attacker’s goal is to compromise any account in the system. They know all usernames and test few passwords per account. Account-based rate limiting does not help because few login attemps will not triggers account lockout. But this can eventually be detected using platform-wide monitoring over a long period of time. Behavior analytics is also important. If your user usual login from an i-phone in Brussels, a login attempt from a Brazilian smart fridge is really suspicious. Notice than this attack is really effective only if users have weak passwords. Enforcing strong passwords is a good mitigation but 2FA will completely prenvent it.


## 4.6 

### The Realistic Failure Scenario of the Pepper :

Scheme E relies on a Pepper, which is a secret (cryptographic key or random string) typically stored on the application server (in a configuration file, an environment variable, hardcoded in the source code maybe...), rather than in the database where the hashes and salts are kept. If an attacker obtains a copy of the password database, he still doens’t know p. In scheme E, the attacker would have to compute the hash of every possible values of both the pepper and  the password. If p is big enough, offline brute force is not feasible.

If the attacker compromises more than just the database and gets his hands on the pepper,the security of Scheme E collapses completely. Scheme E use a fast hash function, meaning than brute forcing every password possibilities is feasiable without a cracking cluster.

### Comparison with the Guarantees of Scheme D :
In Scheme D, if the attacker gets of copy of the database, he must compute Hslow for every password he tries. The salt is also compromised so it doesn’t offer protection against brute force. It only prevent the attacker to know if two user share the same password. Scheme D provide a stronger security against a big system breach, but without using a memory-hard hash function, a cracking cluster could be able to find all the passwords

### Bonus Question - Improving Scheme E with an HSM :

A Hardware Security Module (HSM) is a dedicated, tamper-resistant physical device that securely store cryptographic keys and perform cryptographic operations. Crucially, keys generated inside an HSM can never be extracted from it, even by the server administrator. Instead of storing the pepper p in the web application's memory or configuration files, p is generated and permanently locked inside the HSM.

When a user tries to log in, the application server does not compute the hash itself. Instead, it acts as a client to the HSM. The server sends the salt and the candidate password to the HSM over a secure internal connection. The HSM internally computes the hash and returns only the resulting hash to the server. The server compares this result with the database.

If an attacker compromise your whole infrastructure, he still cannot steal the pepper because it physically cannot leave the HSM hardware. Without any information about the pepper (size), the attacker's only option is to do online attacks and forcing the server to compute the hashes for him. This forces the offline attack to become an online attack that can be prevented using the mechanism described previously.

