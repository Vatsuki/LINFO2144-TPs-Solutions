Although there is a complete walkaround provided, this file purpose is to give a structured summary of all the concepts (background + new) that are covered.


### **1.1 Using `system()` & SETUID**

**Theory:**
*   **Command Injection:** When untrusted user input is passed directly to an operating system shell without sanitization or escaping, an attacker can append additional commands (using separators like `;`, `&&`, or `|`).
*   **The `system()` Function Vulnerability:** In C, `system(cmd)` effectively calls `/bin/sh -c cmd`. Because it invokes a shell to interpret the command, it is susceptible to shell metacharacter injection. 
* **Real UID (rUID):** Who you actually logged in as.
* **Effective UID (eUID):** What permissions the OS is currently granting the process. When an SUID binary owned by root is executed by bob, bob is the Real UID, but root becomes the Effective UID for the duration of that process. 
*   **Processes:** An instance of a program. It is associated an ID, the ID of the user who called id (real UID), and the effective UID TODO continue
*   **SETUID (Set-User-ID) Bit:** A special Linux file permission (the `s` flag). When an executable with this flag is run, the process runs with the **Effective User ID (EUID)** of the file's owner (in this case, root) rather than the user who executed it. This is a primary vector for **Privilege Escalation**.

**test.c**
```c
int main(int argc, char *argv[])
  {char *cat ="/bin/cat";
  char *command = malloc(strlen(cat) + strlen(argv[1]) +2);
  sprintf(command, "%s %s", cat, argv[1]);
  system(command);
  return 0;}
```
The program concatenates user input directly into a command string and runs it using the `system()` function.

**Exploit : ** ./test "test.c;/bin/sh" -> forces the program to execute `cat test.c` followed by `/bin/sh`, spawning a shell. 

When the binary is given the **SETUID** flag and owned by root, the spawned shell but doesn't inherits root privileges. TODO: WHY ?



---

### **1.2 Spam & Delay**


**spam.c :**
```c
int main(int argc, char *argv[]) {
  if (argc < 3) { printf("Insufficient arguments\n");return 1; }
  char *echo ="/bin/echo";
  char *command = malloc(strlen(echo) + strlen(argv[2]) +2);
  sprintf(command, "%s %s", echo, argv[2]);
  unsigned char i = 0;
  int limit = atoi(argv[1]);
  while (i < limit) {
    system(command);
    i++;
  }
  free(command);
  return 0;
}

```

**delay.c :**
```c
int main(int argc, char *argv[]) {
  if (argc != 2) { printf("Usage: \"%s n\" to delay for n seconds\n",argv[0]); return 1;}
  char *sleep ="/bin/sleep";
  char *command = malloc(strlen(sleep) + strlen(argv[1]) +2);
  sprintf(command, "%s %s", sleep, argv[1]);
  system(command);
  return 0;
}
```
`spam.c` and `delay.c` use `system()` combined with `sprintf()` to execute `echo` and `sleep`. 

**Exploit:** Same as before, `./spam 2 "Oops;/bin/sh"` will print Oops then spawn a shell. When you exit, it will do it one more time.

Note that `./spam 2 Oops;/bin/sh` will print twice then open a shell -> TODO why ?(missing quotes ?)

The fix provided is to replaces the `system()` calls entirely with native C functions (`printf` and `sleep()`). *Never use `system()` if a native library function exists*.

---

### **1.3 execve Exploit (File Descriptor Leakage)**


**Concepts & Theory:**
* **getuid() :** returns the real user ID of the calling process.
* **setuid() :** sets the effective user ID of the calling process.
* **File Descriptor:** A FD is a int representing a file for the current process.
*   **File Descriptor Leakage:** When a parent process spawns a child process (via `fork()` and `execve()`), the child inherits all open file descriptors from the parent unless explicitly configured not to (using the `O_CLOEXEC` flag). 
*   **Stream Redirection:** In Linux, file descriptors map to data streams (0 is STDIN, 1 is STDOUT, 2 is STDERR, 3+ are custom). `>&3` is shell syntax to route output directly into File Descriptor 3.


```c
int main(int argc, char *argv[]) {
  int fd;
  char *v[2];
  if (argc > 2) { printf("Insufficient arguments, usage %s <filename>\n", argv[0]); return 1; } 
  fd = open(argv[1],O_RDWR | O_APPEND);
  if (fd==-1){
    printf("cannot open file %s\n", argv[1]);
    exit(0);
  }
  printf("fd is %d\n", fd);
  setuid(getuid());
  v[0] = "/bin/sh"; v[1] = 0;
  execve(v[0],v,0);
  return 0;
}
```
This program open a file, display the fd, drop priviledge, then open a shell.

**Exploit :** If the program has SUID and owned by root, it can opens a sensitive file (like `/etc/sudoers`) and assigns it a file descriptor (`fd = 3`). Although the user inside the spwaned shell is not root and cannot edit the restricted file directly using standard commands, the shell *inherited* the open file descriptor. The attacker bypasses permissions by writing directly to the file descriptor (`echo "#test" >&3`).

---

### **1.4 Integer Overflows**

**Theory:**
* **Unsinged overflow:** It's when you don't enough bits to store the decimal number you want. Example in 4 bits : 1111 + 0001 = 0000 -> 15 + 1 = 0. With buffer overflow we can read/write outside the bounds of a variable, creating Seg Faults or lead to exploits.
*   **Signess Overflow:** A `short` is 16 bits, the max *positive* value 0111 1111 1111 1111 -> 32 767. If an arithmetic operation exceeds this limit, the value "wraps around" due to Two's Complement binary representation, suddenly becoming a massive negative number (1000 0000 0000 0000 -> -32768).
*   **Signed number Casting :** Passing a negative number (like `-1`) to a function expecting an unsigned size (like `malloc` for memory allocation) can result in the negative number being interpreted as an enormous unsigned integer.
* **Truncation:** If we compare two numbers one of 16 bits and the other of 8 bits, only the 8 first bits (from the left, LSB) will be kept. If check size on the first 8 bits, but later use the original 16 bits this will cause overflow.

---

### **1.5 Race Conditions (TOCTOU)**

**Theory:**
*   **TOCTOU (Time of Check to Time of Use):** A specific type of race condition. It occurs when a system checks a condition (or establishes a state) and then uses the result, but the state changes between the check and the use.
*   **Race Conditions & Context Switching:** Multitasking OS architectures rapidly switch CPU execution between processes. 

```c
int main() { 
  struct stat st; FILE* fd; 
  
  if(!stat("password.txt", &st)) { 
     printf("file already exists\n"); 
     return 0;
   } 
  fd = fopen("password.txt", "a"); // Create a file with the default umask so anyone can read
  fputs("monsupermotdepasse", fd); // write password
  chmod("password.txt", S_IREAD | S_IEXEC | S_IWRITE); // secure file access 
  fflush(fd);
  fclose(fd); 
  return 0;
}
```

**Exploit :** The `race.c` program writes a password to a file, and *then* changes the permissions (`chmod`) to make it readable only by root. If execution pauses on `race.c` immediately after writing the file, the attacker's script gets a slice of CPU time to read it before `race.c` resumes to lock it.

The solution here is to first restrict the access to the password and then writing into it.

---

### **1.6 Thread Race Conditions**

A C program shares a variable between threads. When compiled with heavy compiler optimizations (like `-O1`, `-O2`, `-O3`), the program gets stuck in an infinite loop. The compiler assumes the loop variable isn't being modified by other threads and caches it in a register, causing the program to ignore the update from the separate thread.

**Theory:**
*   **Thread Concurrency and Shared Memory:** Threads run in the same memory space. If one thread checks a variable while another modifies it, synchronization (like Mutexes/Locks) is required.
*   **Compiler Optimization Pitfalls:** Compilers try to make code run faster by storing frequently used variables in CPU registers rather than reading from RAM every loop iteration. 
*   **The `volatile` Keyword:** In C, declaring a shared variable as `volatile` tells the compiler: "This variable might change outside the current execution flow (e.g., by another thread), so *do not cache it* and always read it directly from memory."

---

### **1.7 A Bad Cron Task**


**Theory:**
*   **Cron Jobs:** Linux daemon (`crond`) used to schedule recurring background tasks.
*   **Insecure File Permissions:** A script running as root must only be writable by root. If a lower-privileged user has write access, they essentially have root execution rights.
*   **Persistence & Privilege Escalation:** Attackers often use Cron both to elevate their privileges and to ensure their backdoor survives system reboots.

This exercise relies on system misconfiguration. A recurring background task (`cron`) is scheduled to run as `root`. However, the script it executes (/usr/bin/backup.py)has weak file permissions, allowing a normal user to edit it. Anyone can modifies the script and launch a shell (`zsh`). The shell will still belong to root. So to make it exploitable by a user, juste set the setuid flag. The next time the cron job triggers, root runs the script, creating a root backdoor for the user.

---

### **1.8 Finding a Target**

We use the command to scan the whole filesystem for binaries owned by root that have the SETUID bit enabled. 

```bash
find / -user root -perm /u+s -exec ls -l {} + 2>/dev/null
```

Note that you should find several of these programs on a normal system. The next step would be to see which are vulnerable to some kind of vulnerability. This could be done in different ways, for example:
1. Reverse engineering the binary via disassembly
2. run the program through a debugger to observe the behaviour and find a weak point
3. analyse the source code (if available)
4. Fuzzing to try and find a flaw