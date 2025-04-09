# Reason for the requirement of `message_content` intent.

Our bot requires access to the `message_content` intent to enable essential moderation, user interaction, and dynamic command handling features that are critical to the health and safety of Discord servers.

---

## 🔒 Moderation Features

We implement a custom automoderation system that detects and moderates inappropriate content. This includes:

- Blocked keywords or phrases  
- Malicious or unauthorized links  
- Profanity and slurs  
- Spam and repeated messages  
- Excessive emoji usage (emoji spam)  
- Message flooding  

These moderation tools rely heavily on analyzing `message_content` to identify and act on violations in real-time.

---

## 🤖 User Interaction

The bot listens for mentions (e.g., `@paul`) and provides an automated responses. This enhances user experience and accessibility, especially for new members. Processing `message_content` is necessary to identify and handle these mentions properly.

---

## 🚨 Spam & Flood Detection

To maintain a safe and spam-free environment, the bot analyzes both message content and frequency to:

- Detect repeated or fast messages  
- Prevent raids or spam attacks  
- Alert moderators automatically  

These protections require access to `message_content`.

---

## 🔐 Privacy Commitment

We are committed to respecting user privacy. The bot only processes message content when necessary for moderation or explicit user interaction. No data is stored or logged beyond what is required for the functionality described above.